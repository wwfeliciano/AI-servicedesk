"""BotService — máquina de atendimento do WhatsApp (seção 9.5, F6.4/F6.4b).

Recebe uma mensagem já normalizada pelo n8n (`chat_id`, `lid`, `numero`, `texto`,
`tem_midia`, `message_id`) e devolve a lista de respostas do bot. As regras ficam
aqui (o n8n é só transporte). Comandos são aceitos **sem diferenciar maiúsculas
nem acentos**.

Fluxos: vínculo (`VINCULAR <código>`), menu, *1* abertura guiada
(categoria→prioridade→título→descrição→confirmar; cria com `canal_origem=WHATSAPP`),
*2* meus chamados, *3*/protocolo status (do próprio — RN06), aprovação/reprovação
da solução (*1*/*2* após o aviso, ou `APROVAR/REPROVAR TK-xxxx`), `SAIR`/`PARAR`
(opt-out), mídia sem texto e número não vinculado. Estado da conversa no Redis.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.core.vinculo_whatsapp import VinculoWhatsApp
from app.entities.enums import CanalOrigem, SeveridadeChamado
from app.integrations.whatsapp import mensagens
from app.integrations.whatsapp.estado import EstadoBot
from app.repositories.chamado_repository import ChamadoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.chamado_service import ChamadoService, ErroChamado
from app.services.ciclo_vida_service import CicloVidaService, ErroCicloVida

_SAUDACOES = {"oi", "ola", "menu", "0", "inicio", "", "bom dia", "boa tarde", "boa noite"}
_RE_PROTOCOLO = re.compile(r"\btk-?0*(\d+)\b", re.IGNORECASE)
_STATUS_ABERTOS = ("NOVO", "PENDENTE", "ATRIBUIDO", "CONCLUIDO")

# Severidade por opção do fluxo guiado (1..4).
_SEVERIDADE_POR_OPCAO = {
    "1": SeveridadeChamado.BAIXA,
    "2": SeveridadeChamado.MEDIA,
    "3": SeveridadeChamado.ALTA,
    "4": SeveridadeChamado.CRITICO,
}
_ROTULO_PRIORIDADE = {"1": "Baixa", "2": "Média", "3": "Alta", "4": "Urgente"}

# Passos do fluxo guiado (gravados em wa:conversa).
PASSO_CATEGORIA = "abrir_categoria"
PASSO_PRIORIDADE = "abrir_prioridade"
PASSO_TITULO = "abrir_titulo"
PASSO_DESCRICAO = "abrir_descricao"
PASSO_CONFIRMAR = "abrir_confirmar"
ESTADO_AGUARDANDO_APROVACAO = "aguardando_aprovacao"


@dataclass(frozen=True)
class MensagemRecebida:
    message_id: str
    chat_id: str
    lid: str | None
    numero: str | None
    texto: str
    tem_midia: bool


def _normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem espaços nas pontas (para casar comandos)."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.strip().lower()


class BotService:
    def __init__(
        self,
        *,
        usuarios: UsuarioRepository,
        chamados: ChamadoRepository,
        chamado_service: ChamadoService,
        ciclo_vida: CicloVidaService,
        vinculo: VinculoWhatsApp,
        estado: EstadoBot,
        portal_url: str,
    ) -> None:
        self._usuarios = usuarios
        self._chamados = chamados
        self._chamado_service = chamado_service
        self._ciclo_vida = ciclo_vida
        self._vinculo = vinculo
        self._estado = estado
        self._portal_url = portal_url.rstrip("/")

    def processar(self, msg: MensagemRecebida) -> list[str]:
        """Devolve as respostas do bot. Lista vazia quando a mensagem é repetida."""
        if self._estado.ja_processada(msg.message_id):
            return []

        texto_norm = _normalizar(msg.texto)
        usuario = self._usuarios.buscar_por_whatsapp(
            chat_id=msg.chat_id, lid=msg.lid, numero=msg.numero
        )

        # Vínculo vale mesmo sem estar vinculado.
        if texto_norm.startswith("vincular"):
            return [self._vincular(msg, texto_norm)]

        if usuario is None:
            return [mensagens.nao_vinculado(self._portal_url)]

        if msg.tem_midia and not texto_norm:
            return [mensagens.midia_sem_texto(self._portal_url)]

        if texto_norm in {"sair", "parar"}:
            self._usuarios.desvincular_whatsapp(usuario)
            self._estado.limpar_conversa(msg.chat_id)
            return [mensagens.opt_out()]

        if texto_norm == "cancelar":
            self._estado.limpar_conversa(msg.chat_id)
            return [mensagens.fluxo_cancelado()]

        # Aprovação/reprovação explícita por comando (APROVAR/REPROVAR TK-xxxx).
        if texto_norm.startswith(("aprovar", "reprovar")):
            return [self._responder_solucao_comando(usuario, msg.texto, texto_norm)]

        # Conversa em andamento (fluxo guiado ou aviso de solução).
        conversa = self._estado.obter_conversa(msg.chat_id)
        passo = conversa.get("passo")
        if passo in {
            PASSO_CATEGORIA,
            PASSO_PRIORIDADE,
            PASSO_TITULO,
            PASSO_DESCRICAO,
            PASSO_CONFIRMAR,
        }:
            return self._fluxo_abertura(usuario, msg, texto_norm, conversa)
        if passo == ESTADO_AGUARDANDO_APROVACAO and texto_norm in {"1", "2"}:
            return [self._responder_solucao_12(usuario, msg.chat_id, conversa, texto_norm)]

        if texto_norm in _SAUDACOES:
            return [mensagens.menu()]
        if texto_norm in {"9", "ajuda", "help"}:
            return [mensagens.ajuda()]
        if texto_norm in {"1", "abrir"}:
            return self._iniciar_abertura(msg.chat_id)
        if texto_norm == "2":
            return [self._meus_chamados(usuario.id_usuario)]
        if texto_norm == "3":
            return ["Envie o número do protocolo (ex.: *TK-0051*)."]

        protocolo = self._extrair_protocolo(msg.texto)
        if protocolo is not None:
            return [self._status(usuario.id_usuario, protocolo, msg.chat_id)]

        return [mensagens.nao_entendi()]

    # ----- vínculo -----

    def _vincular(self, msg: MensagemRecebida, texto_norm: str) -> str:
        partes = texto_norm.split()
        codigo = partes[1] if len(partes) > 1 else ""
        id_usuario = self._vinculo.consumir(codigo) if codigo else None
        if id_usuario is None:
            return mensagens.vinculo_invalido()
        usuario = self._usuarios.buscar_por_id(id_usuario)
        if usuario is None or not usuario.ativo:
            return mensagens.vinculo_invalido()
        self._usuarios.vincular_whatsapp(
            usuario, chat_id=msg.chat_id, lid=msg.lid, numero=msg.numero
        )
        return mensagens.vinculo_ok(usuario.nome)

    # ----- consulta -----

    def _meus_chamados(self, id_usuario: int) -> str:
        itens, _total = self._chamados.listar(
            id_solicitante=id_usuario, grupo=None, page=1, page_size=5
        )
        abertos = [
            (ln.chamado.protocolo, ln.chamado.titulo, ln.chamado.status_chamado.value)
            for ln in itens
            if ln.chamado.status_chamado.value in _STATUS_ABERTOS
        ]
        return mensagens.meus_chamados(abertos)

    def _status(self, id_usuario: int, id_chamado: int, chat_id: str | None = None) -> str:
        linha = self._chamados.obter(id_chamado, id_solicitante=id_usuario)
        if linha is None:
            return mensagens.protocolo_nao_encontrado()
        c = linha.chamado
        responsavel = linha.tecnico.nome if linha.tecnico is not None else None
        # Se o chamado aguarda aprovação do solicitante, arma o atalho 1/2.
        if chat_id is not None and c.status_chamado.value == "CONCLUIDO":
            self._estado.salvar_conversa(
                chat_id,
                {
                    "passo": ESTADO_AGUARDANDO_APROVACAO,
                    "id_chamado": c.id_chamado,
                    "protocolo": c.protocolo,
                },
            )
        return mensagens.status_chamado(
            protocolo=c.protocolo,
            titulo=c.titulo,
            status=c.status_chamado.value,
            responsavel=responsavel,
            link=f"{self._portal_url}/chamados/{c.id_chamado}",
        )

    # ----- fluxo guiado de abertura -----

    def _categorias_numeradas(self) -> list[tuple[int, str, int]]:
        """(posição 1..N, nome, id_categoria) das categorias ativas."""
        ativas = self._chamado_service.listar_categorias()
        return [(i + 1, c.nome_categoria, c.id_categoria) for i, c in enumerate(ativas)]

    def _iniciar_abertura(self, chat_id: str) -> list[str]:
        cats = self._categorias_numeradas()
        mapa = {str(i): cid for i, _n, cid in cats}
        self._estado.salvar_conversa(chat_id, {"passo": PASSO_CATEGORIA, "mapa_categorias": mapa})
        return [mensagens.abrir_categoria([(i, n) for i, n, _c in cats])]

    def _fluxo_abertura(
        self, usuario: Any, msg: MensagemRecebida, texto_norm: str, conversa: dict[str, Any]
    ) -> list[str]:
        passo = conversa.get("passo")
        chat_id = msg.chat_id
        bruto = msg.texto.strip()

        if passo == PASSO_CATEGORIA:
            mapa = conversa.get("mapa_categorias", {})
            if texto_norm not in mapa:
                return [mensagens.abrir_opcao_invalida()]
            conversa.update(passo=PASSO_PRIORIDADE, id_categoria=mapa[texto_norm])
            self._estado.salvar_conversa(chat_id, conversa)
            return [mensagens.abrir_prioridade()]

        if passo == PASSO_PRIORIDADE:
            if texto_norm not in _SEVERIDADE_POR_OPCAO:
                return [mensagens.abrir_opcao_invalida()]
            conversa.update(passo=PASSO_TITULO, severidade=texto_norm)
            self._estado.salvar_conversa(chat_id, conversa)
            return [mensagens.abrir_titulo()]

        if passo == PASSO_TITULO:
            if not bruto or len(bruto) > 150:
                return ["O título precisa ter de 1 a 150 caracteres. Tente de novo."]
            conversa.update(passo=PASSO_DESCRICAO, titulo=bruto)
            self._estado.salvar_conversa(chat_id, conversa)
            return [mensagens.abrir_descricao()]

        if passo == PASSO_DESCRICAO:
            if not bruto or len(bruto) > 500:
                return ["A descrição precisa ter de 1 a 500 caracteres. Tente de novo."]
            conversa.update(passo=PASSO_CONFIRMAR, descricao=bruto)
            self._estado.salvar_conversa(chat_id, conversa)
            cat_nome = self._nome_categoria(int(conversa["id_categoria"]))
            return [
                mensagens.abrir_confirmacao(
                    categoria=cat_nome,
                    prioridade=_ROTULO_PRIORIDADE[conversa["severidade"]],
                    titulo=conversa["titulo"],
                )
            ]

        # PASSO_CONFIRMAR
        if texto_norm == "2":
            self._estado.limpar_conversa(chat_id)
            return [mensagens.abrir_cancelado()]
        if texto_norm != "1":
            return [mensagens.abrir_opcao_invalida()]
        return [self._criar_chamado(usuario, chat_id, conversa)]

    def _criar_chamado(self, usuario: Any, chat_id: str, conversa: dict[str, Any]) -> str:
        try:
            aberto = self._chamado_service.abrir(
                id_solicitante=usuario.id_usuario,
                id_categoria=int(conversa["id_categoria"]),
                titulo=conversa["titulo"],
                descricao=conversa["descricao"],
                severidade=_SEVERIDADE_POR_OPCAO[conversa["severidade"]],
                canal_origem=CanalOrigem.WHATSAPP,
            )
        except ErroChamado as exc:
            self._estado.limpar_conversa(chat_id)
            return f"Não consegui abrir o chamado: {exc.mensagem}"
        self._estado.limpar_conversa(chat_id)
        return mensagens.abrir_sucesso(
            protocolo=aberto.chamado.protocolo,
            link=f"{self._portal_url}/chamados/{aberto.chamado.id_chamado}",
        )

    def _nome_categoria(self, id_categoria: int) -> str:
        for c in self._chamado_service.listar_categorias():
            if c.id_categoria == id_categoria:
                return c.nome_categoria
        return "—"

    # ----- aprovação/reprovação da solução -----

    def _responder_solucao_comando(self, usuario: Any, texto: str, texto_norm: str) -> str:
        protocolo = self._extrair_protocolo(texto)
        if protocolo is None:
            return mensagens.aprovacao_sem_contexto()
        aprovada = texto_norm.startswith("aprovar")
        motivo: str | None = None
        if not aprovada:
            # Tudo após o protocolo é o motivo.
            resto = re.sub(r"(?i)\breprovar\b|\btk-?0*\d+\b", " ", texto).strip()
            if not resto:
                return mensagens.reprovar_pede_motivo(f"TK-{protocolo:04d}")
            motivo = resto
        return self._aplicar_resposta(usuario, protocolo, aprovada, motivo)

    def _responder_solucao_12(
        self, usuario: Any, chat_id: str, conversa: dict[str, Any], texto_norm: str
    ) -> str:
        id_chamado = int(conversa.get("id_chamado", 0))
        aprovada = texto_norm == "1"
        if not aprovada:
            # Reprovar pelo "2" precisa de motivo; orienta o comando.
            self._estado.limpar_conversa(chat_id)
            protocolo = conversa.get("protocolo", f"TK-{id_chamado:04d}")
            return mensagens.reprovar_pede_motivo(protocolo)
        resposta = self._aplicar_resposta_por_chamado(usuario, id_chamado, True, None)
        self._estado.limpar_conversa(chat_id)
        return resposta

    def _aplicar_resposta(
        self, usuario: Any, id_chamado: int, aprovada: bool, motivo: str | None
    ) -> str:
        # RN06: o chamado tem de ser do próprio solicitante.
        if self._chamados.obter(id_chamado, id_solicitante=usuario.id_usuario) is None:
            return mensagens.protocolo_nao_encontrado()
        return self._aplicar_resposta_por_chamado(usuario, id_chamado, aprovada, motivo)

    def _aplicar_resposta_por_chamado(
        self, usuario: Any, id_chamado: int, aprovada: bool, motivo: str | None
    ) -> str:
        protocolo = f"TK-{id_chamado:04d}"
        try:
            resultado = self._ciclo_vida.responder_solucao(
                ator=usuario, id_chamado=id_chamado, aprovada=aprovada, motivo=motivo
            )
            protocolo = resultado.chamado.protocolo
        except ErroCicloVida as exc:
            return f"Não consegui registrar sua resposta: {exc.mensagem}"
        return (
            mensagens.aprovacao_aprovada(protocolo)
            if aprovada
            else mensagens.aprovacao_reprovada(protocolo)
        )

    @staticmethod
    def _extrair_protocolo(texto: str) -> int | None:
        m = _RE_PROTOCOLO.search(texto or "")
        if not m:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None
