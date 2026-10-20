"""Fixtures compartilhadas dos testes.

A F0.2 testa `/api/health/db` com a dependência de sessão substituída (sem banco).
A F0.3 adiciona testes com PostgreSQL real: a URL vem do `.env` da raiz do
repositório, reescrita para o host (`db:5432` → `127.0.0.1:PORTA_DB`), já que o
pytest roda no host, não dentro da rede do Compose. Se o banco não estiver no ar,
esses testes são pulados (`skip`), não falham.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import fakeredis
import pytest
import redis
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

# Ambiente de teste determinístico (definido antes de instanciar a app/config).
# AMBIENTE=test: a app pula a criação de buckets do MinIO no startup (lifespan),
# o que evita ~10 s de setup por teste. Não é 'prod' (CORS/docs seguem como dev).
os.environ.setdefault("AMBIENTE", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://helpdesk:x@db:5432/helpdesk")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
# BCrypt custo baixo deixa os testes rápidos (seção 10.2: "Use 4 nos testes").
os.environ.setdefault("BCRYPT_CUSTO", "4")
# Chave de integração conhecida para os testes do bot (F6.4).
os.environ.setdefault("INTEGRACAO_API_KEY", "chave-de-teste")
os.environ.setdefault("JWT_SECRET", "segredo-de-teste-com-mais-de-32-bytes-aqui-ok")

from app.controllers.dependencias import (
    obter_anexo_service,
    obter_auth_service,
    obter_base_conhecimento_service,
    obter_bot_service,
    obter_chamado_service,
    obter_ciclo_vida_service,
    obter_estado_bot,
    obter_notificacao_service,
    obter_outbox_service,
    obter_perfil_service,
    obter_sla_service,
    obter_usuario_service,
)
from app.core.database import obter_sessao
from app.core.rate_limit import LimiteTentativasLogin
from app.core.seguranca import gerar_hash_senha
from app.core.storage import StorageMemoria
from app.core.vinculo_whatsapp import VinculoWhatsApp
from app.integrations.whatsapp.estado import EstadoBot
from app.main import create_app
from app.repositories.anexo_repository import AnexoRepository
from app.repositories.base_conhecimento_repository import BaseConhecimentoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.chamado_historico_repository import HistoricoRepository
from app.repositories.chamado_repository import ChamadoRepository
from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.notificacao_repository import NotificacaoRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.sla_repository import SlaRepository
from app.repositories.solucao_repository import SolucaoRepository
from app.repositories.token_redefinicao_repository import TokenRedefinicaoRepository
from app.repositories.token_refresh_repository import TokenRefreshRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.anexo_service import AnexoService
from app.services.auth_service import AuthService
from app.services.base_conhecimento_service import BaseConhecimentoService
from app.services.bot_service import BotService
from app.services.chamado_service import ChamadoService
from app.services.ciclo_vida_service import CicloVidaService
from app.services.evento_service import EventoService
from app.services.notificacao_service import NotificacaoService
from app.services.outbox_service import OutboxService
from app.services.perfil_service import PerfilService
from app.services.sla_service import SlaService
from app.services.usuario_service import UsuarioService


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as cliente:
        yield cliente


def _ler_env_raiz() -> dict[str, str]:
    """Lê o `.env` da raiz do repositório (duas pastas acima de tests/)."""
    caminho = Path(__file__).resolve().parents[2] / ".env"
    valores: dict[str, str] = {}
    if not caminho.exists():
        return valores
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip()
    return valores


def url_banco_host() -> str | None:
    """URL de um banco **de teste dedicado**, acessível pelo host.

    Usa o mesmo servidor/porta do dev, mas um banco separado (`<POSTGRES_DB>_test`),
    criado sob demanda. Assim os testes destrutivos (ida e volta das migrations) e as
    fixtures de integração **nunca tocam os dados de desenvolvimento** (AGENTS.md §5).
    Em CI, `POSTGRES_DB` já é efêmero; o sufixo `_test` continua válido.

    Devolve `None` quando não há `.env` com as variáveis do PostgreSQL.
    """
    env = _ler_env_raiz()
    usuario = env.get("POSTGRES_USER")
    senha = env.get("POSTGRES_PASSWORD")
    banco = env.get("POSTGRES_DB")
    porta = env.get("PORTA_DB", "5442")
    if not (usuario and senha and banco):
        return None

    banco_teste = f"{banco}_test"
    base = f"postgresql+psycopg://{usuario}:{senha}@127.0.0.1:{porta}"
    _garantir_banco(f"{base}/{banco}", banco_teste)
    return f"{base}/{banco_teste}"


def _garantir_banco(url_admin: str, nome: str) -> None:
    """Cria o banco `nome` se não existir (idempotente). Silencioso se o servidor
    não estiver acessível — os testes então pulam via `engine_banco`/`_banco_ou_skip`."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError

    engine = create_engine(url_admin, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conexao:
            existe = conexao.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": nome}
            ).scalar()
            if not existe:
                # Nome vindo de config própria (sufixo fixo), não de entrada do usuário.
                conexao.execute(text(f'CREATE DATABASE "{nome}"'))
    except OperationalError:
        pass
    finally:
        engine.dispose()


