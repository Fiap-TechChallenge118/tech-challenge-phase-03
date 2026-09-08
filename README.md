# Triagem Médica — Sistema de Classificação de Urgência

<!-- Badge do CI será adicionado na ETAPA 6 -->
<!-- ![CI](https://github.com/ORG/REPO/actions/workflows/ci.yml/badge.svg) -->

> Classificação automática de urgência de laudos médicos (`normal` / `atenção` / `urgente`) via API REST, com pipeline de treino orquestrado, monitoramento e deploy em produção na AWS.

## Visão Geral

<!-- Preencher na ETAPA 11: o que o sistema faz, quem usa, visão de alto nível. -->

## Decisão Arquitetural

### Batch vs Real-Time

A triagem hospitalar é um processo **síncrono e sensível ao tempo**: o resultado precisa ser entregue ao profissional de saúde imediatamente após a submissão do laudo, sem acúmulo em fila. Processar requisições em batch (ex.: Lambda agendado ou job periódico) introduziria latência de minutos a horas, inaceitável para o fluxo clínico.

Por isso, a escolha é **inferência real-time**: cada requisição `POST /predict` recebe resposta em milissegundos, com o modelo já carregado em memória.

### Arquitetura de Deploy (ECS Fargate + ALB)

```
Cliente HTTP
    │
    ▼
Application Load Balancer (ALB)
    │  — balanceamento, health check, terminação TLS
    ▼
ECS Fargate Service  (container FastAPI + uvicorn, persistente)
    │  — baixa model.onnx do S3 no startup, serve /predict /health /metrics
    ▼
Amazon S3  (artefatos de modelo: model.onnx / model.pkl)
```

**Por que ECS Fargate Service (e não Lambda ou EC2)?**

| Critério | Lambda | EC2 | ECS Fargate Service ✅ |
|---|---|---|---|
| Cold start com modelo em memória | Alto (recarrega a cada invocação fria) | Baixo | Baixo (container persistente) |
| Escalabilidade horizontal | Automática, mas limitada pelo cold start | Manual | Automática via desired_count |
| Custo de operação contínua | Barato se ocioso | Caro (instância sempre ligada) | Proporcional ao uso |
| Scrape Prometheus (`/metrics`) | Incompatível (sem IP fixo por invocação) | Possível | Nativo (target estável) |
| Sem gerência de servidor | Sim | Não | Sim |

O container **baixa o artefato do S3 no startup** — o modelo não fica embutido na imagem Docker. Isso permite que um retreino (ECS Fargate Task) atualize o `model.onnx` no S3 sem rebuild da imagem.

### Pipeline de Treino (ECS Fargate Task)

O retreino é um processo **batch sob demanda**, orquestrado por uma DAG do Airflow:

```
Airflow DAG  →  ECS Fargate Task  (container efêmero, mesmo CMD override)
                    │  lê dataset de  s3://bucket/data/raw/
                    │  treina pipeline TF-IDF + LogisticRegression
                    ▼
                s3://bucket/models/model.onnx  (atualizado)
```

A mesma imagem Docker serve inferência (ECS Service, `CMD uvicorn`) e treino (ECS Task, `CMD python src/train.py`), reduzindo superfície de manutenção.

### Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `MODEL_BUCKET` | Bucket S3 dos artefatos | `meu-bucket-modelos` |
| `MODEL_KEY` | Chave do artefato no S3 | `models/model.onnx` |
| `USE_ONNX` | `true` = ONNX Runtime / `false` = sklearn | `true` |
| `AWS_REGION` | Região do bucket | `us-east-1` |
| `LOG_LEVEL` | Nível de log da API | `INFO` |

## Modelo

Classificador de texto (NLP) leve que categoriza o laudo médico em **5 condições**
(`neoplasms`, `digestive system diseases`, `nervous system diseases`,
`cardiovascular diseases`, `general pathological conditions`) — decisão de escopo
acordada com o grupo em substituição ao mapeamento em 3 urgências, já que o dataset
fornece o rótulo de condição nativamente.

| Componente | Detalhe |
|------------|---------|
| Dataset | [Medical Abstracts TC Corpus](https://www.kaggle.com/datasets/saharalaa/medical-abstracts-tc-corpus) (Kaggle) |
| Pipeline | `preprocess → TF-IDF → LogisticRegression` (scikit-learn, CPU) |
| Artefato | `models/model.pkl` (pipeline completo, consumível pela API) |

### Resultados (split de teste, 2.310 laudos)

| Classificador | Acurácia | Macro-F1 |
|---------------|---------:|---------:|
| RandomForest (default) | 0.486 | 0.440 |
| LinearSVC (C=0.1, balanced) | 0.595 | 0.594 |
| **LogisticRegression (C=0.3, balanced)** | **0.607** | **0.609** |

Métricas completas (F1 por classe, holdout oficial): `docs/metricas_modelo.txt` e
`models/metrics.json`.

### Treinar

```bash
pip install -e ".[dev]"
python scripts/download_data.py            # baixa o dataset → data/raw/
python src/train.py \
    --data data/raw/medical_tc_train.csv \
    --test-data data/raw/medical_tc_test.csv \
    --model models/model.pkl \
    --classifier all --test-size 0.2 --random-state 42
```

### Usar o modelo

```python
import sys, joblib

sys.path.insert(0, "src")   # expõe o módulo `preprocess` usado pelo .pkl
import preprocess           # noqa: F401  (necessário p/ joblib desserializar)

pipe = joblib.load("models/model.pkl")
label = pipe.predict(["patient presents with chest pain radiating to the left arm"])[0]
print(label)  # 1..5 → condição médica
```

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Terraform ≥ 1.7 (para deploy na AWS)
- Credenciais AWS configuradas (`~/.aws/credentials` ou variáveis de ambiente)

## Como Executar

### Desenvolvimento local

```bash
pip install -e ".[dev]"
cp .env.example .env   # preencha MODEL_BUCKET e AWS_REGION se quiser o modelo real
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

> Sem `MODEL_BUCKET` configurado, a API inicia em modo **mock** e responde normalmente.

### Docker isolado

```bash
docker build -t triagem-api .
docker run -p 8000:8000 --env-file .env triagem-api
# → http://localhost:8000/docs
```

### Stack completa (Docker Compose)

```bash
docker compose up
# API     → http://localhost:8000
# Prometheus → http://localhost:9090
# Grafana → http://localhost:3000  (admin / admin)
```

## Testes e Qualidade de Código

### Pré-requisito

```bash
pip install -e ".[dev]"
```

### Lint (ruff)

```bash
ruff check app/ src/
```

Saída esperada: `All checks passed!`

### Testes automatizados (pytest)

Os testes **não dependem de modelo real, S3 ou arquivo local** — o `model_loader`
é substituído por um mock via `monkeypatch` em `tests/conftest.py`.

```bash
pytest -v
```

Saída esperada:

```
tests/test_health.py::test_health_returns_200                    PASSED
tests/test_health.py::test_health_body_has_status_key            PASSED
tests/test_health.py::test_health_body_has_model_key             PASSED
tests/test_predict.py::test_predict_valid_text_returns_200       PASSED
tests/test_predict.py::test_predict_valid_text_returns_valid_class PASSED
tests/test_predict.py::test_predict_empty_text_returns_422       PASSED
tests/test_predict.py::test_predict_blank_text_returns_422       PASSED
tests/test_predict.py::test_predict_missing_field_returns_422    PASSED
tests/test_predict.py::test_predict_text_too_long_returns_422    PASSED
tests/test_predict.py::test_predict_response_fields_present      PASSED

10 passed in ~0.1s
```

### Cobertura dos testes

| Teste | O que valida |
|---|---|
| `test_health_returns_200` | `GET /health` retorna HTTP 200 |
| `test_health_body_has_status_key` | Corpo contém `status: ok` |
| `test_health_body_has_model_key` | Corpo contém a chave `model` |
| `test_predict_valid_text_returns_200` | `POST /predict` com texto válido retorna HTTP 200 |
| `test_predict_valid_text_returns_valid_class` | Resposta contém `classe` ∈ {normal, atenção, urgente}, `confianca` ∈ [0,1], `tempo_ms` ≥ 0 |
| `test_predict_empty_text_returns_422` | Texto vazio é rejeitado com HTTP 422 |
| `test_predict_blank_text_returns_422` | Texto com só espaços é rejeitado com HTTP 422 |
| `test_predict_missing_field_returns_422` | Payload sem o campo `texto` retorna HTTP 422 |
| `test_predict_text_too_long_returns_422` | Texto com mais de 5.000 caracteres retorna HTTP 422 |
| `test_predict_response_fields_present` | Resposta contém exatamente os campos `classe`, `confianca` e `tempo_ms` |

## Dataset

O modelo é treinado com o **Medical Abstracts TC Corpus** — 14.438 resumos de artigos médicos em inglês, rotulados em 5 categorias de condições clínicas.

| Atributo | Valor |
|---|---|
| Fonte | [Kaggle](https://www.kaggle.com/datasets/saharalaa/medical-abstracts-tc-corpus) · [GitHub](https://github.com/sebischair/Medical-Abstracts-TC-Corpus) · [HuggingFace](https://huggingface.co/datasets/TimSchopf/medical_abstracts) |
| Total de amostras | 14.438 (11.550 treino / 2.888 teste) |
| Coluna de entrada | `medical_abstract` (texto do resumo) |
| Classes originais | 5 condições clínicas |
| Classes do projeto | 3 (`normal` / `atenção` / `urgente`) |
| Licença | Creative Commons |

**Mapeamento das classes originais → urgência:**

| Classe original | Urgência |
|---|---|
| General pathological conditions | `normal` |
| Digestive system diseases | `normal` |
| Nervous system diseases | `atenção` |
| Neoplasms | `atenção` |
| Cardiovascular diseases | `urgente` |

Documentação completa, instruções de download e justificativa do mapeamento: [`docs/dataset.md`](docs/dataset.md).

## Resultados de Latência

<!-- Preencher na ETAPA 9: tabela comparativa sklearn vs ONNX (docs/latencia_comparativo.md). -->

## CI/CD

<!-- Preencher na ETAPA 6: badge do workflow + link para o GitHub Actions. -->

## Monitoramento

<!-- Preencher na ETAPA 8: descrição da stack Prometheus + Grafana e print do dashboard. -->

## Deploy em Produção

<!-- Preencher na ETAPA 10: URL do ALB + passo a passo do deploy (terraform apply) e rollback. -->

## Vídeo STAR

<!-- Preencher na ETAPA 11: link do vídeo (≤ 5 min). -->

## Time

| Dev | Eixo | Etapas |
|-----|------|--------|
| Alexandre Araújo | Fundação, API, Testes, Documentação | 0, 3, 4, 11 |
| Matheus Santos | Infra, CI/CD, Observabilidade, Cloud | 5, 6, 8, 10 |
| Matheus Ferreira | Dataset, EDA, Modelo, Airflow, ONNX | 1, 2, 7, 9 |
