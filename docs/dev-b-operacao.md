# Operação e handoff — Dev B

Escopo: Docker/baseline, CI, monitoramento e infraestrutura AWS (etapas 5, 6, 8 e
10). Trabalho sempre na **develop**. API/testes/README final/vídeo são do Dev A;
modelo, dataset, Airflow e ONNX são do Dev C. Fonte de requisitos:
`../.docs/content/tech-challenge.md`.

## Ambiente instalado

Python 3.11.16, Terraform 1.16.1 e actionlint 1.7.12 instalados via Homebrew.
`.venv` com dependências do projeto e constraints; `.env` configurado localmente
e ignorado pelo Git. Playwright/Chromium instalados apenas para captura do dashboard.

Reprodução em outra máquina:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -c constraints.txt -e '.[dev]'
.venv/bin/ruff check app/ src/ scripts/benchmark.py scripts/test_benchmark.py
.venv/bin/python -m pytest -v tests/ scripts/test_benchmark.py
docker compose up -d --build
```

O Compose também funciona sem `.env`; defaults são locais. Para S3, configurar
as variáveis do `.env.example` com a chave correta (`model.pkl`/`model.onnx`).
A constraint de ONNX preserva compatibilidade com o `skl2onnx` fixado no projeto.
Importações sklearn, skl2onnx e onnxruntime foram verificadas em ARM64 e AMD64.

## Stack local e evidências

| Serviço | URL |
|---|---|
| API/Swagger | http://localhost:8000/docs |
| Saúde do modelo | http://localhost:8000/health |
| Prometheus | http://localhost:9090/targets |
| Grafana | http://localhost:3000/d/triagem |

Grafana local: `admin` / `admin` (configurável por `GRAFANA_ADMIN_PASSWORD` na
primeira inicialização do volume). Portas publicadas somente em `127.0.0.1`.
Dados persistem nos volumes; retenção Prometheus de 14 dias. `docker compose stop`
para parar e `docker compose up -d` para retomar. `docker compose down` remove
containers/rede do projeto, preservando os volumes enquanto não se usar `-v`.

Quatro painéis: total de predições desde o início do processo, p95 de inferência,
erros de inferência/s e distribuição por classe. O contador de erros existente
não inclui falhas de validação 422; zero erros é um resultado válido, não dados
simulados. O histograma usa milissegundos. Após carga, aguardar dois scrapes
(aproximadamente 30 s) para `rate`; sem novas chamadas, o p95 pode ficar sem dados.

`grafana_dashboard_mock.png` é evidência visual de infraestrutura com chamadas
HTTP reais, **modelo mock**. A única classe exibida é `normal` por esse motivo.
Repetir a captura com modelo carregado antes do vídeo final:

```bash
.venv/bin/python scripts/benchmark.py --n 200
.venv/bin/pip install playwright
.venv/bin/playwright install chromium
.venv/bin/python scripts/capture_dashboard.py
```

## AWS preparada

Região `us-east-1`, prefixo exclusivo `tc03-triagem`. Recursos existentes de outros
projetos foram preservados. Valores da instalação:

| Item | Valor |
|---|---|
| ECR | `958268153605.dkr.ecr.us-east-1.amazonaws.com/tc03-triagem` |
| Imagem inicial AMD64 | `bootstrap-20260912` |
| Role GitHub | `arn:aws:iam::958268153605:role/tc03-github-ecr-develop` |
| Bucket state | `tc03-958268153605-tfstate` |
| Bucket modelos | `tc03-triagem-958268153605-models` |
| Bucket datasets | `tc03-triagem-958268153605-datasets` |
| Cluster | `tc03-triagem` |
| Task family inferência | `tc03-triagem-inference` |
| Task family treino | `tc03-triagem-training` |

O state de bootstrap usa `bootstrap/terraform.tfstate`; a infraestrutura usa
`triagem/terraform.tfstate` no mesmo bucket. Ambos com locking nativo S3,
versionamento e criptografia. `infra/backend.hcl` e `infra/terraform.tfvars` são
locais/ignorados; `.terraform.lock.hcl` deve ser versionado.

Rede: VPC dedicada, duas subnets públicas e duas privadas reservadas. Fargate
usa subnets públicas com IP público para acessar ECR/S3, sem NAT Gateway; entrada
na porta 8000 permitida apenas pelo security group do ALB. Inferência prevista:
1 task, 0,25 vCPU/512 MiB; treino: 1 vCPU/2 GiB apenas quando executado. Ajustar
memória caso o modelo real demonstre necessidade. Métricas ficam no stack local;
CloudWatch **Logs**, retenção 14 dias, serve só ao diagnóstico das tasks.

`enable_inference=false` enquanto falta um modelo compatível: ALB e Service não ficam ativos.
A definição de inferência exige `model=loaded` no healthcheck do ECS; um HTTP 200
em modo mock não é aceito como serviço saudável. O treino ainda depende do
contrato de ingestão/upload do Dev C. A imagem inicial foi publicada diretamente
no ECR para validar infraestrutura; isso não substitui a execução do GitHub Actions.

## Configuração e publicação no GitHub

1. Em Settings → Secrets and variables → Actions → **Variables**, criar:

| Variable | Valor |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `AWS_ROLE_ARN` | `arn:aws:iam::958268153605:role/tc03-github-ecr-develop` |
| `ECR_REPOSITORY` | `tc03-triagem` |

Não são necessárias access keys em Secrets: o workflow usa OIDC. A role tem
permissão para publicar somente nesse ECR e confia somente na `develop` deste
repositório, incluindo os formatos de subject com e sem IDs imutáveis.

Após autenticar a conta com `gh auth login --web`:

```bash
gh variable set AWS_REGION --body us-east-1 --repo Fiap-TechChallenge118/tech-challenge-phase-03
gh variable set AWS_ROLE_ARN --body arn:aws:iam::958268153605:role/tc03-github-ecr-develop --repo Fiap-TechChallenge118/tech-challenge-phase-03
gh variable set ECR_REPOSITORY --body tc03-triagem --repo Fiap-TechChallenge118/tech-challenge-phase-03
```

2. Revisar e fazer commit/push na `develop` com autoria de Matheus Santos:

```bash
git branch --show-current
git diff --check
git add .dockerignore .gitignore Dockerfile constraints.txt docker-compose.yml
git add .github/workflows/ci.yml infra monitoring
git add scripts/benchmark.py scripts/test_benchmark.py scripts/capture_dashboard.py
git add scripts/validate_model.py scripts/test_validate_model.py
git add docs/dev-b-operacao.md docs/latencia_baseline.md docs/benchmark_smoke_mock.json docs/grafana_dashboard_mock.png
git add docs/infra_validacao.md docs/aws_outputs.json
git add .docs/TODO/dev-b-matheus-santos.md
git diff --cached --stat
git commit -m "feat(infra): add Docker, monitoring, CI and AWS bootstrap"
git push origin develop
```

Arquivos de evidência adicionais devem ser revisados e incluídos se presentes.
O instalador `AWSCLIV2.pkg` foi preservado e passou a ser ignorado. Não incluir
`.env`, credenciais, `.terraform/`, planos, tfvars reais ou state no commit.

3. Actions validado em `develop`: run `34722395361` concluiu com `lint`, `test`,
`infra`, `build` e `publish` verdes. A imagem do commit foi publicada no ECR
com tag `720e9980f6696bf9d61212bb876ba7ae7c3d7675` e digest
`sha256:b4b54620b05b6acd2089ee0bb3cb75ac7748cbdb0ce0211b031b23ad62290f75`.
Em execuções futuras, o esperado é `lint`, `test`, `infra`, `build`, `publish`
verdes no push.
Em PR, publicação é pulada; sem `AWS_ROLE_ARN`, publicação também é pulada, mas
lint/test/build continuam. O build inclui smoke test HTTP e CLI de treino em mock.
O job `infra` valida formatação, módulos Terraform e Compose sem acessar o state
AWS. O build depende dos testes e da validação de infraestrutura.
O job `publish` importa o arquivo da imagem aprovada no smoke test e publica essa
mesma imagem, sem outro build. O artefato intermediário é retido por um dia;
se expirar antes de repetir um publish que falhou, usar **Re-run all jobs**.
Reruns não sobrescrevem a tag SHA já publicada. A publicação não aplica Terraform.
Salvar print da execução para o Dev A. Badge a inserir por ele no README:

```markdown
[![CI](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/workflows/ci.yml)
```

## Pendências para o Dev C

- Regenerar `models/model.pkl` com sklearn **1.4.2** e as dependências de
  `pyproject.toml` + `constraints.txt`. O arquivo recebido foi salvo com 1.9.0;
  `scripts/validate_model.py` detectou a diferença. Entregar também hash e
  versões do treino. O pipeline deve incluir o preprocessamento.
- Entregar ONNX e paridade após a etapa de otimização. Enquanto isso, `.pkl` é
  suficiente para baseline e primeiro deploy real.
- Definir ingestão de `DATA_BUCKET`/`DATA_KEY` para
  `/app/data/processed/train.csv`, executar treino e salvar/upload em
  `MODEL_BUCKET`/`models/model.pkl`. Essas variáveis estão na Task Definition,
  mas o script atual não as consome automaticamente.
- O container de treino chama `python -m src.train --data
  /app/data/processed/train.csv --model /app/models/model.pkl --classifier logistic`.
  O Dev C pode fornecer um wrapper como comando de `training_command`. Usar a
  mesma imagem publicada após incluir o código da DAG/wrapper que precisar ir no
  container (hoje o Dockerfile copia `app/` e `src/`).
- Na DAG usar `launch_type=FARGATE`, `assignPublicIp=ENABLED`, container `train` e
  os outputs `training_task_definition`, `public_subnet_ids`,
  `ecs_security_group_id`. A role da task já permite ler datasets e gravar em
  `processed/*` e `models/*`; a identidade que dispara a DAG ainda precisa de
  `ecs:RunTask`, `ecs:DescribeTasks` e `iam:PassRole` das roles retornadas.
- A tarefa de save da DAG precisa considerar que o filesystem da task Fargate
  termina junto com ela: o modelo deve sair para S3 antes desse encerramento.

Consultar os valores exatos: `terraform -chdir=infra output -json`.
Snapshot não secreto em `docs/aws_outputs.json`. A task de infraestrutura executou
`python -m src.train --help` no Fargate e terminou com código 0; ver
`docs/infra_validacao.md`. Isso não é uma execução de treino.

## Ativar o serviço após receber o modelo

Executar esta sequência somente após o validador aceitar o modelo:

```bash
.venv/bin/python scripts/validate_model.py models/model.pkl
# Prosseguir somente se a validação terminar com código 0.
aws s3 cp models/model.pkl s3://tc03-triagem-958268153605-models/models/model.pkl --region us-east-1
aws s3api head-object --bucket tc03-triagem-958268153605-models --key models/model.pkl --region us-east-1
terraform -chdir=infra init -backend-config=backend.hcl
```

Atualizar `infra/terraform.tfvars`: `enable_inference=true`, `use_onnx=false`,
`model_key="models/model.pkl"`, `image_uri` com o SHA publicado pelo Actions
(ou digest da imagem inicial verificada). Então:

```bash
terraform -chdir=infra plan -out=deploy.tfplan
terraform -chdir=infra apply deploy.tfplan
terraform -chdir=infra output -raw alb_url
```

Na URL retornada validar `/health` com `model=loaded`, `/docs` e `/predict`.
Executar `scripts/benchmark.py --n 100 --url http://DNS_DO_ALB/predict --output
docs/benchmark_aws_raw.json` e registrar os resultados. O ALB é HTTP para esta
demo; utilizar os textos públicos/sintéticos de teste.

Rollback: restaurar `image_uri` para digest anterior e, se necessário, uma chave
S3 versionada do modelo; fazer plan/apply. A API baixa o modelo apenas no startup.
Se apenas o objeto corrente no S3 mudou, reiniciar o Service com
`aws ecs update-service --cluster tc03-triagem --service tc03-triagem
--force-new-deployment --region us-east-1`. Não executar isso antes de o Service existir.

## Janela de duas semanas

Janela autorizada: 12 a **26/09/2026**. Tags `ExpiresOn` e retenção de logs/métricas
de 14 dias foram configuradas. **Tags não desligam recursos automaticamente.**
Ao fim da demo, definir `enable_inference=false` e executar plan/apply remove
Service/ALB, interrompendo o custo desses recursos sem apagar modelos/datasets.

Para remover a infraestrutura inteira, primeiro preservar os artefatos/evidências;
depois revisar `terraform -chdir=infra plan -destroy`. Buckets não são apagados
com conteúdo (`force_destroy=false`); a exclusão de objetos/versionamentos exige
uma decisão explícita. O bootstrap fica separado e o bucket de state possui
`prevent_destroy=true`. ECR e S3 podem manter pequenos custos de armazenamento
enquanto forem preservados.

## Bootstrap em outra conta (não repetir na conta atual)

Como o backend precisa existir antes de ser usado, a primeira aplicação deve
ocorrer com backend local. Em uma cópia nova, mover temporariamente
`infra/bootstrap/backend.tf` para `backend.tf.disabled`, executar init/plan/apply
do bootstrap e restaurar o nome do arquivo. Criar `infra/backend.hcl` com
`bucket="NOME_RETORNADO_PELO_BOOTSTRAP"` e migrar:

```bash
terraform -chdir=infra/bootstrap init -migrate-state -backend-config=../backend.hcl
terraform -chdir=infra init -backend-config=backend.hcl
```

A instalação atual já passou por essa migração; basta `init` com o bucket existente.
Se a outra conta já tiver um provider OIDC GitHub, importá-lo no bootstrap em vez
de tentar criar outro. A autenticação local observada nesta execução foi root;
ela não foi copiada para GitHub nem para os containers. CI e ECS usam roles próprias.

## Referências de implementação

- [Terraform: backend S3 e locking](https://developer.hashicorp.com/terraform/language/backend/s3).
- [AWS: rede Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html).
- [GitHub: OIDC com AWS e subject por branch](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws).
- [Docker: compartilhar imagem entre jobs](https://docs.docker.com/build/ci/github-actions/share-image-jobs/).

## Compatibilidade do modelo recebido

Em 12/09/2026, `models/model.pkl` chegou com SHA-256
`3516b921aa882c42a4f1ca7e334d72b9e3f51c1a34287ddcb510e7cf2e7157b1`.
A desserialização indicou treino em sklearn 1.9.0, diferente do runtime 1.4.2.
O arquivo foi preservado e não foi enviado ao S3. O Dockerfile adiciona
`/app/src` ao `PYTHONPATH` para resolver a referência `preprocess` do treino.

O Dev C deve recriar seu ambiente a partir das dependências do repositório e
refazer o treino, preservando o artefato anterior até concluir a validação.
Confirmar a versão antes de treinar:

```bash
.venv/bin/pip install -c constraints.txt -e '.[dev]'
.venv/bin/python -c 'import sklearn; print(sklearn.__version__)'
# Esperado: 1.4.2. Executar o treino do Dev C e depois:
.venv/bin/python scripts/validate_model.py models/model.pkl
```

A compatibilidade entre versões distintas de sklearn não é suportada para
modelos persistidos; ver a [documentação de persistência](https://scikit-learn.org/stable/model_persistence.html).
