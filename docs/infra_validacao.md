# Evidências técnicas — Dev B — 12/09/2026

## Validação executada

| Verificação | Resultado |
|---|---|
| Testes existentes (Dev A) | 10 passaram |
| Testes do benchmark (Dev B) | 3 passaram: percentis, recusa mock, erro HTTP |
| Ruff | Sem erros no código validado |
| actionlint | Workflow válido; execução GitHub pendente de autenticação/publicação |
| Docker ARM64 e AMD64 | Build concluído e imports ML/CLI verificados |
| Usuário runtime | `uid=10001(triagem) gid=10001(triagem)` |
| Diretório de treino | `/app/data/processed` gravável pelo usuário runtime |
| API local | `/health`: `status=ok, model=loaded`; `/predict` real responde |
| Compose | API saudável, Prometheus e Grafana ativos |
| promtool | Configuração válida |
| Target Prometheus | `http://api:8000/metrics`, `health=up`, sem erro |
| Grafana | Provisioning confirmado; 4 painéis; captura visual inspecionada |
| Carga local | 500 chamadas reais + 20 warmup; p50 1,697 ms, p95 2,164 ms, p99 2,570 ms |
| Bootstrap Terraform | 10 recursos criados; state migrado para S3 |
| Infra base Terraform | 35 recursos criados, sem alterações em projetos anteriores |
| Plan após apply | Sem diferenças no bootstrap e na infra base |
| Imagem ECR | Tag `bootstrap-20260912`, digest registrado em `latencia_baseline.md` |
| Smoke real no Fargate | Task terminou com exit code 0 |
| Smoke HTTP AMD64 local | `/health` e `/predict` responderam em mock; UID 10001 |
| Terraform em diretórios limpos | Bootstrap e infra: init sem backend e validate passaram com lockfile readonly |
| GitHub Actions | Run `34722395361`: lint, test, infra, build e publish verdes |
| Imagem publicada pelo CI | Tag `720e9980f6696bf9d61212bb876ba7ae7c3d7675`, digest `sha256:b4b54620b05b6acd2089ee0bb3cb75ac7748cbdb0ce0211b031b23ad62290f75` |
| Modelo S3 | `models/model.pkl`, 10.870.500 bytes, versão `ey17zfSRXWBRwlFQ.xILZjxl2YSt68EU` |

Revisão adicional do CI: `publish` usa o artefato exportado pelo job `build`,
garantindo que a imagem publicada é a que foi testada. O novo job `infra` valida
Terraform/Compose antes do build, sem aplicar recursos ou acessar o state remoto.

## Smoke Fargate

- Cluster: `tc03-triagem`.
- Task Definition: `tc03-triagem-training:1`.
- Task: `arn:aws:ecs:us-east-1:958268153605:task/tc03-triagem/02ecccab2ce840ceaa8a53bc340331ed`.
- Override: `python -m src.train --help` no container `train`.
- Resultado: `STOPPED`, `Essential container in task exited`, **exitCode=0**.
- Log: `/ecs/tc03-triagem`, stream `ecs/train/02ecccab2ce840ceaa8a53bc340331ed`.

Esse teste comprova execução da imagem AMD64 no Fargate, download ECR, uso das
roles, rede e entrada da CLI. **Não executou treinamento nem produziu modelo.**
A task terminou; não é um serviço persistente.

## O que ainda não foi validado

Paridade ONNX, treino/DAG com S3, execução remota do workflow, ALB/Service
ativo e benchmark da URL pública. O `model.pkl` recebido foi salvo com sklearn
1.9.0, agora alinhado ao runtime do projeto. Não há `model.onnx` neste checkout.
Essas pendências estão detalhadas em `dev-b-operacao.md`.

O Dockerfile inclui `/app/src` no `PYTHONPATH`, pois o treino serializa funções
do módulo `preprocess`. Com sklearn 1.9.0 alinhado, o artefato foi carregado e
validado no container sem warning de incompatibilidade.

O print `grafana_dashboard_mock.png` documenta o smoke inicial com fallback; a
captura final com o modelo carregado está em `grafana_dashboard.png`.
Os outputs de infraestrutura não secretos estão em `aws_outputs.json`; consultar
`terraform -chdir=infra output -json` novamente após alterações.
