"""Textos do bot de atendimento do WhatsApp (seção 9.5).

Formatação do WhatsApp: `*negrito*`, `_itálico_`. Minimização de dados (LGPD):
as mensagens levam protocolo, título, status e link; descrição e solução ficam no
portal. Mantidos aqui (não no n8n) e cobertos por testes.
"""

from __future__ import annotations

from collections.abc import Sequence

ROTULO_STATUS = {
    "NOVO": "Aberto",
    "PENDENTE": "Em triagem",
    "ATRIBUIDO": "Em atendimento",
    "CONCLUIDO": "Aguardando sua aprovação",
    "FECHADO": "Encerrado",
}


def menu() -> str:
    return (
        "👋 *Mentory Help Desk*\n"
        "Como posso ajudar?\n\n"
        "*1* - Abrir um chamado\n"
        "*2* - Meus chamados em aberto\n"
        "*3* - Consultar um protocolo (ex.: TK-0051)\n"
        "*9* - Ajuda\n\n"
        "Envie *SAIR* para deixar de receber mensagens."
    )


def ajuda() -> str:
    return (
        "❓ *Ajuda*\n"
        "• *1* abre um chamado passo a passo.\n"
        "• *2* lista seus chamados em aberto.\n"
        "• *3* ou um protocolo (TK-0051) mostra o status.\n"
        "• Envie _TK-0051 sua mensagem_ para responder a um chamado.\n"
        "• *SAIR* encerra as notificações.\n"
        "Digite *menu* a qualquer momento."
    )


def nao_vinculado(portal_url: str) -> str:
    return (
        "Olá! Este é o atendimento do *Mentory Help Desk*.\n\n"
        "Não encontrei seu cadastro vinculado a este número. Para vincular, acesse o portal, "
        "vá em *Perfil → WhatsApp* e siga as instruções.\n"
        f"{portal_url.rstrip('/')}/perfil\n\n"
        "Se você já tem um código, envie: *VINCULAR 123456*."
    )


def vinculo_ok(nome: str) -> str:
    return (
        f"✅ Pronto, *{nome.split()[0] if nome.strip() else 'tudo certo'}*! "
        "Seu WhatsApp foi vinculado.\n"
        "Digite *menu* para começar."
    )


def vinculo_invalido() -> str:
    return (
        "❌ Código de vínculo inválido ou expirado. "
        "Gere um novo no portal em *Perfil → WhatsApp* e tente de novo."
    )


def opt_out() -> str:
    return (
        "Tudo bem, você não receberá mais mensagens por aqui. 👋\n"
        "Se mudar de ideia, vincule novamente no portal em *Perfil → WhatsApp*."
    )


def midia_sem_texto(portal_url: str) -> str:
    return (
        "Por enquanto recebo só texto. Para anexar arquivos, use o portal: "
        f"{portal_url.rstrip('/')}"
    )


def nao_entendi() -> str:
    return "Não entendi. 🤔 Digite *menu* para ver as opções."


def _linha_chamado(protocolo: str, titulo: str, status: str) -> str:
    rotulo = ROTULO_STATUS.get(status, status)
    return f"*{protocolo}* — {rotulo}\n_{titulo}_"


def meus_chamados(itens: Sequence[tuple[str, str, str]]) -> str:
    """`itens`: (protocolo, titulo, status) dos chamados não encerrados."""
    if not itens:
        return "Você não tem chamados em aberto. 🎉 Digite *1* para abrir um."
    corpo = "\n\n".join(_linha_chamado(p, t, s) for (p, t, s) in itens)
    return "🗂️ *Seus chamados em aberto:*\n\n" + corpo


def status_chamado(
    *, protocolo: str, titulo: str, status: str, responsavel: str | None, link: str
) -> str:
    rotulo = ROTULO_STATUS.get(status, status)
    resp = responsavel or "sem responsável"
    return (
        f"🔎 *{protocolo}*\n"
        f"_{titulo}_\n"
        f"Status: *{rotulo}*\n"
        f"Responsável: {resp}\n"
        f"Detalhes: {link}"
    )


def protocolo_nao_encontrado() -> str:
    return (
        "Não encontrei esse protocolo entre os seus chamados. "
        "Confira o número (ex.: *TK-0051*) ou digite *2* para ver os seus."
    )


# ===== Fluxo guiado de abertura (F6.4b) =====


def abrir_categoria(categorias: Sequence[tuple[int, str]]) -> str:
    """`categorias`: (posição 1..N, nome). Lista numerada para escolher."""
    linhas = "\n".join(f"*{i}* - {nome}" for (i, nome) in categorias)
    return "📝 *Novo chamado* (envie *cancelar* para sair)\n\n" "Qual a categoria?\n" + linhas


def abrir_prioridade() -> str:
    return "Qual a prioridade?\n" "*1* - Baixa\n*2* - Média\n*3* - Alta\n*4* - Urgente"


def abrir_titulo() -> str:
    return "Em uma linha, qual é o *título* do chamado? (até 150 caracteres)"


def abrir_descricao() -> str:
    return "Agora *descreva* o problema com detalhes. (até 500 caracteres)"


def abrir_confirmacao(*, categoria: str, prioridade: str, titulo: str) -> str:
    return (
        "Confere os dados?\n\n"
        f"Categoria: *{categoria}*\n"
        f"Prioridade: *{prioridade}*\n"
        f"Título: _{titulo}_\n\n"
        "*1* - Confirmar e abrir\n*2* - Cancelar"
    )


def abrir_opcao_invalida() -> str:
    return "Opção inválida. Responda com o *número* da opção ou envie *cancelar*."


def abrir_sucesso(*, protocolo: str, link: str) -> str:
    return (
        f"✅ Chamado aberto! Protocolo *{protocolo}*.\n"
        f"Acompanhe por aqui (digite *{protocolo}*) ou no portal: {link}"
    )


def abrir_cancelado() -> str:
    return "Tudo bem, cancelei a abertura. Digite *menu* quando quiser."


def fluxo_cancelado() -> str:
    return "Ok, cancelei. Digite *menu* para ver as opções."


# ===== Aprovação da solução pelo WhatsApp (F6.4b) =====


def aprovacao_sem_contexto() -> str:
    return (
        "Para aprovar ou reprovar uma solução, use *APROVAR TK-0051* ou "
        "*REPROVAR TK-0051 motivo*."
    )


def aprovacao_aprovada(protocolo: str) -> str:
    return f"🎉 Obrigado! A solução do *{protocolo}* foi aprovada e o chamado foi encerrado."


def aprovacao_reprovada(protocolo: str) -> str:
    return (
        f"↩️ Entendido. A solução do *{protocolo}* foi reprovada e o chamado "
        "voltou para o atendimento."
    )


def reprovar_pede_motivo(protocolo: str) -> str:
    return f"Para reprovar o *{protocolo}*, envie: *REPROVAR {protocolo} o motivo*."
