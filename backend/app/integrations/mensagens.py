"""Textos das mensagens dos canais externos (seção 9.2, 9.5, 9.6).

Cada função devolve o `payload` que vai no `eventos_outbox` e, depois, ao n8n:

- WhatsApp: ``{"texto": "..."}`` com a formatação do WhatsApp (``*negrito*``);
- E-mail: ``{"assunto": "...", "texto": "...", "html": "..."}``.

Minimização de dados (LGPD, seção 9.5): as mensagens levam protocolo, título,
status e link para o portal. Descrição e solução completas ficam no portal; a
solução vai resumida em até 300 caracteres para permitir a aprovação pelo WhatsApp.
"""

from __future__ import annotations

from typing import Any

SOLUCAO_RESUMO_MAX = 300


def _link_chamado(portal_url: str, id_chamado: int) -> str:
    return f"{portal_url.rstrip('/')}/chamados/{id_chamado}"


def _resumir(texto: str, limite: int = SOLUCAO_RESUMO_MAX) -> str:
    texto = texto.strip()
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"


# ===== WhatsApp =====


def wa_chamado_criado(*, protocolo: str, titulo: str, link: str) -> dict[str, Any]:
    return {
        "texto": (f"✅ *{protocolo}* aberto.\n" f"_{titulo}_\n" f"Acompanhe pelo portal: {link}")
    }


def wa_chamado_urgente(*, protocolo: str, titulo: str, link: str) -> dict[str, Any]:
    return {"texto": (f"🚨 *{protocolo}* (URGENTE) aguarda atendimento.\n" f"_{titulo}_\n{link}")}


def wa_chamado_atribuido(*, protocolo: str, titulo: str, link: str) -> dict[str, Any]:
    return {"texto": (f"👤 *{protocolo}* atribuído.\n_{titulo}_\nEm atendimento. {link}")}


def wa_followup(*, protocolo: str, link: str) -> dict[str, Any]:
    return {"texto": f"💬 Nova mensagem no chamado *{protocolo}*. Veja em {link}"}


def wa_solucao_registrada(*, protocolo: str, resumo_solucao: str, link: str) -> dict[str, Any]:
    return {
        "texto": (
            f"✅ *{protocolo}* — solução registrada.\n"
            f"{_resumir(resumo_solucao)}\n\n"
            "Responda *1* para aprovar e encerrar ou *2* para reprovar.\n"
            f"Detalhes: {link}"
        )
    }


def wa_solucao_aprovada(*, protocolo: str, link: str) -> dict[str, Any]:
    return {"texto": f"🎉 *{protocolo}* encerrado — solução aprovada. {link}"}


def wa_solucao_rejeitada(*, protocolo: str, link: str) -> dict[str, Any]:
    return {
        "texto": (
            f"↩️ *{protocolo}* — a solução foi reprovada e o chamado voltou "
            f"ao atendimento. {link}"
        )
    }


# ===== E-mail =====


def _email(assunto: str, corpo: str, link: str) -> dict[str, Any]:
    texto = f"{corpo}\n\nAcesse o portal: {link}"
    html = f"<p>{corpo}</p>" f'<p><a href="{link}">Abrir no portal Mentory</a></p>'
    return {"assunto": assunto, "texto": texto, "html": html}


def email_chamado_criado(*, protocolo: str, titulo: str, link: str) -> dict[str, Any]:
    return _email(
        f"[Mentory] Chamado {protocolo} aberto",
        f"Seu chamado {protocolo} — {titulo} — foi aberto e está na fila de atendimento.",
        link,
    )


def email_chamado_urgente(*, protocolo: str, titulo: str, link: str) -> dict[str, Any]:
    return _email(
        f"[Mentory] Chamado URGENTE {protocolo}",
        f"O chamado {protocolo} (URGENTE) — {titulo} — aguarda atendimento.",
        link,
    )


def email_chamado_atribuido(*, protocolo: str, titulo: str, link: str) -> dict[str, Any]:
    return _email(
        f"[Mentory] Chamado {protocolo} atribuído",
        f"O chamado {protocolo} — {titulo} — foi atribuído e está em atendimento.",
        link,
    )


def email_solucao_registrada(*, protocolo: str, resumo_solucao: str, link: str) -> dict[str, Any]:
    return _email(
        f"[Mentory] Solução do chamado {protocolo}",
        (
            f"O chamado {protocolo} recebeu uma solução aguardando sua aprovação:\n\n"
            f"{_resumir(resumo_solucao)}"
        ),
        link,
    )


def email_solucao_rejeitada(*, protocolo: str, link: str) -> dict[str, Any]:
    return _email(
        f"[Mentory] Solução reprovada — {protocolo}",
        (
            f"A solução do chamado {protocolo} foi reprovada pelo solicitante e o "
            "chamado voltou ao atendimento. Veja o motivo no acompanhamento."
        ),
        link,
    )


def email_senha_redefinicao(*, link: str) -> dict[str, Any]:
    """E-mail do fluxo "esqueci a senha" (FA02). O link leva à tela de redefinição."""
    corpo = (
        "Recebemos um pedido para redefinir a senha da sua conta no Mentory Help Desk.\n"
        "Se foi você, use o link abaixo (válido por 30 minutos). Se não foi, ignore este e-mail."
    )
    texto = f"{corpo}\n\nRedefinir senha: {link}"
    html = f'<p>{corpo}</p><p><a href="{link}">Redefinir minha senha</a></p>'
    return {"assunto": "[Mentory] Redefinição de senha", "texto": texto, "html": html}