# ===== Fixtures de integração (API + PostgreSQL real + fakeredis) =====
# Cada teste roda numa transação desfeita no fim (rollback); o esquema é aplicado
# uma vez por sessão com `alembic upgrade head` (seção 12.1). Redis é fakeredis.

_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _config_alembic_para(url: str) -> AlembicConfig:
    cfg = AlembicConfig(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "app" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture(scope="session")
def engine_banco() -> Iterator[Engine]:
    """Engine para o PostgreSQL real do host; pula se o banco não estiver no ar."""
    url = url_banco_host()
    if url is None:
        pytest.skip("Sem .env com variáveis do PostgreSQL; teste de integração pulado.")
    engine = create_engine(url)
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except OperationalError:
        engine.dispose()
        pytest.skip("Banco não está no ar (127.0.0.1); teste de integração pulado.")
    alembic_command.upgrade(_config_alembic_para(url), "head")
    yield engine
    engine.dispose()


@pytest.fixture
def sessao_banco(engine_banco: Engine) -> Iterator[Session]:
    """Sessão ligada a uma transação externa desfeita no fim do teste (isolamento)."""
    conexao = engine_banco.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, autoflush=False, expire_on_commit=False)
    try:
        yield sessao
    finally:
        sessao.close()
        transacao.rollback()
        conexao.close()


