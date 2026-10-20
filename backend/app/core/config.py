"""Configuração da aplicação (pydantic-settings).

Lê as variáveis do ambiente (e do `.env` em desenvolvimento). Só os campos usados
até a F0.2 são declarados; os demais entram quando a fase correspondente precisar.
Campos extras no `.env` são ignorados (`extra="ignore"`).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ===== Geral =====
    ambiente: str = "dev"
    log_level: str = "INFO"
    tz: str = "America/Sao_Paulo"
    portal_url: str = "http://localhost:8180"

    # ===== PostgreSQL =====
    database_url: str = "postgresql+psycopg://helpdesk:troque-me@db:5432/helpdesk"

    # ===== Redis =====
    redis_url: str = "redis://redis:6379/0"
    redis_prefixo: str = "mentory:"

    # ===== Autenticação (seção 10.2, 11) =====
    # JWT_SECRET deve ter 32 bytes ou mais em produção (validado em segurança.py).
    jwt_secret: str = "troque-me-com-openssl-rand-hex-32-apenas-para-dev"
    jwt_access_minutos: int = 30
    jwt_refresh_dias: int = 7
    bcrypt_custo: int = 12
    # Origens liberadas no CORS (só em dev; em produção front e API têm a mesma origem).
    cors_origins: str = "http://localhost:5173"

    # ===== Primeiro administrador (make criar-admin, seção 5.7) =====
    admin_nome: str = "Administrador"
    admin_email: str = "admin@empresa.com.br"
    admin_senha: str = "troque-me-agora"

    # ===== Config pública (GET /api/config/publica, seção 7.2) =====
    # Número só com dígitos (DDI+DDD); vazio desliga o atalho de WhatsApp na tela de login.
    whatsapp_numero_suporte: str = ""
    email_suporte: str = ""
    google_client_id: str = ""

    # ===== S3 (MinIO) — anexos (seção 5.6) =====
    s3_endpoint_url: str = "http://s3:9000"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_regiao: str = "us-east-1"
    s3_bucket_anexos: str = "mentory-anexos"
    s3_bucket_backups: str = "mentory-backups"

    # ===== Anexos (seção 13, decisões B9/B10) =====
    anexos_max_mb: int = 10
    anexos_max_por_chamado: int = 5

    # ===== Canais externos (seção 9, F6) =====
    # Quando false (padrão), o EventoService ainda grava o outbox, mas o worker
    # não despacha ao n8n: os eventos ficam PENDENTE até ligar a integração.
    outbox_habilitado: bool = False
    # URL do webhook do n8n que recebe os eventos de notificação (F6.2).
    n8n_webhook_notificacoes_url: str = ""
    # Token que o worker envia ao n8n (header X-Mentory-Token).
    n8n_webhook_token: str = ""
    # Chave que o n8n envia à API (header X-Integracao-Chave).
    integracao_api_key: str = ""

    @property
    def em_producao(self) -> bool:
        return self.ambiente.lower() == "prod"

    @property
    def docs_habilitado(self) -> bool:
        # OpenAPI/Swagger ficam desligados em produção (seção 7.1).
        return not self.em_producao

    @property
    def lista_cors_origins(self) -> list[str]:
        """CORS_ORIGINS como lista (separada por vírgula)."""
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]

    @property
    def google_sso(self) -> bool:
        """Login com Google disponível apenas quando há client id configurado (Fase 7)."""
        return bool(self.google_client_id.strip())

    @property
    def anexos_max_bytes(self) -> int:
        """Tamanho máximo de um anexo em bytes (decisão B9)."""
        return self.anexos_max_mb * 1024 * 1024

    @property
    def versao(self) -> str:
        """Versão da aplicação (fonte única em app.__version__)."""
        from app import __version__

        return __version__


@lru_cache
def obter_configuracao() -> Configuracao:
    """Configuração única por processo (cacheada)."""
    return Configuracao()
