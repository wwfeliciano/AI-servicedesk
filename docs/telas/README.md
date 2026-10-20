# Documentação funcional das telas

O que cada tela faz e **por que faz assim**. Descreve só o que existe; o planejado fica no
[ROADMAP](../ROADMAP.md) e na seção 8.4 do [prompt](../PROMPT_IMPLEMENTACAO.md).

## Como está organizado

| Arquivo | Cobre |
|---|---|
| [01-acesso.md](01-acesso.md) | Login, Perfil e Administração de usuários (F1.3) |
| [02-chamados.md](02-chamados.md) | Dashboard, Novo Chamado, Meus Chamados, Detalhe e anexos (F2.4, F3.3) |
| [03-notificacoes.md](03-notificacoes.md) | Tela de Notificações e contador no menu (F3.3) |
| [HISTORICO.md](HISTORICO.md) | Mudanças de comportamento, com o commit de cada uma |

Um arquivo por grupo de telas entra quando a primeira tela do grupo for entregue (por exemplo,
`01-acesso.md` na F1 e `02-chamados.md` na F2).

## Como manter atualizado

Ao concluir um recorte que muda o que uma tela faz:

1. atualize o arquivo da tela com o comportamento e o motivo;
2. acrescente uma entrada no topo do [HISTORICO.md](HISTORICO.md) com data, recorte, telas
   afetadas, o que mudou para quem usa e o commit.
