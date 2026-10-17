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

    @property
    def em_producao(self) -> bool:
        return self.ambiente.lower() == "prod"

    @property
    def docs_habilitado(self) -> bool:
        # OpenAPI/Swagger ficam desligados em produção (seção 7.1).
        return not self.em_producao


@lru_cache
def obter_configuracao() -> Configuracao:
    """Configuração única por processo (cacheada)."""
    return Configuracao()
