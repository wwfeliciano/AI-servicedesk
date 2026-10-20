"""Dados de desenvolvimento e de performance (seção 5.7).

- `semear_dev`: 1 admin, 3 analistas e 10 clientes (entre eles "Ana Lima, Analista
  de Marketing" e o analista "Rafael Mendes", como no protótipo) e ~60 chamados
  variados (categorias, severidades e status). Idempotente pelo e-mail.
- `semear_performance`: 200 usuários e 10.000 chamados, em lote, para medir o RNF02.

Tudo fictício e sem PII real (AGENTS.md §8); e-mails em `@empresa.com.br`. Os seeds
só rodam em desenvolvimento (a CLI faz a guarda de ambiente).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.seguranca import gerar_hash_senha
from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.enums import PerfilUsuario, SeveridadeChamado, StatusChamado
from app.entities.usuario import Usuario

SENHA_PADRAO = "mentory-dev-123"

# Clientes fictícios do seed dev (nome, cargo). Inclui a Ana Lima do protótipo.
_CLIENTES_DEV: list[tuple[str, str]] = [
    ("Ana Lima", "Analista de Marketing"),
    ("Bruno Carvalho", "Assistente Administrativo"),
    ("Carla Dias", "Coordenadora de RH"),
    ("Diego Esteves", "Vendedor"),
    ("Elaine Farias", "Analista Financeira"),
    ("Felipe Gomes", "Estagiário de TI"),
    ("Gabriela Horta", "Gerente de Projetos"),
    ("Hugo Itália", "Comprador"),
    ("Isabela Jardim", "Recepcionista"),
    ("João Klein", "Técnico de Logística"),
]
# Analistas fictícios (inclui o Rafael Mendes do protótipo).
_ANALISTAS_DEV: list[str] = ["Rafael Mendes", "Sofia Nunes", "Thiago Oliveira"]

# Títulos variados para os chamados (fictícios).
_TITULOS = [
    "VPN não conecta após atualização do Windows",
    "Solicitar acesso ao sistema Protheus",
    "Troca de monitor com defeito de imagem",
    "Erro ao emitir nota fiscal",
    "Outlook não sincroniza e-mails",
    "Impressora do 2º andar fora do ar",
    "Reset de senha do portal de benefícios",
    "Notebook lento após inicialização",
    "Instalação do Microsoft Teams",
    "Acesso negado à pasta compartilhada",
    "Telefone IP sem linha",
    "Cadastro de novo fornecedor no ERP",
]
_DESCRICAO = (
    "Descrição fictícia de demonstração: o usuário relatou o problema e aguarda "
    "o atendimento da equipe de suporte."
)


def _email(nome: str, dominio: str = "empresa.com.br") -> str:
    base = nome.strip().lower().replace(" ", ".")
    # Remove acentos simples para o e-mail (EmailStr do protótipo usa ASCII).
    tabela = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    return f"{base.translate(tabela)}@{dominio}"


@dataclass(frozen=True)
class ResumoSeed:
    usuarios_criados: int
    chamados_criados: int
    mensagem: str


def _garantir_usuario(
    sessao: Session,
    *,
    nome: str,
    perfil: PerfilUsuario,
    cargo: str | None,
    senha_hash: str,
) -> tuple[int, bool]:
    """Cria o usuário se o e-mail não existir. Devolve (id, criado?)."""
    email = _email(nome)
    existente = sessao.scalar(select(Usuario.id_usuario).where(Usuario.email == email))
    if existente is not None:
        return int(existente), False
    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=senha_hash,
        tipo_perfil=perfil,
        cargo=cargo,
    )
    sessao.add(usuario)
    sessao.flush()
    return usuario.id_usuario, True


def semear_dev(sessao: Session) -> ResumoSeed:
    """Popula o ambiente de dev (idempotente). ~60 chamados variados."""
    senha_hash = gerar_hash_senha(SENHA_PADRAO)
    criados_usuarios = 0

    # Admin de demonstração (separado do make criar-admin).
    _, novo = _garantir_usuario(
        sessao,
        nome="Admin Demo",
        perfil=PerfilUsuario.ADMIN,
        cargo="Administrador",
        senha_hash=senha_hash,
    )
    criados_usuarios += int(novo)

    ids_analistas: list[int] = []
    for nome in _ANALISTAS_DEV:
        aid, novo = _garantir_usuario(
            sessao,
            nome=nome,
            perfil=PerfilUsuario.ANALISTA,
            cargo="Analista de Suporte",
            senha_hash=senha_hash,
        )
        ids_analistas.append(aid)
        criados_usuarios += int(novo)

    ids_clientes: list[int] = []
    for nome, cargo in _CLIENTES_DEV:
        cid, novo = _garantir_usuario(
            sessao, nome=nome, perfil=PerfilUsuario.CLIENTE, cargo=cargo, senha_hash=senha_hash
        )
        ids_clientes.append(cid)
        criados_usuarios += int(novo)

    categorias = [int(c) for c in sessao.scalars(select(Categoria.id_categoria)).all()]

    # Idempotência dos chamados: semeia só se os clientes do seed ainda não têm
    # chamados (ignora dados avulsos de outros usuários, como testes manuais).
    ja_tem_do_seed = int(
        sessao.scalar(
            select(func.count())
            .select_from(Chamado)
            .where(Chamado.id_usuario_abertura.in_(ids_clientes))
        )
        or 0
    )
    criados_chamados = 0
    if ja_tem_do_seed == 0:
        rng = random.Random(42)  # determinístico
        severidades = list(SeveridadeChamado)
        # Distribuição de status realista; ATRIBUIDO+ exige técnico (CHECK RN03).
        plano_status = (
            [StatusChamado.NOVO] * 18
            + [StatusChamado.PENDENTE] * 12
            + [StatusChamado.ATRIBUIDO] * 14
            + [StatusChamado.CONCLUIDO] * 10
            + [StatusChamado.FECHADO] * 6
        )
        for i, status_chamado in enumerate(plano_status):
            solicitante = rng.choice(ids_clientes)
            severidade = rng.choice(severidades)
            tecnico = (
                rng.choice(ids_analistas)
                if status_chamado
                in (StatusChamado.ATRIBUIDO, StatusChamado.CONCLUIDO, StatusChamado.FECHADO)
                else None
            )
            sessao.add(
                _novo_chamado_orm(
                    id_usuario_abertura=solicitante,
                    id_categoria=rng.choice(categorias),
                    titulo=_TITULOS[i % len(_TITULOS)],
                    severidade=severidade,
                    status_chamado=status_chamado,
                    id_tecnico=tecnico,
                )
            )
            criados_chamados += 1
        sessao.flush()

    return ResumoSeed(
        usuarios_criados=criados_usuarios,
        chamados_criados=criados_chamados,
        mensagem=(
            f"Seed dev: {criados_usuarios} usuário(s) novo(s), "
            f"{criados_chamados} chamado(s). Senha padrão: {SENHA_PADRAO}"
        ),
    )


def _novo_chamado_orm(
    *,
    id_usuario_abertura: int,
    id_categoria: int,
    titulo: str,
    severidade: SeveridadeChamado,
    status_chamado: StatusChamado,
    id_tecnico: int | None,
) -> Chamado:
    return Chamado(
        id_usuario_abertura=id_usuario_abertura,
        id_categoria=id_categoria,
        titulo=titulo,
        descricao=_DESCRICAO,
        severidade=severidade,
        status_chamado=status_chamado,
        id_tecnico_responsavel=id_tecnico,
    )


def semear_performance(
    sessao: Session, *, qtd_usuarios: int = 200, qtd_chamados: int = 10_000
) -> ResumoSeed:
    """Popula em lote para medir o RNF02. Insere usuários e chamados com SQL em
    massa (todas as senhas com o mesmo hash, já que são dados de carga)."""
    senha_hash = gerar_hash_senha(SENHA_PADRAO)

    # Usuários de carga (clientes), com e-mail único por índice.
    linhas_usuarios = [
        {
            "nome": f"Usuário Carga {i:04d}",
            "email": f"carga{i:04d}@empresa.com.br",
            "senha_hash": senha_hash,
            "perfil": "CLIENTE",
            "cargo": "Colaborador",
            "ativo": True,
        }
        for i in range(qtd_usuarios)
    ]
    sessao.execute(
        text(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo_perfil, cargo, ativo) "
            "VALUES (:nome, :email, :senha_hash, CAST(:perfil AS perfil_usuario), :cargo, :ativo) "
            "ON CONFLICT (email) DO NOTHING"
        ),
        linhas_usuarios,
    )

    ids_clientes = [
        int(r)
        for r in sessao.scalars(
            select(Usuario.id_usuario).where(Usuario.email.like("carga%@empresa.com.br"))
        ).all()
    ]
    categorias = [int(c) for c in sessao.scalars(select(Categoria.id_categoria)).all()]

    rng = random.Random(7)
    severidades = ["BAIXA", "MEDIA", "ALTA", "CRITICO"]
    # Carga só com status que não exigem técnico (NOVO/PENDENTE) — evita o CHECK RN03
    # e mantém a inserção em massa simples.
    status_carga = ["NOVO", "PENDENTE"]
    linhas_chamados = [
        {
            "id_usuario_abertura": rng.choice(ids_clientes),
            "id_categoria": rng.choice(categorias),
            "titulo": f"{rng.choice(_TITULOS)} #{i}",
            "descricao": _DESCRICAO,
            "severidade": rng.choice(severidades),
            "status_chamado": rng.choice(status_carga),
        }
        for i in range(qtd_chamados)
    ]
    sessao.execute(
        text(
            "INSERT INTO chamados "
            "(id_usuario_abertura, id_categoria, titulo, descricao, severidade, status_chamado) "
            "VALUES (:id_usuario_abertura, :id_categoria, :titulo, :descricao, "
            "CAST(:severidade AS severidade_chamado), CAST(:status_chamado AS status_chamado))"
        ),
        linhas_chamados,
    )
    sessao.flush()
    return ResumoSeed(
        usuarios_criados=len(ids_clientes),
        chamados_criados=qtd_chamados,
        mensagem=(
            f"Seed performance: ~{len(ids_clientes)} usuários de carga e "
            f"{qtd_chamados} chamados."
        ),
    )
