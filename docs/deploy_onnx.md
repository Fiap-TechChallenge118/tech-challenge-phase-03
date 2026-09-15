# Deploy ONNX — 14/09/2026 (America/Sao_Paulo)

## Versão publicada

- Código: `d447ec1c75cc343c76658031c06e2a9b9858a8fc` (`develop`).
- [CI aprovado](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/runs/34908089669): lint, test, infra, build e publish.
- Imagem ECR: `958268153605.dkr.ecr.us-east-1.amazonaws.com/tc03-triagem@sha256:ce4e5e98d8a3ec1cbb98208f19ab24dc74b1e6bd03e4338471a4f1fd463f1b7e`.
- Modelo: `s3://tc03-triagem-958268153605-models/models/releases/d447ec1/model.onnx`.
- Versão S3: `fVEvhHaXALPWr9wRBnGhH0H1AYGExtWw`.
- SHA-256 do ONNX: `e29c8425739c45dbadb78dcc3f3099f01bb2401809e8eebb5cad9a83616477cd`.
- Tamanho: 8.742.267 bytes.
- Task Definition de inferência: `tc03-triagem-inference:3`; treino: `tc03-triagem-training:3`.
- Task de inferência validada: `db4555846a9c4b5c85f3ec592aacb104`.
- [Swagger público](http://tc03-triagem-1006816505.us-east-1.elb.amazonaws.com/docs).

## Origem e validação do modelo

O S3 e o checkout continham somente o `.pkl` antigo. A conversão desse arquivo
apresentou 14 divergências em 2.888 amostras; não foi publicada. O modelo foi
retreinado com `src/train.py` da develop, classificador logistic, seed 42,
split 0,2 e dados oficiais baixados por `scripts/download_data.py`.
A busca escolheu `C=0.3`, `class_weight=balanced`, reproduzindo as métricas
versionadas em `models/metrics.json`.

| Verificação | Resultado |
|---|---|
| Holdout: acurácia / macro-F1 | 0,6083795 / 0,6110232 |
| Paridade ONNX vs sklearn no holdout | 2.888/2.888 classes; zero divergências |
| Maior diferença absoluta de probabilidade | 2,6545 × 10⁻⁷ |
| Terraform apply | Concluído; novas revisões de tarefas e atualização do Service |
| Terraform plan após deploy | Sem diferenças |
| ECS | Rollout COMPLETED, running=1, pending=0 |
| CloudWatch Logs | Download da chave desta versão e “Modelo ONNX carregado” |
| HTTP público | `/health` loaded, `/docs` 200, `/metrics` 200 |
| Predições públicas | Cinco textos sintéticos; classe e confiança equivalentes ao sklearn |

O build/smoke da imagem ocorreu no CI. O runtime com o modelo real foi
validado diretamente no Fargate; o download local da imagem foi interrompido
por demora de conexão.

## Latência pública

100 chamadas, após 20 de aquecimento; conexão HTTP persistente do macOS até o ALB.
Dados brutos: [benchmark_aws_onnx.json](benchmark_aws_onnx.json).

| p50 | p95 | p99 | Throughput |
|---:|---:|---:|---:|
| 134,486 ms | 197,117 ms | 200,064 ms | 7,199 req/s |

Essa medição inclui rede e foi feita em outra data que o baseline AWS; não
isola o ganho do runtime. O comparativo controlado na mesma máquina consta
em [latencia_comparativo.md](latencia_comparativo.md).

## Rollback e encerramento

Para rollback, restaurar em `infra/terraform.tfvars` a imagem anterior
`958268153605.dkr.ecr.us-east-1.amazonaws.com/tc03-triagem@sha256:16852254240f87721be5e2510700b16899342758e24fc690550b3ab9efa62b31`,
`model_key="models/model.pkl"` e `use_onnx=false`; revisar plan e aplicar.
O `.pkl` anterior permanece no S3. O Service tem circuit breaker com rollback.

Janela autorizada até 26/09/2026. Encerrar com `enable_inference=false` e
plan/apply; tags não desligam recursos. Buckets e ECR permanecem armazenados.
