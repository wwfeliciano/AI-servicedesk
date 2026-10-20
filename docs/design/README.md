# Design — Mentory Help Desk

**Identidade aprovada (17/10/2026):** herdada do esboço do usuário ("01 — Foundations", ex-HelpFlow).
Marca teal (Brand 600 `#066873` / Brand 500 `#087F8C`), tipografia **IBM Plex Sans**, sidebar
branca, tema **claro e escuro**. Tokens oficiais na **seção 8.2** do prompt; decisão em
`../DECISOES.md` (ADR 2026-10-17 — Identidade visual herdada do esboço).

- [`mentory/index.html`](mentory/index.html) — **protótipo de referência** do Mentory (Login +
  Dashboard, claro/escuro). Abra no navegador. O assistente de IA/RAG aparece como visão de
  produto, marcado "em breve" (implementação em fase futura; núcleo de chamados primeiro).
- [`exploracao/`](exploracao/) — material de apoio: o esboço original do usuário
  (`helpflow/`, `Screenshot ... .png` com as Foundations) e três direções que foram **descartadas**
  (`exploracao/index.html`) por terem "cara de IA".

A implementação (Vite + React + Tailwind 4 com estes tokens) é a **F0.5**.