@pytest.fixture
def redis_fake() -> fakeredis.FakeStrictRedis:
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def app_integrado(
    sessao_banco: Session, redis_fake: fakeredis.FakeStrictRedis
) -> Iterator[TestClient]:
    """App com a sessão transacional e o Redis fake injetados por dependency_overrides."""
    app = create_app()

    def _sessao_sobrescrita() -> Iterator[Session]:
        yield sessao_banco

    def _auth_service_sobrescrito() -> AuthService:
        return AuthService(
            usuarios=UsuarioRepository(sessao_banco),
            tokens=TokenRefreshRepository(sessao_banco),
            limite_login=LimiteTentativasLogin(cast("redis.Redis", redis_fake)),
            refresh_dias=7,
            redefinicao=TokenRedefinicaoRepository(sessao_banco),
            eventos=EventoService(
                notificacoes=NotificacaoRepository(sessao_banco),
                usuarios=UsuarioRepository(sessao_banco),
                outbox=OutboxRepository(sessao_banco),
                portal_url="http://localhost:8180",
            ),
            portal_url="http://localhost:8180",
        )

    def _usuario_service_sobrescrito() -> UsuarioService:
        return UsuarioService(usuarios=UsuarioRepository(sessao_banco))

    def _chamado_service_sobrescrito() -> ChamadoService:
        usuarios = UsuarioRepository(sessao_banco)
        return ChamadoService(
            chamados=ChamadoRepository(sessao_banco),
            categorias=CategoriaRepository(sessao_banco),
            usuarios=usuarios,
            eventos=EventoService(
                notificacoes=NotificacaoRepository(sessao_banco),
                usuarios=usuarios,
                outbox=OutboxRepository(sessao_banco),
                portal_url="http://localhost:8180",
            ),
            historico=HistoricoRepository(sessao_banco),
            sla=SlaRepository(sessao_banco),
        )

    storage_fake = StorageMemoria()

    def _anexo_service_sobrescrito() -> AnexoService:
        return AnexoService(
            anexos=AnexoRepository(sessao_banco),
            chamados=ChamadoRepository(sessao_banco),
            storage=storage_fake,
            max_bytes=10 * 1024 * 1024,
            max_por_chamado=5,
        )

    def _notificacao_service_sobrescrito() -> NotificacaoService:
        return NotificacaoService(notificacoes=NotificacaoRepository(sessao_banco))

    def _ciclo_vida_service_sobrescrito() -> CicloVidaService:
        usuarios = UsuarioRepository(sessao_banco)
        return CicloVidaService(
            chamados=ChamadoRepository(sessao_banco),
            categorias=CategoriaRepository(sessao_banco),
            usuarios=usuarios,
            historico=HistoricoRepository(sessao_banco),
            solucoes=SolucaoRepository(sessao_banco),
            followups=FollowUpRepository(sessao_banco),
            eventos=EventoService(
                notificacoes=NotificacaoRepository(sessao_banco),
                usuarios=usuarios,
                outbox=OutboxRepository(sessao_banco),
                portal_url="http://localhost:8180",
            ),
        )

    def _base_conhecimento_sobrescrito() -> BaseConhecimentoService:
        return BaseConhecimentoService(
            base=BaseConhecimentoRepository(sessao_banco),
            solucoes=SolucaoRepository(sessao_banco),
        )

    def _outbox_service_sobrescrito() -> OutboxService:
        return OutboxService(outbox=OutboxRepository(sessao_banco))

    def _perfil_service_sobrescrito() -> PerfilService:
        return PerfilService(
            usuarios=UsuarioRepository(sessao_banco),
            vinculo=VinculoWhatsApp(cast("redis.Redis", redis_fake)),
            numero_suporte="5515999999999",
        )

    def _bot_service_sobrescrito() -> BotService:
        cliente = cast("redis.Redis", redis_fake)
        usuarios = UsuarioRepository(sessao_banco)
        chamados = ChamadoRepository(sessao_banco)
        eventos = EventoService(
            notificacoes=NotificacaoRepository(sessao_banco),
            usuarios=usuarios,
            outbox=OutboxRepository(sessao_banco),
            portal_url="http://localhost:8180",
        )
        chamado_service = ChamadoService(
            chamados=chamados,
            categorias=CategoriaRepository(sessao_banco),
            usuarios=usuarios,
            eventos=eventos,
            historico=HistoricoRepository(sessao_banco),
            sla=SlaRepository(sessao_banco),
        )
        ciclo_vida = CicloVidaService(
            chamados=chamados,
            categorias=CategoriaRepository(sessao_banco),
            usuarios=usuarios,
            historico=HistoricoRepository(sessao_banco),
            solucoes=SolucaoRepository(sessao_banco),
            followups=FollowUpRepository(sessao_banco),
            eventos=eventos,
        )
        return BotService(
            usuarios=usuarios,
            chamados=chamados,
            chamado_service=chamado_service,
            ciclo_vida=ciclo_vida,
            vinculo=VinculoWhatsApp(cliente),
            estado=EstadoBot(cliente),
            portal_url="http://localhost:8180",
        )

    def _estado_bot_sobrescrito() -> EstadoBot:
        return EstadoBot(cast("redis.Redis", redis_fake))

    def _sla_service_sobrescrito() -> SlaService:
        return SlaService(sla=SlaRepository(sessao_banco))

    app.dependency_overrides[obter_sessao] = _sessao_sobrescrita
    app.dependency_overrides[obter_auth_service] = _auth_service_sobrescrito
    app.dependency_overrides[obter_usuario_service] = _usuario_service_sobrescrito
    app.dependency_overrides[obter_chamado_service] = _chamado_service_sobrescrito
    app.dependency_overrides[obter_anexo_service] = _anexo_service_sobrescrito
    app.dependency_overrides[obter_notificacao_service] = _notificacao_service_sobrescrito
    app.dependency_overrides[obter_ciclo_vida_service] = _ciclo_vida_service_sobrescrito
    app.dependency_overrides[obter_base_conhecimento_service] = _base_conhecimento_sobrescrito
    app.dependency_overrides[obter_outbox_service] = _outbox_service_sobrescrito
    app.dependency_overrides[obter_perfil_service] = _perfil_service_sobrescrito
    app.dependency_overrides[obter_bot_service] = _bot_service_sobrescrito
    app.dependency_overrides[obter_estado_bot] = _estado_bot_sobrescrito
    app.dependency_overrides[obter_sla_service] = _sla_service_sobrescrito
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def criar_usuario(
    sessao: Session,
    *,
    email: str,
    senha: str,
    nome: str = "Usuária de Teste",
    perfil: str = "CLIENTE",
    ativo: bool = True,
    cargo: str | None = None,
) -> int:
    """Insere um usuário de teste (senha com hash BCrypt custo 4) e devolve o id."""
    linha = sessao.execute(
        text(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo_perfil, cargo, ativo) "
            "VALUES (:nome, :email, :senha_hash, CAST(:perfil AS perfil_usuario), :cargo, :ativo) "
            "RETURNING id_usuario"
        ),
        {
            "nome": nome,
            "email": email.strip().lower(),
            "senha_hash": gerar_hash_senha(senha),
            "perfil": perfil,
            "cargo": cargo,
            "ativo": ativo,
        },
    )
    sessao.flush()
    return int(linha.scalar_one())
