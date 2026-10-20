"""Schemas (Pydantic v2) de categorias e chamados (contratos da seção 7.3)."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, field_validator

from app.entities.enums import SeveridadeChamado, StatusChamado


class CategoriaSaida(BaseModel):
    id_categoria: int
    nome_categoria: str
    icone: str | None = None
    ordem: int
    ativa: bool


class CategoriaResumo(BaseModel):
    """Categoria aninhada na resposta do chamado."""

    id_categoria: int
    nome_categoria: str
    icone: str | None = None


class UsuarioResumo(BaseModel):
    """Solicitante/técnico aninhado na resposta do chamado."""

    id_usuario: int
    nome: str


class ChamadoCriar(BaseModel):
    """Corpo de POST /api/chamados. O solicitante vem do token, nunca do corpo.

    Título (1..150) e descrição (1..500) são validados **após `strip`** (TU04);
    `severidade` é opcional e assume BAIXA.
    """

    id_categoria: int
    severidade: SeveridadeChamado = SeveridadeChamado.BAIXA
    titulo: str
    descricao: str

    @field_validator("titulo")
    @classmethod
    def _validar_titulo(cls, valor: str) -> str:
        v = valor.strip()
        if not v:
            raise ValueError("O título é obrigatório.")
        if len(v) > 150:
            raise ValueError("O título deve ter no máximo 150 caracteres.")
        return v

    @field_validator("descricao")
    @classmethod
    def _validar_descricao(cls, valor: str) -> str:
        v = valor.strip()
        if not v:
            raise ValueError("A descrição é obrigatória.")
        if len(v) > 500:
            raise ValueError("A descrição deve ter no máximo 500 caracteres.")
        return v


class ChamadoSaida(BaseModel):
    """Resposta de POST /api/chamados e item da lista (seção 7.3)."""

    id_chamado: int
    protocolo: str
    titulo: str
    descricao: str
    categoria: CategoriaResumo
    severidade: SeveridadeChamado
    status_chamado: StatusChamado
    status_grupo: str
    solicitante: UsuarioResumo
    tecnico_responsavel: UsuarioResumo | None = None
    qtd_mensagens: int
    data_criacao: datetime.datetime
    data_atualizacao: datetime.datetime


class ContadoresChamados(BaseModel):
    """Contadores das abas (seção 7.3). Respeitam busca e categoria, ignoram o grupo."""

    todos: int
    abertos: int
    em_andamento: int
    resolvidos: int
    encerrados: int


class ChamadoLista(BaseModel):
    """Envelope de GET /api/chamados (paginação + contadores, seção 7.3)."""

    items: list[ChamadoSaida]
    total: int
    page: int
    page_size: int
    contadores: ContadoresChamados


class ResumoSaida(BaseModel):
    """Indicadores do Dashboard (GET /api/chamados/resumo, seção 7.3)."""

    abertos: int
    em_andamento: int
    resolvidos: int
    encerrados: int
    urgentes: int


class TriagemEntrada(BaseModel):
    """Corpo de POST /api/chamados/{id}/triagem (ajustes opcionais na triagem)."""

    id_categoria: int | None = None
    severidade: SeveridadeChamado | None = None
    observacao: str | None = None


class AtribuicaoEntrada(BaseModel):
    """Corpo de POST /api/chamados/{id}/atribuicao."""

    id_tecnico: int
    observacao: str | None = None


class HistoricoSaida(BaseModel):
    """Item da linha do tempo do chamado (GET /api/chamados/{id}/historico)."""

    id_historico: int
    status_anterior: StatusChamado | None
    status_novo: StatusChamado
    observacao: str | None
    id_autor: int | None
    data_evento: datetime.datetime


class SolucaoCriar(BaseModel):
    """Corpo de POST /api/chamados/{id}/solucoes (RN01)."""

    descricao_solucao: str


class RespostaSolucao(BaseModel):
    """Corpo de POST /api/solucoes/{id}/resposta (RN02)."""

    aprovada: bool
    motivo: str | None = None


class SolucaoSaida(BaseModel):
    id_solucao: int
    descricao_solucao: str
    status_aprovacao: str
    id_analista: int
    data_solucao: datetime.datetime


class FollowUpCriar(BaseModel):
    mensagem: str


class FollowUpSaida(BaseModel):
    id_followup: int
    id_autor: int
    mensagem: str
    data_envio: datetime.datetime
