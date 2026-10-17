<!--
Fluxo do Documento 02 (seção 12.4): feature/* -> PR para develop -> PR para main.
Preencha as seções abaixo. Remova o que não se aplicar ao recorte.
-->

## Resumo das mudanças

<!-- O que muda e por quê, em uma ou duas frases. Cite o recorte (ex.: F0.4). -->

## Requisitos e códigos atendidos

<!-- Liste os códigos dos Documentos 01 a 03 tocados: RF, RNF, RN, UC, UJ, FA, FE, TU. -->

- 

## O que foi testado

<!-- Como validou: make lint, make test (com cobertura), ida e volta de migration,
     telas no protótipo, etc. Cole os resultados relevantes. -->

- 

## Checklist

- [ ] `make lint` passou (ruff check, ruff format --check, mypy strict)
- [ ] `make test` passou (pytest com cobertura)
- [ ] Migration, quando há: ida e volta (`upgrade head -> downgrade base -> upgrade head`)
- [ ] `docker compose config` ok e nenhuma porta fora de `127.0.0.1`
- [ ] Sem dado pessoal real em código, testes, logs, documentação ou commits
- [ ] Documentação do recorte atualizada (DEVELOPMENT_STATUS, ROADMAP, RASTREABILIDADE e o que couber)
- [ ] Prints das telas, quando há mudança visual
