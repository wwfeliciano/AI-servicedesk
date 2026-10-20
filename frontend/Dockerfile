# Front-end (container "web"): build com Node, servido por Nginx. ARM64 conferido.

# ----- Build da SPA -----
FROM node:22.11.0-alpine AS build
WORKDIR /app

# Instala dependências primeiro (camada cacheável).
COPY package.json package-lock.json* ./
RUN npm ci

# Código e build de produção (tsc -b && vite build → /app/dist).
COPY . .
RUN npm run build

# ----- Runtime: Nginx (imagem unprivileged, roda como não-root na 8080) -----
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
