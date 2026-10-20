"""Service de eventos de domínio — canais Portal, e-mail e WhatsApp (F3.2, F6.1).

O `EventoService` transforma eventos do domínio (abertura, triagem, atribuição,
solução…) em:

- **notificações de portal** (tabela `notificacoes`), e
- **eventos do outbox** (tabela `eventos_outbox`) para e-mail e WhatsApp,

sempre na **mesma transação** da mudança de estado (seção 9.2). Os canais seguem a
matriz da seção 9.6 e as preferências de cada destinatário:

- WhatsApp só para quem está **vinculado** (`whatsapp_chat_id`) e com **opt-in**;
- e-mail respeita `notificar_email` (a redefinição de senha é exceção, F7).

Até a F6.2 o `worker` não despacha o outbox (`OUTBOX_HABILITADO=false`): os eventos
ficam `PENDENTE`. Nada aqui conhece HTTP nem SMTP/WAHA — o n8n é só transporte.
"""

from __future__ import annotations

from typing import Any

from app.entities.chamado import Chamado
from app.entities.enums import CanalNotificacao, SeveridadeChamado
from app.entities.usuario import Usuario
from app.integrations import mensagens
from app.repositories.notificacao_repository import NotificacaoRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.usuario_repository import UsuarioRepository

TIPO_CHAMADO_CRIADO = "CHAMADO_CRIADO"
TIPO_CHAMADO_URGENTE = "CHAMADO_URGENTE"
TIPO_STATUS_ALTERADO = "STATUS_ALTERADO"
TIPO_CHAMADO_ATRIBUIDO = "CHAMADO_ATRIBUIDO"
TIPO_FOLLOWUP_ADICIONADO = "FOLLOWUP_ADICIONADO"
TIPO_SOLUCAO_REGISTRADA = "SOLUCAO_REGISTRADA"
TIPO_SOLUCAO_APROVADA = "SOLUCAO_APROVADA"
TIPO_SOLUCAO_REJEITADA = "SOLUCAO_REJEITADA"
TIPO_SENHA_REDEFINICAO = "SENHA_REDEFINICAO"


