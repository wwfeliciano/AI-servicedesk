# 01 — Acesso (Login, Perfil, Administração de usuários)

Telas da F1.3, na identidade do esboço (marca teal, IBM Plex Sans, tema claro/escuro). Descreve o
comportamento atual; o planejado fica na seção 8.4 do prompt.

## Login (`/login`)

- Painel esquerdo na cor da marca (oculto no celular) com a proposta e três destaques; formulário
  "Bem-vindo de volta" à direita.
- Validação no cliente (React Hook Form + Zod): e-mail e senha obrigatórios, formato de e-mail.
- Envio chama `POST /api/auth/login`. Em sucesso, grava o access token **em memória** e vai para o
  destino (ou `/dashboard`). O refresh token fica no cookie HttpOnly do servidor.
- **FE01:** credenciais inválidas mostram a mensagem genérica do backend ("E-mail ou senha
  inválidos."), sem dizer qual campo errou; o e-mail digitado permanece. Excesso de tentativas
  mostra o aviso de `429` ("Muitas tentativas…").
- "Entrar com Google Workspace" só aparece quando `/api/config/publica` retorna `google_sso: true`
  (Fase 7). "Contate o TI" abre `wa.me`/`mailto` conforme os canais da config pública.
- Por que assim: o token em memória reduz risco de XSS; a restauração de sessão usa o cookie.

## Restauração de sessão e proteção de rotas

- Ao abrir o app, tenta `POST /api/auth/refresh` pelo cookie: se houver sessão, entra autenticado;
  senão, anônimo. Enquanto verifica, as rotas protegidas mostram um carregamento (não piscam o
  `/login`).
- `RequirePerfil` manda anônimo para `/login` (guardando a origem) e barra perfil sem permissão
  (volta ao Dashboard). `/admin/usuarios` exige **ADMIN**.
- Em `401` numa chamada autenticada, o cliente tenta um refresh automático e repete a requisição;
  se falhar, encerra a sessão. O botão **Sair** (topo) faz logout e volta ao Login.

## Perfil (`/perfil`)

- Mostra nome, e-mail, perfil e cargo do usuário autenticado.
- Troca de senha (`PUT /api/auth/senha`): senha atual, nova (≥ 8) e confirmação. Senha atual
  incorreta vira erro no campo; sucesso dá toast e limpa o formulário. Trocar a senha encerra as
  outras sessões (regra do backend).

## Administração de usuários (`/admin/usuarios`, só ADMIN)

- Lista paginada (`GET /api/usuarios`) com busca por nome/e-mail e filtro por perfil; mostra nome,
  e-mail, perfil, situação (Ativo/Inativo) e data de cadastro, com paginação de 10.
- "Novo usuário" abre um modal (`POST /api/usuarios`): nome, e-mail, senha, perfil e cargo
  (opcional). **E-mail duplicado** (RN07) e **senha fraca** aparecem como erro no campo
  correspondente; sucesso dá toast e atualiza a lista.
- Estados de carregando, vazio e erro (com "Tentar novamente").
