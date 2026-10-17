# Backend (api, worker e, a partir da F0.3, migrate) — multi-stage com uv.
# Imagens fixadas (ARM64 conferido, docs/INSTRUCOES_AGENTES.md seção 6).

# ----- Estágio de dependências: resolve o ambiente com o uv -----
FROM ghcr.io/astral-sh/uv:0.13.1 AS uv

FROM python:3.13.16-slim AS build
COPY --from=uv /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Instala só as dependências primeiro (camada cacheável), sem o código-fonte.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ----- Estágio final: runtime enxuto e não-root -----
FROM python:3.13.16-slim AS runtime

# Usuário não-root (seção 10.4).
RUN groupadd --system app && useradd --system --gid app --home /app app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Ambiente virtual pronto do estágio de build e o código da aplicação.
COPY --from=build --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app ./app
COPY --chown=app:app pyproject.toml uv.lock ./

USER app

EXPOSE 8000

# Padrão: API. O worker sobrescreve o comando no compose (python -m app.worker).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