class EventoService:
    def __init__(
        self,
        *,
        notificacoes: NotificacaoRepository,
        usuarios: UsuarioRepository,
        outbox: OutboxRepository | None = None,
        portal_url: str = "http://localhost:8180",
    ) -> None:
        self._notificacoes = notificacoes
        self._usuarios = usuarios
        self._outbox = outbox
        self._portal_url = portal_url

    # ----- helpers de canais externos -----

    def _link(self, id_chamado: int) -> str:
        return f"{self._portal_url.rstrip('/')}/chamados/{id_chamado}"

    def _enfileirar_email(self, *, usuario: Usuario, tipo: str, payload: dict[str, Any]) -> None:
        """Enfileira um e-mail se houver outbox, e-mail e a preferência estiver ligada."""
        if self._outbox is None or not usuario.notificar_email or not usuario.email:
            return
        self._outbox.enfileirar(
            tipo=tipo, canal=CanalNotificacao.EMAIL, destino=usuario.email, payload=payload
        )

    def _enfileirar_whatsapp(self, *, usuario: Usuario, tipo: str, payload: dict[str, Any]) -> None:
        """Enfileira um WhatsApp se houver outbox, vínculo e opt-in."""
        if self._outbox is None or not usuario.whatsapp_opt_in or not usuario.whatsapp_chat_id:
            return
        self._outbox.enfileirar(
            tipo=tipo,
            canal=CanalNotificacao.WHATSAPP,
            destino=usuario.whatsapp_chat_id,
            payload=payload,
        )

    def _usuario(self, id_usuario: int | None) -> Usuario | None:
        if id_usuario is None:
            return None
        return self._usuarios.buscar_por_id(id_usuario)

    # ----- eventos -----

    def chamado_criado(self, *, chamado: Chamado, solicitante: Usuario) -> None:
        """Abertura: confirma ao solicitante (portal/e-mail/WhatsApp) e, se CRITICO,
        alerta os técnicos ativos (seção 6.3, matriz 9.6)."""
        self._notificacoes.criar(
            id_usuario=solicitante.id_usuario,
            id_chamado=chamado.id_chamado,
            tipo=TIPO_CHAMADO_CRIADO,
            titulo="Chamado aberto",
            mensagem=f"Seu chamado {chamado.protocolo} foi aberto e está na fila.",
        )
        link = self._link(chamado.id_chamado)
        self._enfileirar_email(
            usuario=solicitante,
            tipo=TIPO_CHAMADO_CRIADO,
            payload=mensagens.email_chamado_criado(
                protocolo=chamado.protocolo, titulo=chamado.titulo, link=link
            ),
        )
        self._enfileirar_whatsapp(
            usuario=solicitante,
            tipo=TIPO_CHAMADO_CRIADO,
            payload=mensagens.wa_chamado_criado(
                protocolo=chamado.protocolo, titulo=chamado.titulo, link=link
            ),
        )

        if chamado.severidade == SeveridadeChamado.CRITICO:
            for id_tecnico in self._usuarios.ids_tecnicos_ativos():
                if id_tecnico == solicitante.id_usuario:
                    continue
                tecnico = self._usuario(id_tecnico)
                self._notificacoes.criar(
                    id_usuario=id_tecnico,
                    id_chamado=chamado.id_chamado,
                    tipo=TIPO_CHAMADO_URGENTE,
                    titulo="Chamado urgente",
                    mensagem=(
                        f"Chamado {chamado.protocolo} (URGENTE) aguarda atendimento: "
                        f"{chamado.titulo}"
                    ),
                )
                if tecnico is None:
                    continue
                self._enfileirar_email(
                    usuario=tecnico,
                    tipo=TIPO_CHAMADO_URGENTE,
                    payload=mensagens.email_chamado_urgente(
                        protocolo=chamado.protocolo, titulo=chamado.titulo, link=link
                    ),
                )
                self._enfileirar_whatsapp(
                    usuario=tecnico,
                    tipo=TIPO_CHAMADO_URGENTE,
                    payload=mensagens.wa_chamado_urgente(
                        protocolo=chamado.protocolo, titulo=chamado.titulo, link=link
                    ),
                )

    def status_alterado(self, *, chamado: Chamado, id_solicitante: int, rotulo_novo: str) -> None:
        """Triagem: só portal (matriz 9.6)."""
        self._notificacoes.criar(
            id_usuario=id_solicitante,
            id_chamado=chamado.id_chamado,
            tipo=TIPO_STATUS_ALTERADO,
            titulo="Status atualizado",
            mensagem=f"O chamado {chamado.protocolo} agora está: {rotulo_novo}.",
        )

    def chamado_atribuido(self, *, chamado: Chamado, id_tecnico: int) -> None:
        """Atribuição: portal/e-mail/WhatsApp ao técnico (matriz 9.6)."""
        self._notificacoes.criar(
            id_usuario=id_tecnico,
            id_chamado=chamado.id_chamado,
            tipo=TIPO_CHAMADO_ATRIBUIDO,
            titulo="Chamado atribuído a você",
            mensagem=f"O chamado {chamado.protocolo} foi atribuído a você: {chamado.titulo}",
        )
        tecnico = self._usuario(id_tecnico)
        if tecnico is None:
            return
        link = self._link(chamado.id_chamado)
        self._enfileirar_email(
            usuario=tecnico,
            tipo=TIPO_CHAMADO_ATRIBUIDO,
            payload=mensagens.email_chamado_atribuido(
                protocolo=chamado.protocolo, titulo=chamado.titulo, link=link
            ),
        )
        self._enfileirar_whatsapp(
            usuario=tecnico,
            tipo=TIPO_CHAMADO_ATRIBUIDO,
            payload=mensagens.wa_chamado_atribuido(
                protocolo=chamado.protocolo, titulo=chamado.titulo, link=link
            ),
        )

    def followup_adicionado(self, *, chamado: Chamado, id_destinatario: int | None) -> None:
        """Nova mensagem: portal + WhatsApp à outra parte (matriz 9.6, sem e-mail)."""
        if id_destinatario is None:
            return
        self._notificacoes.criar(
            id_usuario=id_destinatario,
            id_chamado=chamado.id_chamado,
            tipo=TIPO_FOLLOWUP_ADICIONADO,
            titulo="Nova mensagem",
            mensagem=f"O chamado {chamado.protocolo} recebeu uma nova mensagem.",
        )
        destinatario = self._usuario(id_destinatario)
        if destinatario is None:
            return
        self._enfileirar_whatsapp(
            usuario=destinatario,
            tipo=TIPO_FOLLOWUP_ADICIONADO,
            payload=mensagens.wa_followup(
                protocolo=chamado.protocolo, link=self._link(chamado.id_chamado)
            ),
        )

    def solucao_registrada(
        self, *, chamado: Chamado, id_solicitante: int, resumo_solucao: str = ""
    ) -> None:
        """→ CONCLUIDO: portal/e-mail/WhatsApp ao solicitante (com 1/2 no WhatsApp)."""
        self._notificacoes.criar(
            id_usuario=id_solicitante,
            id_chamado=chamado.id_chamado,
            tipo=TIPO_SOLUCAO_REGISTRADA,
            titulo="Solução registrada",
            mensagem=(f"O chamado {chamado.protocolo} tem uma solução aguardando sua aprovação."),
        )
        solicitante = self._usuario(id_solicitante)
        if solicitante is None:
            return
        link = self._link(chamado.id_chamado)
        self._enfileirar_email(
            usuario=solicitante,
            tipo=TIPO_SOLUCAO_REGISTRADA,
            payload=mensagens.email_solucao_registrada(
                protocolo=chamado.protocolo, resumo_solucao=resumo_solucao, link=link
            ),
        )
        self._enfileirar_whatsapp(
            usuario=solicitante,
            tipo=TIPO_SOLUCAO_REGISTRADA,
            payload=mensagens.wa_solucao_registrada(
                protocolo=chamado.protocolo, resumo_solucao=resumo_solucao, link=link
            ),
        )

    def solucao_respondida(
        self, *, chamado: Chamado, id_tecnico: int | None, aprovada: bool
    ) -> None:
        """Resposta do solicitante ao técnico (matriz 9.6):
        aprovada → portal + WhatsApp; reprovada → portal + e-mail + WhatsApp."""
        if id_tecnico is None:
            return
        tecnico = self._usuario(id_tecnico)
        link = self._link(chamado.id_chamado)
        if aprovada:
            self._notificacoes.criar(
                id_usuario=id_tecnico,
                id_chamado=chamado.id_chamado,
                tipo=TIPO_SOLUCAO_APROVADA,
                titulo="Solução aprovada",
                mensagem=f"O solicitante aprovou a solução do chamado {chamado.protocolo}.",
            )
            if tecnico is not None:
                self._enfileirar_whatsapp(
                    usuario=tecnico,
                    tipo=TIPO_SOLUCAO_APROVADA,
                    payload=mensagens.wa_solucao_aprovada(protocolo=chamado.protocolo, link=link),
                )
        else:
            self._notificacoes.criar(
                id_usuario=id_tecnico,
                id_chamado=chamado.id_chamado,
                tipo=TIPO_SOLUCAO_REJEITADA,
                titulo="Solução reprovada",
                mensagem=(
                    f"O solicitante reprovou a solução do chamado {chamado.protocolo}. "
                    "Veja o motivo no acompanhamento."
                ),
            )
            if tecnico is not None:
                self._enfileirar_email(
                    usuario=tecnico,
                    tipo=TIPO_SOLUCAO_REJEITADA,
                    payload=mensagens.email_solucao_rejeitada(
                        protocolo=chamado.protocolo, link=link
                    ),
                )
                self._enfileirar_whatsapp(
                    usuario=tecnico,
                    tipo=TIPO_SOLUCAO_REJEITADA,
                    payload=mensagens.wa_solucao_rejeitada(protocolo=chamado.protocolo, link=link),
                )

    def senha_redefinicao(self, *, usuario: Usuario, token: str) -> None:
        """Enfileira o e-mail de redefinição de senha (FA02).

        Exceção da matriz 9.6: **ignora `notificar_email`** (é um e-mail transacional
        de segurança, não uma notificação opcional). Só e-mail; sem portal/WhatsApp.
        """
        if self._outbox is None or not usuario.email:
            return
        link = f"{self._portal_url}/redefinir-senha?token={token}"
        self._outbox.enfileirar(
            tipo=TIPO_SENHA_REDEFINICAO,
            canal=CanalNotificacao.EMAIL,
            destino=usuario.email,
            payload=mensagens.email_senha_redefinicao(link=link),
        )
