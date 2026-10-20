"""Service de abertura e classificação de chamados (UC02, RF02, RF05, RN04).

Não conhece HTTP: recebe os repositórios por injeção e levanta `ErroChamado` com
código estável para o controller traduzir ao formato único de erro (seção 7.1).

RN04 (TU01, TU02): um chamado só nasce ligado a uma **categoria ativa** e a um
**solicitante ativo**. O solicitante vem sempre do token (nunca do corpo). O
estado inicial é NOVO e o protocolo é gerado pelo banco (coluna gerada).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.enums import CanalOrigem, PerfilUsuario, SeveridadeChamado, StatusChamado
from app.entities.usuario import Usuario
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.chamado_historico_repository import HistoricoRepository
from app.repositories.chamado_repository import ChamadoRepository, LinhaChamado
from app.repositories.sla_repository import SlaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.evento_service import EventoService


class ErroChamado(Exception):
    """Erro de domínio da abertura/consulta de chamado, com código estável."""

    def __init__(self, codigo: str, mensagem: str, campo: str | None = None) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.campo = campo


# Grupos de status das abas e indicadores (seção 6.1).
_GRUPO_POR_STATUS: dict[StatusChamado, str] = {
    StatusChamado.NOVO: "abertos",
    StatusChamado.PENDENTE: "abertos",
    StatusChamado.ATRIBUIDO: "em_andamento",
    StatusChamado.CONCLUIDO: "resolvidos",
    StatusChamado.FECHADO: "encerrados",
}


def status_grupo(status: StatusChamado) -> str:
    """Rótulo de grupo (abertos/em_andamento/resolvidos/encerrados) do status."""
    return _GRUPO_POR_STATUS[status]


@dataclass(frozen=True)
class ChamadoAberto:
    """Resultado da abertura: o chamado e as entidades para montar a resposta."""

    chamado: Chamado
    categoria: Categoria
    solicitante: Usuario
    qtd_mensagens: int = 0


@dataclass(frozen=True)
class PaginaChamados:
    items: list[LinhaChamado]
    total: int
    page: int
    page_size: int
    contadores: dict[str, int]


def escopo_solicitante(usuario: Usuario) -> int | None:
    """Escopo por perfil (RN06, seção 6.4): CLIENTE só os seus (id); ANALISTA e
    ADMIN veem todos (None)."""
    if usuario.tipo_perfil == PerfilUsuario.CLIENTE:
        return usuario.id_usuario
    return None


class ChamadoService:
    def __init__(
        self,
        *,
        chamados: ChamadoRepository,
        categorias: CategoriaRepository,
        usuarios: UsuarioRepository,
        eventos: EventoService | None = None,
        historico: HistoricoRepository | None = None,
        sla: SlaRepository | None = None,
    ) -> None:
        self._chamados = chamados
        self._categorias = categorias
        self._usuarios = usuarios
        self._eventos = eventos
        self._historico = historico
        self._sla = sla

    def listar_categorias(self) -> list[Categoria]:
        """Categorias ativas, ordenadas (RF05)."""
        return self._categorias.listar_ativas()

    def abrir(
        self,
        *,
        id_solicitante: int,
        id_categoria: int,
        titulo: str,
        descricao: str,
        severidade: SeveridadeChamado = SeveridadeChamado.BAIXA,
        canal_origem: CanalOrigem = CanalOrigem.PORTAL,
    ) -> ChamadoAberto:
        """Abre um chamado para o solicitante do token (RN04). Estado inicial NOVO."""
        # RN04 / TU02: solicitante precisa existir e estar ativo.
        solicitante = self._usuarios.buscar_por_id(id_solicitante)
        if solicitante is None or not solicitante.ativo:
            raise ErroChamado(
                "SOLICITANTE_INATIVO", "Solicitante inválido ou inativo.", campo="id_solicitante"
            )

        # RN04 / TU01: categoria precisa existir e estar ativa.
        categoria = self._categorias.buscar_ativa_por_id(id_categoria)
        if categoria is None:
            raise ErroChamado(
                "CATEGORIA_INVALIDA", "Categoria inválida ou inativa.", campo="id_categoria"
            )

        chamado = self._chamados.criar(
            id_usuario_abertura=solicitante.id_usuario,
            id_categoria=categoria.id_categoria,
            titulo=titulo,
            descricao=descricao,
            severidade=severidade,
            canal_origem=canal_origem,
        )
        # SLA (F7.2): prazo-alvo = data_criacao + prazo_horas da severidade (decisão B20).
        if self._sla is not None:
            horas = self._sla.prazo_horas(severidade)
            if horas is not None and chamado.data_criacao is not None:
                chamado.prazo_sla = chamado.data_criacao + datetime.timedelta(hours=horas)
                self._chamados.flush()
        # Histórico: evento de criação (NOVO), coerente com o backfill da migration 0004.
        if self._historico is not None:
            self._historico.registrar(
                id_chamado=chamado.id_chamado,
                status_anterior=None,
                status_novo=StatusChamado.NOVO,
                id_autor=solicitante.id_usuario,
                observacao="Chamado criado",
            )
        # Evento de domínio (canal Portal): notifica solicitante e, se urgente, técnicos.
        if self._eventos is not None:
            self._eventos.chamado_criado(chamado=chamado, solicitante=solicitante)
        return ChamadoAberto(chamado=chamado, categoria=categoria, solicitante=solicitante)

    # ----- Consulta (F2.2) -----
    def listar(
        self,
        *,
        usuario: Usuario,
        q: str | None = None,
        grupo: str | None = None,
        id_categoria: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginaChamados:
        """Lista paginada no escopo do perfil (RN06), com busca, filtros e contadores.
        Os contadores respeitam `q` e categoria, mas ignoram o `grupo` (seção 6.5)."""
        escopo = escopo_solicitante(usuario)
        itens, total = self._chamados.listar(
            id_solicitante=escopo,
            q=q,
            grupo=grupo,
            id_categoria=id_categoria,
            page=page,
            page_size=page_size,
        )
        contadores = self._chamados.contadores(
            id_solicitante=escopo, q=q, id_categoria=id_categoria
        )
        return PaginaChamados(
            items=itens, total=total, page=page, page_size=page_size, contadores=contadores
        )

    def resumo(self, *, usuario: Usuario) -> dict[str, int]:
        """Indicadores do Dashboard no escopo do perfil (RF04)."""
        return self._chamados.resumo(id_solicitante=escopo_solicitante(usuario))

    def obter(self, *, usuario: Usuario, id_chamado: int) -> LinhaChamado:
        """Detalhe por id no escopo do perfil. Fora do escopo ou inexistente →
        `NAO_ENCONTRADO` (404), para não revelar chamados de outros (RN06, 6.4)."""
        linha = self._chamados.obter(id_chamado, id_solicitante=escopo_solicitante(usuario))
        if linha is None:
            raise ErroChamado("NAO_ENCONTRADO", "Chamado não encontrado.")
        return linha
