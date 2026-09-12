# Baseline de latência — Etapa 5

## Situação em 12/09/2026

Container e ferramenta de medição validados. **Baseline do modelo pendente:** o
`models/model.pkl` recebido em 12/09 foi treinado com sklearn 1.9.0; o runtime
fixado no projeto usa 1.4.2. O Dev C precisa regenerá-lo nesse ambiente.
SHA-256 recebido: `3516b921aa882c42a4f1ca7e334d72b9e3f51c1a34287ddcb510e7cf2e7157b1`.
O arquivo foi preservado, permanece fora do Git e não foi publicado no S3.
O baseline será do `.pkl`, comparado com ONNX pelo Dev C na Etapa 9.

| Medida do modelo real | Resultado |
|---|---|
| p50 / p95 / p99 HTTP | Pendente de artefato compatível |
| Throughput sequencial | Pendente de artefato compatível |
| Latência na AWS | Pendente de modelo e ativação do serviço |

Não usar `benchmark_smoke_mock.json` como resultado de otimização: ele contém
200 chamadas de infraestrutura com o fallback mock e 20 chamadas de aquecimento.
Serve apenas para validar transporte HTTP, métricas e funcionamento do script.

## Ambiente e imagem

- Máquina: macOS 15.6.1, ARM64, 8 CPUs lógicas, 16 GiB RAM.
- Docker Engine 29.7.2; Compose 5.5.1; aplicação em Python 3.11.
- Docker Desktop: 8 CPUs e 8.319.770.624 bytes de RAM disponíveis ao engine.
- Imagem ARM64 usada no smoke inicial: tamanho reportado pelo engine
  **238.422.257 bytes**, ID
  `sha256:4e560beb4531d58798bc677efe3469ed65a1d73ea357449951056bf10906c66b`.
- Imagem AWS AMD64: tamanho comprimido reportado pelo ECR **243.483.489 bytes**,
  digest `sha256:19019b7c11b0a32194dce87af88fe8c1145b7ff28c307c9d26521f18f3c0029a`.
- Imagens sem modelo embutido; usuário `triagem`, UID/GID 10001.
- Revalidar estes números se o Dockerfile/dependências forem reconstruídos.

## Executar com o modelo do Dev C

Na raiz do projeto, colocar o artefato confiável em `models/model.pkl` e executar:

```bash
.venv/bin/python scripts/validate_model.py models/model.pkl
docker compose up -d --build
curl -fsS http://localhost:8000/health
shasum -a 256 models/model.pkl
.venv/bin/python scripts/benchmark.py --n 500 --output docs/benchmark_raw.json
```

Executar os passos seguintes somente se a validação do modelo passar.
`/health` deve mostrar `model: loaded`. O script recusa mock por padrão, aborta
em erro HTTP/resposta inválida e só grava o relatório após todas as requisições
terem sucesso. `--allow-mock` existe apenas para o smoke test da infraestrutura.

A medição usa 20 requisições de aquecimento, conexão HTTP persistente, 500
requisições sequenciais com três textos fixos e timeout de 10 segundos. O JSON
registra horário UTC, máquina, textos, respostas, tempos individuais e resumo.
Percentis usam interpolação linear; throughput = N / tempo total da medição.
Não é ensaio de carga concorrente nem avaliação clínica do classificador.

O p95 do Grafana é uma estimativa do histograma de **inferência** em ms. O
benchmark mede HTTP completo (transporte + API + inferência); são medidas diferentes.
Guardar o hash do artefato, a imagem e a alocação CPU/RAM do Docker Desktop junto
do baseline final. Medir sklearn e ONNX na mesma arquitetura e configuração.

## Repetir com ONNX — responsabilidade do Dev C

Após disponibilização e validação de paridade do artefato:

```bash
USE_ONNX=true MODEL_FILE=model.onnx docker compose up -d api
.venv/bin/python scripts/benchmark.py --n 500 --output docs/benchmark_onnx_raw.json
```

Restaurar `USE_ONNX=false MODEL_FILE=model.pkl docker compose up -d api` para
voltar ao baseline. Reiniciar a API zera seus contadores Prometheus.
