# Contribuindo

Guia de contribuição para o projeto de triagem médica (classificação de urgência de laudos).

## Conventional Commits

Todo commit segue o formato:

```
tipo(escopo): descrição curta
```

Tipos aceitos:

| Tipo | Uso |
|------|-----|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `test` | Testes |
| `refactor` | Refatoração sem mudança de comportamento |
| `chore` | Tarefas de manutenção (deps, config, build) |
| `ci` | Pipeline de CI/CD |

Exemplos:

```
feat(api): add /predict and /health endpoints
test(api): add pytest suite and ruff lint config
feat(infra): add Terraform for ECS/Fargate, ALB, ECR, S3
```

## Branch strategy

- `main` é protegida — nenhum merge direto.
- Toda mudança nasce em uma branch de etapa: `etapa-N-descricao-curta`.
  - Exemplos: `etapa-0-fundacao-repo`, `etapa-3-api-fastapi`, `etapa-10-infra-terraform`.
- Criar as branches sempre a partir de `main` atualizada.

## Pull Requests

- Todo merge em `main` passa por Pull Request.
- O PR só é mergeado com o CI verde (lint + testes) — ver `.github/workflows/ci.yml`.
- Descreva no PR: o que muda, como foi testado e o que ficou pendente.

## Qualidade de código

- Lint: `ruff check app/ src/` deve retornar zero erros.
- Testes: `pytest -v` deve passar 100%.
- Rode ambos localmente antes de abrir o PR.

## Segurança

- Nunca commitar segredos: `.env`, chaves AWS, `*.tfstate`.
- Artefatos de modelo (`*.pkl`, `*.onnx`) e dados brutos não são versionados (ver `.gitignore`).
