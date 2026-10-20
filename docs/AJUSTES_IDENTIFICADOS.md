# Ajustes identificados

Defeitos, problemas e propostas encontrados usando o sistema ou revisando o código. Não descreve o
que já existe. Um item só muda o comportamento oficial depois de aprovado, implementado, testado e
validado pelo usuário.

## Estados

- `identificado`: observado, sem solução aprovada;
- `em_analise`: alternativas sendo avaliadas;
- `aprovado`: regra definida e autorizada;
- `em_implementacao`: em desenvolvimento;
- `validado`: implementado, testado e validado pelo usuário;
- `adiado` / `descartado`: com o motivo registrado.

## Resumo

| Id | Assunto | Módulo | Estado | Prioridade |
|---|---|---|---|---|
| AJ-001 | `obter_sessao` não fazia commit: nenhum endpoint de escrita persistia | backend/core | validado | alta |
| AJ-002 | `make test` apagava os dados de dev (ida e volta das migrations no banco `helpdesk`) | backend/testes | validado | alta |
| AJ-003 | `make test` lento (~8 min): boto3 conectava ao MinIO no startup a cada TestClient | backend/testes | validado | média |

## AJ-003 — `make test` ficou lento (isolar os testes pesados)

- **Data:** 2026-10-17
- **Origem:** uso (a suíte completa passou a levar ~8 min)
- **Estado:** `validado`
- **Prioridade:** média

### Cenário observado
`make test` subiu para ~8 min. A causa **real** (descoberta com `--durations`): ~10 s de **setup
por teste**. A cada `TestClient`, o `lifespan` da app tentava criar os buckets no MinIO e o boto3
ficava em timeout, porque o host `s3` não resolve fora da rede do Compose. Não era o upload de
10 MB nem a ida e volta das migrations (esses são rápidos).

### Comportamento esperado
O `make test` padrão roda em poucos segundos; os testes pesados rodam sob demanda.

### Solução (implementada)
- O `conftest` roda com `AMBIENTE=test`; o `lifespan` **pula** a criação de buckets nesse ambiente
  (a app nos testes não depende do MinIO — o storage é o fake em memória). `make test` caiu para
  **~8 s**.
- Marcador `lento` nos dois testes genuinamente mais pesados (upload de 10 MB, ida e volta das
  migrations), excluído do run padrão (`addopts -m 'not performance and not lento'`); alvos
  `make test-lento` e `make test-tudo` para rodá-los sob demanda.

## AJ-002 — Testes destruíam o banco de desenvolvimento

- **Data:** 2026-10-17
- **Origem:** uso (login do admin parou de funcionar após rodar os testes)
- **Estado:** `validado`
- **Prioridade:** alta

### Cenário observado
Depois de `make test`, o login do admin passava a devolver `401` e a tabela `usuarios` ficava
vazia (as 7 categorias voltavam e a sequência de ids não). Causa: `test_migrations_ida_e_volta`
e as fixtures de integração usavam `url_banco_host()`, que apontava para o **banco de dev**
(`helpdesk`). O teste de ida e volta faz `downgrade base → upgrade head`, dropando e recriando
todas as tabelas — o que apaga os usuários (as categorias voltam porque a migration 0001 as
reinsere). Fere o AGENTS.md §5 ("não apague dado para acomodar uma mudança").

### Comportamento esperado
Rodar os testes nunca deve afetar os dados de desenvolvimento.

### Proposta (implementada)
`url_banco_host()` passou a usar um **banco de teste dedicado** (`<POSTGRES_DB>_test`), criado sob
demanda no mesmo servidor/porta (`_garantir_banco`). Toda a suíte (ida e volta + integração) roda
nele; o banco `helpdesk` de dev fica intacto. Verificado: após `make test`, o admin continua no
banco de dev e o login com a senha do `.env` volta `200`. Em CI nada muda (o `POSTGRES_DB` já é
efêmero; o sufixo `_test` continua válido).

## AJ-001 — Dependência de sessão não commitava os writes

- **Data:** 2026-10-17
- **Origem:** validação ao vivo da F1.3 (fluxo de auth e cadastro pelo front)
- **Estado:** `validado`
- **Prioridade:** alta

### Cenário observado
Pela stack no ar: login funcionava, mas `POST /api/auth/refresh` falhava com
`NAO_AUTENTICADO` (o refresh token não era gravado); `POST /api/usuarios` devolvia `201`
mas o usuário não aparecia na lista; e o e-mail duplicado **não** era barrado (RN07). Causa:
`app/core/database.obter_sessao` só fazia `yield` e `close()`, sem `commit()`. Os `flush()`
dos services enviavam o SQL, mas a transação era desfeita ao fechar a sessão. Os testes de
integração não pegaram porque usam uma sessão transacional desfeita por `rollback` (e
afirmam dentro da mesma transação).

### Comportamento esperado
Requisição bem-sucedida persiste (commit); requisição com erro desfaz (rollback).

### Proposta (implementada)
`obter_sessao` passou a fazer `commit()` ao fim do `yield` e `rollback()` em exceção, sempre
com `close()` no `finally`. Regressão coberta por `tests/test_sessao.py` (commit no sucesso,
rollback no erro). Revalidado ao vivo: refresh renova o token, cadastro persiste e e-mail
duplicado retorna `409 EMAIL_DUPLICADO`.

<!-- Modelo de item:

## AJ-001 — Título

- **Data:** AAAA-MM-DD
- **Origem:** uso / revisão de código / Sprint Review
- **Estado:** `identificado`
- **Prioridade:** alta | média | baixa

### Cenário observado
### Comportamento esperado
### Proposta
-->
