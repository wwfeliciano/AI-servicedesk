"""Controllers de chamados (F2.1 abertura; F2.2 lista, resumo e detalhe).

- POST /api/chamados          → abre para o próprio usuário (UC02, RN04)
- GET  /api/chamados          → lista com busca, filtros, contadores e paginação
- GET  /api/chamados/resumo   → indicadores do Dashboard (rota fixa antes da param.)
- GET  /api/chamados/{id}     → detalhe no escopo do perfil (RN06)

Escopo por perfil (RN06, seção 6.4) fica no service: CLIENTE só os seus; fora do
escopo ou inexistente → 404. `ErroChamado` vira o formato único de erro (7.1).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.controllers.dependencias import (
    ChamadoServiceDep,
    CicloVidaServiceDep,
    UsuarioAtualDep,
)
from app.controllers.schemas_chamados import (
    AtribuicaoEntrada,
    CategoriaResumo,
    ChamadoCriar,
    ChamadoLista,
    ChamadoSaida,
    ContadoresChamados,
    FollowUpCriar,
    FollowUpSaida,
    HistoricoSaida,
    RespostaSolucao,
    ResumoSaida,
    SolucaoCriar,
    SolucaoSaida,
    TriagemEntrada,
    UsuarioResumo,
)
from app.core.errors import ErroAPI
from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.solucao import Solucao
from app.entities.usuario import Usuario
from app.repositories.chamado_repository import LinhaChamado
from app.services.chamado_service import ChamadoAberto, ErroChamado, status_grupo
from app.services.ciclo_vida_service import ErroCicloVida

router = APIRouter(prefix="/api/chamados", tags=["chamados"])

_STATUS_POR_CODIGO = {
    "CATEGORIA_INVALIDA": status.HTTP_409_CONFLICT,
    "SOLICITANTE_INATIVO": status.HTTP_409_CONFLICT,
    "VALIDACAO": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "NAO_ENCONTRADO": status.HTTP_404_NOT_FOUND,
    "SEM_PERMISSAO": status.HTTP_403_FORBIDDEN,
    "TRANSICAO_INVALIDA": status.HTTP_409_CONFLICT,
    "RN03_TECNICO_INVALIDO": status.HTTP_409_CONFLICT,
}

_GRUPOS_VALIDOS = {"abertos", "em_andamento", "resolvidos", "encerrados"}


def _erro_http(exc: ErroChamado) -> ErroAPI:
    status_code = _STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_409_CONFLICT)
    campos = {exc.campo: exc.mensagem} if exc.campo else None
    return ErroAPI(status_code=status_code, codigo=exc.codigo, mensagem=exc.mensagem, campos=campos)


def _saida(
    *,
    chamado: Chamado,
    categoria: Categoria,
    solicitante: Usuario,
    tecnico: Usuario | None,
    qtd_mensagens: int,
) -> ChamadoSaida:
    return ChamadoSaida(
        id_chamado=chamado.id_chamado,
        protocolo=chamado.protocolo,
        titulo=chamado.titulo,
        descricao=chamado.descricao,
        categoria=CategoriaResumo(
            id_categoria=categoria.id_categoria,
            nome_categoria=categoria.nome_categoria,
            icone=categoria.icone,
        ),
        severidade=chamado.severidade,
        status_chamado=chamado.status_chamado,
        status_grupo=status_grupo(chamado.status_chamado),
        solicitante=UsuarioResumo(id_usuario=solicitante.id_usuario, nome=solicitante.nome),
        tecnico_responsavel=(
            UsuarioResumo(id_usuario=tecnico.id_usuario, nome=tecnico.nome)
            if tecnico is not None
            else None
        ),
        qtd_mensagens=qtd_mensagens,
        data_criacao=chamado.data_criacao,
        data_atualizacao=chamado.data_atualizacao,
    )


def _de_aberto(resultado: ChamadoAberto) -> ChamadoSaida:
    return _saida(
        chamado=resultado.chamado,
        categoria=resultado.categoria,
        solicitante=resultado.solicitante,
        tecnico=None,
        qtd_mensagens=resultado.qtd_mensagens,
    )


def _de_linha(linha: LinhaChamado) -> ChamadoSaida:
    return _saida(
        chamado=linha.chamado,
        categoria=linha.categoria,
        solicitante=linha.solicitante,
        tecnico=linha.tecnico,
        qtd_mensagens=linha.qtd_mensagens,
    )


@router.post(
    "",
    response_model=ChamadoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Abre um chamado (autenticado, para o próprio usuário)",
)
def abrir(
    dados: ChamadoCriar, servico: ChamadoServiceDep, usuario: UsuarioAtualDep
) -> ChamadoSaida:
    try:
        resultado = servico.abrir(
            id_solicitante=usuario.id_usuario,
            id_categoria=dados.id_categoria,
            titulo=dados.titulo,
            descricao=dados.descricao,
            severidade=dados.severidade,
        )
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    return _de_aberto(resultado)


@router.get("", response_model=ChamadoLista, summary="Lista chamados (escopo do perfil)")
def listar(
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
    q: Annotated[str | None, Query(max_length=150)] = None,
    grupo: Annotated[str | None, Query()] = None,
    id_categoria: Annotated[int | None, Query(ge=1)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> ChamadoLista:
    grupo_valido = grupo if grupo in _GRUPOS_VALIDOS else None
    pagina = servico.listar(
        usuario=usuario,
        q=q,
        grupo=grupo_valido,
        id_categoria=id_categoria,
        page=page,
        page_size=page_size,
    )
    return ChamadoLista(
        items=[_de_linha(linha) for linha in pagina.items],
        total=pagina.total,
        page=pagina.page,
        page_size=pagina.page_size,
        contadores=ContadoresChamados(**pagina.contadores),
    )


@router.get("/resumo", response_model=ResumoSaida, summary="Indicadores do Dashboard")
def resumo(servico: ChamadoServiceDep, usuario: UsuarioAtualDep) -> ResumoSaida:
    return ResumoSaida(**servico.resumo(usuario=usuario))


@router.get("/{id_chamado}", response_model=ChamadoSaida, summary="Detalhe (escopo do perfil)")
def obter(id_chamado: int, servico: ChamadoServiceDep, usuario: UsuarioAtualDep) -> ChamadoSaida:
    try:
        linha = servico.obter(usuario=usuario, id_chamado=id_chamado)
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    return _de_linha(linha)


def _erro_ciclo(exc: ErroCicloVida) -> ErroAPI:
    status_code = _STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_409_CONFLICT)
    return ErroAPI(status_code=status_code, codigo=exc.codigo, mensagem=exc.mensagem)


@router.post(
    "/{id_chamado}/triagem",
    response_model=ChamadoSaida,
    summary="Triagem: NOVO → PENDENTE (ANALISTA/ADMIN)",
)
def triar(
    id_chamado: int,
    dados: TriagemEntrada,
    ciclo: CicloVidaServiceDep,
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
) -> ChamadoSaida:
    try:
        ciclo.triar(
            ator=usuario,
            id_chamado=id_chamado,
            id_categoria=dados.id_categoria,
            severidade=dados.severidade,
            observacao=dados.observacao,
        )
        linha = servico.obter(usuario=usuario, id_chamado=id_chamado)
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    return _de_linha(linha)


@router.post(
    "/{id_chamado}/atribuicao",
    response_model=ChamadoSaida,
    summary="Atribui um técnico → ATRIBUIDO (RN03)",
)
def atribuir(
    id_chamado: int,
    dados: AtribuicaoEntrada,
    ciclo: CicloVidaServiceDep,
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
) -> ChamadoSaida:
    try:
        ciclo.atribuir(
            ator=usuario,
            id_chamado=id_chamado,
            id_tecnico=dados.id_tecnico,
            observacao=dados.observacao,
        )
        linha = servico.obter(usuario=usuario, id_chamado=id_chamado)
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    return _de_linha(linha)


@router.get(
    "/{id_chamado}/historico",
    response_model=list[HistoricoSaida],
    summary="Linha do tempo de status (escopo do perfil)",
)
def historico(
    id_chamado: int,
    ciclo: CicloVidaServiceDep,
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
) -> list[HistoricoSaida]:
    # Garante o escopo do perfil (CLIENTE só os seus) antes de expor o histórico.
    try:
        servico.obter(usuario=usuario, id_chamado=id_chamado)
        eventos = ciclo.historico(id_chamado=id_chamado)
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    return [
        HistoricoSaida(
            id_historico=e.id_historico,
            status_anterior=e.status_anterior,
            status_novo=e.status_novo,
            observacao=e.observacao,
            id_autor=e.id_autor,
            data_evento=e.data_evento,
        )
        for e in eventos
    ]


def _solucao_saida(s: Solucao) -> SolucaoSaida:
    return SolucaoSaida(
        id_solucao=s.id_solucao,
        descricao_solucao=s.descricao_solucao,
        status_aprovacao=s.status_aprovacao.value,
        id_analista=s.id_analista,
        data_solucao=s.data_solucao,
    )


@router.post(
    "/{id_chamado}/solucoes",
    response_model=ChamadoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra a solução e conclui (ATRIBUIDO→CONCLUIDO, RN01)",
)
def concluir(
    id_chamado: int,
    dados: SolucaoCriar,
    ciclo: CicloVidaServiceDep,
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
) -> ChamadoSaida:
    try:
        ciclo.concluir(
            ator=usuario, id_chamado=id_chamado, descricao_solucao=dados.descricao_solucao
        )
        linha = servico.obter(usuario=usuario, id_chamado=id_chamado)
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    return _de_linha(linha)


@router.get(
    "/{id_chamado}/solucoes",
    response_model=list[SolucaoSaida],
    summary="Soluções do chamado (escopo do perfil)",
)
def listar_solucoes(
    id_chamado: int,
    ciclo: CicloVidaServiceDep,
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
) -> list[SolucaoSaida]:
    try:
        servico.obter(usuario=usuario, id_chamado=id_chamado)  # escopo
        solucoes = ciclo.solucoes(id_chamado=id_chamado)
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    return [_solucao_saida(s) for s in solucoes]


@router.get(
    "/{id_chamado}/followups",
    response_model=list[FollowUpSaida],
    summary="Follow-ups do chamado (participantes)",
)
def listar_followups(
    id_chamado: int, ciclo: CicloVidaServiceDep, usuario: UsuarioAtualDep
) -> list[FollowUpSaida]:
    try:
        itens = ciclo.listar_followups(ator=usuario, id_chamado=id_chamado)
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    return [
        FollowUpSaida(
            id_followup=f.id_followup,
            id_autor=f.id_autor,
            mensagem=f.mensagem,
            data_envio=f.data_envio,
        )
        for f in itens
    ]


@router.post(
    "/{id_chamado}/followups",
    response_model=FollowUpSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um follow-up (participantes; FECHADO bloqueia)",
)
def adicionar_followup(
    id_chamado: int,
    dados: FollowUpCriar,
    ciclo: CicloVidaServiceDep,
    usuario: UsuarioAtualDep,
) -> FollowUpSaida:
    try:
        f = ciclo.adicionar_followup(ator=usuario, id_chamado=id_chamado, mensagem=dados.mensagem)
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    return FollowUpSaida(
        id_followup=f.id_followup, id_autor=f.id_autor, mensagem=f.mensagem, data_envio=f.data_envio
    )


# Router à parte para a resposta do solicitante (prefixo /api/solucoes).
router_solucoes = APIRouter(prefix="/api/solucoes", tags=["chamados"])


@router_solucoes.post(
    "/{id_solucao}/resposta",
    response_model=ChamadoSaida,
    summary="Solicitante aprova/reprova a solução (RN02)",
)
def responder_solucao(
    id_solucao: int,
    dados: RespostaSolucao,
    ciclo: CicloVidaServiceDep,
    servico: ChamadoServiceDep,
    usuario: UsuarioAtualDep,
) -> ChamadoSaida:
    try:
        resultado = ciclo.responder_por_solucao(
            ator=usuario, id_solucao=id_solucao, aprovada=dados.aprovada, motivo=dados.motivo
        )
        linha = servico.obter(usuario=usuario, id_chamado=resultado.chamado.id_chamado)
    except ErroCicloVida as exc:
        raise _erro_ciclo(exc) from exc
    except ErroChamado as exc:
        raise _erro_http(exc) from exc
    return _de_linha(linha)
