# TODO — Dev B: Matheus Santos

Revisão de 14/09/2026. Infraestrutura, CI/CD, observabilidade e AWS.
Branch de trabalho: `develop`. Janela AWS: até 26/09/2026.
Fonte: [requisitos oficiais](../content/tech-challenge.md).
[Operação](../../docs/dev-b-operacao.md) · [deploy ONNX](../../docs/deploy_onnx.md)
· [auditoria](../../docs/status-entrega.md).

## ETAPA 5 — Docker e baseline

- [x] Dockerfile multi-stage Python 3.11, API + CLI de treino, usuário UID 10001.
- [x] HEALTHCHECK, porta 8000, Uvicorn, `.dockerignore`.
- [x] Dependências fixadas e locale necessário ao ONNX na imagem.
- [x] Builds ARM64/AMD64 e smoke documentados; release atual construída/testada pelo CI em AMD64.
- [x] API com modelo real em container validada, incluindo release atual no Fargate.
- [x] Benchmark parametrizado com aquecimento, p50/p95/p99, throughput e JSON bruto.
- [x] Benchmark rejeita mock; baseline real em `docs/latencia_baseline.md`.

## ETAPA 6 — CI/CD

- [x] Push/PR em `develop` e execução manual.
- [x] Lint, testes, Terraform/Compose e build; smoke da imagem antes da publicação.
- [x] ECR com OIDC, tag SHA e publicação da mesma imagem aprovada no smoke.
- [x] Variables AWS configuradas; sem access keys no workflow.
- [x] Release `d447ec1`: cinco jobs verdes no [run 34908089669](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/runs/34908089669).
- [x] Badge, link Actions e captura histórica no README/docs.
- [ ] Se o time escolher `master` para submissão, configurar gatilhos/checks dessa branch antes de integrar.

## ETAPA 8 — Monitoramento

- [x] Counter de requisições/classes, Histogram de inferência e Counter de erros.
- [x] Prometheus com scrape de 15 segundos em `api:8000/metrics`.
- [x] Docker Compose API + Prometheus + Grafana, rede e volumes de dados.
- [x] Datasource/dashboard provisionados; quatro painéis (≥3 exigidos).
- [x] `monitoring/dashboard.json` e print real `docs/grafana_dashboard.png`.
- [x] Stack existente revalidada: API saudável, target UP e Grafana database OK.
- [ ] Reprodução de clone limpo com o ONNX atual, em conjunto com a revisão final do time.

## ETAPA 10 — Terraform/AWS

- [x] Rede dedicada, S3, ECR, IAM, ECS, ALB e CloudWatch Logs.
- [x] State remoto S3 com versionamento, criptografia e locking; bootstrap separado.
- [x] Inferência Fargate 0,25 vCPU/512 MiB, modelo baixado no startup.
- [x] Task Definition de treino com imagem/roles/rede; CLI `--help` validada historicamente.
- [x] Defaults e exemplos alinhados a ONNX; `.tfvars`/backend/state fora do Git.
- [x] ONNX retreinado/reproduzido, paridade 2.888/2.888 e upload S3 versionado.
- [x] Deploy em `tc03-triagem-inference:3` concluído; running=1, pending=0, rollout COMPLETED.
- [x] `/health` loaded, `/docs` e `/metrics` 200, predições públicas equivalentes ao sklearn.
- [x] Terraform plan após apply sem diferenças.
- [x] Benchmark AWS ONNX: 100 chamadas; p95 197,117 ms incluindo rede.
- [x] Digest, chave/versão S3, evidências e rollback em `docs/deploy_onnx.md`.
- [x] README e outputs atualizados para a implantação real.

## Dependências e operação final

- [x] ONNX/paridade entregues; migração da inferência concluída.
- [ ] Dev C: extensão da DAG para ECS/S3 e promoção do ONNX após treino (meta interna adicional).
- [ ] Dev A/time: vídeo, clone limpo, branch final e submissão.
- [x] Procedimento de encerramento documentado: `enable_inference=false`, plan/apply; preserva buckets/ECR.
- [ ] Definir responsável nominal e executar encerramento após a demo, até 26/09/2026.

Tags de expiração não desligam recursos. A DAG local já atende ao requisito
oficial de pipeline simples; não declarar treino ECS/S3 end-to-end concluído.
