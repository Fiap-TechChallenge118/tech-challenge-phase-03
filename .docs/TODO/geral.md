# TODO — Geral do Time

Revisado em 15/09/2026 contra [os requisitos oficiais](../content/tech-challenge.md).
Evidências e limites: [auditoria de entrega](../../docs/status-entrega.md).
`[x]` indica entrega com evidência; `[ ]` indica pendência ou confirmação ausente.
Histórico dos checklists anteriores permanece no Git.

## Entregáveis oficiais

- [x] API FastAPI `/predict`, `/health`, `/metrics`, schemas e testes.
- [x] Dockerfile funcional, usuário não-root e baseline local documentado.
- [x] Decisão arquitetural no README: real-time em ECS/Fargate + ALB.
- [x] GitHub Actions: lint, test, infra, build e publish verdes na `develop`.
- [x] DAG local `ingest >> train >> save`, Compose Airflow e captura das três tasks verdes.
- [x] Stack local API + Prometheus + Grafana; quatro painéis, JSON e print.
- [x] Classificador treinado; TF-IDF + LogisticRegression; métricas documentadas.
- [x] ONNX exportado e validado em 2.888 amostras sem divergências.
- [x] Comparativo de latência sklearn/ONNX nas mesmas condições registrado.
- [x] ONNX publicado no S3 e servido pelo ECS; [deploy e validação](../../docs/deploy_onnx.md).
- [x] README revisado para refletir a implementação e as métricas atuais.
- [ ] Vídeo STAR ≤5 min publicado, acessível sem login e linkado no README.
- [ ] Reprodução final dos comandos a partir de clone limpo.

## Decisões confirmadas

- [x] Inferência AWS: Service ECS/Fargate atrás de ALB; modelo baixado do S3 no startup.
- [x] Imagem única de inferência/CLI de treino no ECR; release por digest.
- [x] Retreino entregue: Airflow **local** via `docker-compose.airflow.yml`.
- [x] Modelo prevê cinco condições; API aplica mapeamento para três urgências.
- [x] Contrato da inferência: `MODEL_BUCKET`, `MODEL_KEY`, `MODEL_PATH`, `USE_ONNX`, `AWS_REGION`.
- [x] State remoto S3 com versionamento e locking; bootstrap separado.
- [x] Prometheus/Grafana locais para métricas; CloudWatch Logs para diagnóstico ECS.
- [x] Janela AWS autorizada até 26/09/2026; encerramento por `enable_inference=false` + plan/apply.

## Metas internas ainda abertas

- [ ] Integrar a DAG com ECS RunTask e download/upload S3; não é requisito obrigatório do enunciado.
- [ ] Definir contrato de promoção automática do ONNX após retreino; a DAG atual salva somente `.pkl` local.
- [x] Notebook EDA executado: 16 células, outputs salvos e quatro gráficos renovados.
- [ ] Confirmar branch de submissão e proteção/acessos correspondentes.
- [ ] Confirmar responsável pelo encerramento AWS e executar ao fim da janela.

## Checkpoints e etapas

| Etapa interna | Responsável | Estado auditado |
|---|---|---|
| 0 — Fundação | Dev A | Estrutura/repositório público entregues; proteção atual não revalidada |
| 1 — EDA | Dev C | Notebook executado, outputs salvos e gráficos renovados |
| 2 — Modelo | Dev C | Entregue; retreino reproduzido nesta revisão |
| 3 — API | Dev A | Entregue; runtime ONNX integrado |
| 4 — Testes | Dev A | Entregue; 17 testes incluindo scripts de validação |
| 5 — Docker/baseline | Dev B | Entregue |
| 6 — CI/CD | Dev B | Entregue na develop |
| 7 — Airflow | Dev C | Nova execução local comprovada; extensão ECS/S3 pendente |
| 8 — Monitoramento | Dev B | Entregue; stack existente revalidada |
| 9 — ONNX | Dev C | Entregue; paridade completa e deploy validados |
| 10 — AWS | Dev B | Entregue; ONNX em produção |
| 11 — README/vídeo | Dev A | Documentação revisada; vídeo e reprodução final pendentes |

## Submissão

- [x] Repositório público verificado via GitHub.
- [x] Commits semânticos e CI verde na branch de trabalho `develop`.
- [x] Busca limitada por nomes de arquivos sensíveis no histórico sem resultados (`*.env`, `*.key`, `*.tfstate*`).
- [ ] Revisar proteção da branch final e realizar revisão de segredos completa.
- [ ] Consolidar branch/link de entrega: padrão remoto é `master`, não `main`; `develop` estava 29 commits à frente em `d447ec1`.
- [ ] Se integrar em `master`, ajustar CI/checks para essa branch antes do merge.
- [ ] Validar links e comandos em clone limpo; comprovar modelo carregado, não apenas HTTP 200 em mock.
- [ ] Confirmar data limite e canal de submissão com a instituição.
- [ ] Inserir link público do vídeo e verificar duração/método STAR.
- [ ] Submeter repositório e vídeo no portal e registrar recebimento.

Detalhes por responsável: [Dev A](dev-a-alexandre.md),
[Dev B](dev-b-matheus-santos.md), [Dev C](dev-c-matheus-ferreira.md).
