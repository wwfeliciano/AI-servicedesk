"""Service do ciclo de vida do chamado (F4; RF03, RN03; seção 6.3).

Transições desta etapa (F4.1):
- **Triagem** NOVO → PENDENTE: por ANALISTA ou ADMIN; pode ajustar categoria e
  severidade. Evento `STATUS_ALTERADO`.
- **Atribuição** NOVO/PENDENTE/ATRIBUIDO → ATRIBUIDO: ANALISTA (a si mesmo) ou
  ADMIN (a qualquer técnico). RN03: técnico precisa ser ANALISTA/ADMIN **ativo**.
  Evento `CHAMADO_ATRIBUIDO`.

Qualquer transição fora da tabela 6.3 → `TRANSICAO_INVALIDA` (409). Cada transição
grava `historico_chamado` e atualiza `data_atualizacao` na mesma transação (o
commit é da sessão da requisição). Não conhece HTTP.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from app.entities.chamado import Chamado
from app.entities.enums import PerfilUsuario, SeveridadeChamado, StatusAprovacao, StatusChamado
from app.entities.follow_up import FollowUp
from app.entities.historico_chamado import HistoricoChamado
from app.entities.solucao import Solucao
from app.entities.usuario import Usuario
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.chamado_historico_repository import HistoricoRepository
from app.repositories.chamado_repository import ChamadoRepository
from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.solucao_repository import SolucaoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.evento_service import EventoService

# Rótulos de status para as mensagens de notificação (seção 6.1).
ROTULO_STATUS: dict[StatusChamado, str] = {
    StatusChamado.NOVO: "Aberto",
    StatusChamado.PENDENTE: "Aberto",
    StatusChamado.ATRIBUIDO: "Em andamento",
    StatusChamado.CONCLUIDO: "Resolvido",
    StatusChamado.FECHADO: "Encerrado",
}


class ErroCicloVida(Exception):
    """Erro de domínio do ciclo de vida, com código estável para o controller."""

    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass(frozen=True)
class ResultadoTransicao:
    chamado: Chamado
    evento: HistoricoChamado


def _agora() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


class CicloVidaService:
    def __init__(
        self,
        *,
        chamados: ChamadoRepository,
        categorias: CategoriaRepository,
        usuarios: UsuarioRepository,
        historico: HistoricoRepository,
        solucoes: SolucaoRepository | None = None,
        followups: FollowUpRepository | None = None,
        eventos: EventoService | None = None,
    ) -> None:
        self._chamados = chamados
        self._categorias = categorias
        self._usuarios = usuarios
        self._historico = historico
        self._solucoes = solucoes
        self._followups = followups
        self._eventos = eventos

    def _carregar(self, id_chamado: int) -> Chamado:
        chamado = self._chamados.buscar_por_id(id_chamado)
        if chamado is None:
            raise ErroCicloVida("NAO_ENCONTRADO", "Chamado não encontrado.")
        return chamado

    @staticmethod
    def _exigir_tecnico(ator: Usuario) -> None:
        if ator.tipo_perfil not in (PerfilUsuario.ANALISTA, PerfilUsuario.ADMIN):
            raise ErroCicloVida(
                "SEM_PERMISSAO", "Ação permitida apenas a analistas e administradores."
            )

    # ----- Triagem: NOVO → PENDENTE -----
    def triar(
        self,
        *,
        ator: Usuario,
        id_chamado: int,
        id_categoria: int | None = None,
        severidade: SeveridadeChamado | None = None,
        observacao: str | None = None,
    ) -> ResultadoTransicao:
        self._exigir_tecnico(ator)
        chamado = self._carregar(id_chamado)
        if chamado.status_chamado != StatusChamado.NOVO:
            raise ErroCicloVida(
                "TRANSICAO_INVALIDA", "A triagem só é possível em chamados com status NOVO."
            )

        # Ajustes opcionais na triagem (categoria ativa e/ou severidade).
        if id_categoria is not None and id_categoria != chamado.id_categoria:
            categoria = self._categorias.buscar_ativa_por_id(id_categoria)
            if categoria is None:
                raise ErroCicloVida("CATEGORIA_INVALIDA", "Categoria inválida ou inativa.")
            chamado.id_categoria = categoria.id_categoria
        if severidade is not None:
            chamado.severidade = severidade

        anterior = chamado.status_chamado
        chamado.status_chamado = StatusChamado.PENDENTE
        chamado.data_atualizacao = _agora()
        self._chamados.flush()
        evento = self._historico.registrar(
            id_chamado=chamado.id_chamado,
            status_anterior=anterior,
            status_novo=StatusChamado.PENDENTE,
            id_autor=ator.id_usuario,
            observacao=observacao or "Triagem",
        )
        if self._eventos is not None:
            self._eventos.status_alterado(
                chamado=chamado,
                id_solicitante=chamado.id_usuario_abertura,
                rotulo_novo=ROTULO_STATUS[StatusChamado.PENDENTE],
            )
        return ResultadoTransicao(chamado=chamado, evento=evento)

    # ----- Atribuição: NOVO/PENDENTE/ATRIBUIDO → ATRIBUIDO (RN03) -----
    def atribuir(
        self,
        *,
        ator: Usuario,
        id_chamado: int,
        id_tecnico: int,
        observacao: str | None = None,
    ) -> ResultadoTransicao:
        self._exigir_tecnico(ator)
        chamado = self._carregar(id_chamado)

        if chamado.status_chamado not in (
            StatusChamado.NOVO,
            StatusChamado.PENDENTE,
            StatusChamado.ATRIBUIDO,
        ):
            raise ErroCicloVida(
                "TRANSICAO_INVALIDA", "O chamado não pode ser atribuído no status atual."
            )

        # ANALISTA só pode atribuir a si mesmo; ADMIN a qualquer técnico (seção 6.3).
        if ator.tipo_perfil == PerfilUsuario.ANALISTA and id_tecnico != ator.id_usuario:
            raise ErroCicloVida(
                "SEM_PERMISSAO", "Um analista só pode atribuir o chamado a si mesmo."
            )

        # RN03: o responsável precisa ser ANALISTA/ADMIN ativo.
        tecnico = self._usuarios.buscar_tecnico_ativo(id_tecnico)
        if tecnico is None:
            raise ErroCicloVida(
                "RN03_TECNICO_INVALIDO",
                "O responsável deve ser um analista ou administrador ativo.",
            )

        anterior = chamado.status_chamado
        chamado.id_tecnico_responsavel = tecnico.id_usuario
        chamado.status_chamado = StatusChamado.ATRIBUIDO
        chamado.data_atualizacao = _agora()
        self._chamados.flush()
        evento = self._historico.registrar(
            id_chamado=chamado.id_chamado,
            status_anterior=anterior,
            status_novo=StatusChamado.ATRIBUIDO,
            id_autor=ator.id_usuario,
            observacao=observacao or f"Atribuído a {tecnico.nome}",
        )
        if self._eventos is not None:
            self._eventos.chamado_atribuido(chamado=chamado, id_tecnico=tecnico.id_usuario)
            if tecnico.id_usuario != chamado.id_usuario_abertura:
                self._eventos.status_alterado(
                    chamado=chamado,
                    id_solicitante=chamado.id_usuario_abertura,
                    rotulo_novo=ROTULO_STATUS[StatusChamado.ATRIBUIDO],
                )
        return ResultadoTransicao(chamado=chamado, evento=evento)

    # ----- Histórico -----
    def historico(self, *, id_chamado: int) -> list[HistoricoChamado]:
        self._carregar(id_chamado)  # 404 se não existe
        return self._historico.listar_do_chamado(id_chamado)

    # ----- Conclusão: ATRIBUIDO → CONCLUIDO (RN01) -----
    def concluir(
        self, *, ator: Usuario, id_chamado: int, descricao_solucao: str
    ) -> ResultadoTransicao:
        """Técnico responsável ou ADMIN registra a solução e conclui o chamado.

        RN01: concluir **exige** registrar a solução aplicada; a solução nasce
        PENDENTE_APROVACAO. Preenche `data_conclusao`. Só a partir de ATRIBUIDO.
        """
        assert self._solucoes is not None
        self._exigir_tecnico(ator)
        chamado = self._carregar(id_chamado)

        if chamado.status_chamado != StatusChamado.ATRIBUIDO:
            raise ErroCicloVida(
                "TRANSICAO_INVALIDA", "Só é possível concluir um chamado atribuído."
            )
        # Técnico responsável ou ADMIN (seção 6.3).
        if (
            ator.tipo_perfil != PerfilUsuario.ADMIN
            and chamado.id_tecnico_responsavel != ator.id_usuario
        ):
            raise ErroCicloVida(
                "SEM_PERMISSAO", "Apenas o técnico responsável ou um administrador pode concluir."
            )
        if not descricao_solucao.strip():
            raise ErroCicloVida("VALIDACAO", "A descrição da solução é obrigatória (RN01).")

        self._solucoes.criar(
            id_chamado=chamado.id_chamado,
            id_analista=ator.id_usuario,
            descricao_solucao=descricao_solucao,
        )
        anterior = chamado.status_chamado
        chamado.status_chamado = StatusChamado.CONCLUIDO
        agora = _agora()
        chamado.data_conclusao = agora
        chamado.data_atualizacao = agora
        self._chamados.flush()
        evento = self._historico.registrar(
            id_chamado=chamado.id_chamado,
            status_anterior=anterior,
            status_novo=StatusChamado.CONCLUIDO,
            id_autor=ator.id_usuario,
            observacao="Solução registrada",
        )
        if self._eventos is not None:
            self._eventos.solucao_registrada(
                chamado=chamado,
                id_solicitante=chamado.id_usuario_abertura,
                resumo_solucao=descricao_solucao,
            )
        return ResultadoTransicao(chamado=chamado, evento=evento)

    # ----- Resposta do solicitante: CONCLUIDO → FECHADO/ATRIBUIDO (RN02) -----
    def responder_solucao(
        self, *, ator: Usuario, id_chamado: int, aprovada: bool, motivo: str | None = None
    ) -> ResultadoTransicao:
        """Apenas o solicitante responde à solução pendente (RN02).

        - aprovar → FECHADO, `data_fechamento`, solução APROVADO;
        - reprovar (motivo obrigatório) → ATRIBUIDO, solução REJEITADO e o motivo
          vira um follow-up.
        """
        assert self._solucoes is not None
        chamado = self._carregar(id_chamado)

        if chamado.id_usuario_abertura != ator.id_usuario:
            raise ErroCicloVida("SEM_PERMISSAO", "Apenas o solicitante pode responder à solução.")
        if chamado.status_chamado != StatusChamado.CONCLUIDO:
            raise ErroCicloVida(
                "TRANSICAO_INVALIDA", "O chamado não está aguardando aprovação da solução."
            )
        solucao = self._solucoes.buscar_pendente(chamado.id_chamado)
        if solucao is None:
            raise ErroCicloVida("NAO_ENCONTRADO", "Não há solução pendente para responder.")

        anterior = chamado.status_chamado
        agora = _agora()
        if aprovada:
            solucao.status_aprovacao = StatusAprovacao.APROVADO
            chamado.status_chamado = StatusChamado.FECHADO
            chamado.data_fechamento = agora
            chamado.data_atualizacao = agora
            self._chamados.flush()
            evento = self._historico.registrar(
                id_chamado=chamado.id_chamado,
                status_anterior=anterior,
                status_novo=StatusChamado.FECHADO,
                id_autor=ator.id_usuario,
                observacao="Solução aprovada",
            )
        else:
            texto = (motivo or "").strip()
            if not texto:
                raise ErroCicloVida("VALIDACAO", "Informe o motivo da reprovação.")
            solucao.status_aprovacao = StatusAprovacao.REJEITADO
            chamado.status_chamado = StatusChamado.ATRIBUIDO
            chamado.data_conclusao = None
            chamado.data_atualizacao = agora
            self._chamados.flush()
            # O motivo da reprovação vira um follow-up do solicitante.
            if self._followups is not None:
                self._followups.criar(
                    id_chamado=chamado.id_chamado,
                    id_autor=ator.id_usuario,
                    mensagem=f"Solução reprovada: {texto}",
                )
            evento = self._historico.registrar(
                id_chamado=chamado.id_chamado,
                status_anterior=anterior,
                status_novo=StatusChamado.ATRIBUIDO,
                id_autor=ator.id_usuario,
                observacao="Solução reprovada",
            )
        if self._eventos is not None:
            self._eventos.solucao_respondida(
                chamado=chamado, id_tecnico=chamado.id_tecnico_responsavel, aprovada=aprovada
            )
        return ResultadoTransicao(chamado=chamado, evento=evento)

    # ----- Follow-ups -----
    @staticmethod
    def _participa(ator: Usuario, chamado: Chamado) -> bool:
        """Participantes do chamado: solicitante, técnico responsável e ADMIN."""
        return (
            ator.tipo_perfil == PerfilUsuario.ADMIN
            or ator.id_usuario == chamado.id_usuario_abertura
            or ator.id_usuario == chamado.id_tecnico_responsavel
        )

    def listar_followups(self, *, ator: Usuario, id_chamado: int) -> list[FollowUp]:
        assert self._followups is not None
        chamado = self._carregar(id_chamado)
        if not self._participa(ator, chamado):
            raise ErroCicloVida("NAO_ENCONTRADO", "Chamado não encontrado.")
        return self._followups.listar_do_chamado(id_chamado)

    def adicionar_followup(self, *, ator: Usuario, id_chamado: int, mensagem: str) -> FollowUp:
        assert self._followups is not None
        chamado = self._carregar(id_chamado)
        if not self._participa(ator, chamado):
            raise ErroCicloVida("NAO_ENCONTRADO", "Chamado não encontrado.")
        if chamado.status_chamado == StatusChamado.FECHADO:
            raise ErroCicloVida(
                "TRANSICAO_INVALIDA", "Chamado encerrado não aceita novas mensagens."
            )
        if not mensagem.strip():
            raise ErroCicloVida("VALIDACAO", "A mensagem é obrigatória.")
        return self._followups.criar(
            id_chamado=id_chamado, id_autor=ator.id_usuario, mensagem=mensagem
        )

    def solucoes(self, *, id_chamado: int) -> list[Solucao]:
        """Soluções do chamado (para o cartão de solução no detalhe)."""
        assert self._solucoes is not None
        self._carregar(id_chamado)
        return self._solucoes.listar_do_chamado(id_chamado)

    def responder_por_solucao(
        self, *, ator: Usuario, id_solucao: int, aprovada: bool, motivo: str | None = None
    ) -> ResultadoTransicao:
        """Responde pela id da solução (localiza o chamado). 404 se a solução não existe."""
        assert self._solucoes is not None
        solucao = self._solucoes.buscar_por_id(id_solucao)
        if solucao is None:
            raise ErroCicloVida("NAO_ENCONTRADO", "Solução não encontrada.")
        return self.responder_solucao(
            ator=ator, id_chamado=solucao.id_chamado, aprovada=aprovada, motivo=motivo
        )
