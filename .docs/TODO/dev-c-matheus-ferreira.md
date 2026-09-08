# TODO — Dev C: Matheus Ferreira

**Eixo de responsabilidade:** Dataset, EDA, Modelo NLP, Airflow e Otimização (ONNX)
**Etapas cobertas:** ETAPA 1 → ETAPA 2 → ETAPA 7 → ETAPA 9
**Peso na nota (PDF):** Modelagem e Otimização 20% + Orquestração Airflow 15% = **35%**

> Arquitetura do projeto: **100% ECS + Fargate**. Treino = ECS Fargate Task efêmera disparada pela DAG, lê dataset do S3 e grava `model.onnx`/`model.pkl` no S3. Inferência = ECS Fargate Service.
> Fonte de verdade: `.docs/content/tech-challenge.md`. Plano: `.docs/content/plan.md`.

---

## ETAPA 1 — EDA (Análise Exploratória)

**Objetivo:** entender o dataset antes de modelar — base para o mapeamento das 3 classes de urgência.

**Entregável:** `notebooks/01_eda.ipynb` + `docs/eda_resumo.md`.

**Dependências:** Requer ETAPA 0. Bloqueia ETAPA 2.

**Branch:** `etapa-1-eda`

---

### Checklist
- [ ] Carregar o dataset bruto de `data/raw/` no `notebooks/01_eda.ipynb` *(notebook vazio — só `.gitkeep`)*
- [ ] Distribuição de classes (identificar desbalanceamento)
- [ ] Estatísticas de comprimento de texto (caracteres/tokens): média, mediana, p95
- [ ] Contagem de nulos, duplicatas e amostras por classe
- [ ] Amostras representativas de cada classe (inspeção qualitativa)
- [ ] Conclusões que embasam o mapeamento para `normal`/`atenção`/`urgente`
- [ ] Registrar achados em `docs/eda_resumo.md`
- [ ] Commit: `docs(eda): add exploratory data analysis`; PR → `main`

### ✅ Definition of Done — ETAPA 1
- Notebook executa do início ao fim sem erro ⬜
- `docs/eda_resumo.md` com distribuição de classes, comprimento de texto e proposta de mapeamento ⬜
- PR aberto e revisado ⬜

---
---

## ETAPA 2 — Dataset + Feature Engineering + Modelo baseline

**Objetivo:** classificador de urgência treinado, avaliado e serializado, pronto para o S3.

**Entregável:** `models/model.pkl` (pipeline TF-IDF + classificador) + métricas em `docs/metricas_modelo.txt` e no README.

**Dependências:** Requer ETAPA 1. Bloqueia ETAPA 7 (DAG chama `src/train.py`) e ETAPA 9 (ONNX parte do `.pkl`).

**Branch:** `etapa-2-dataset-modelo`

---

### Checklist

#### Dataset
- [x] Dataset público escolhido: **Medical Abstracts TC Corpus** (14.438 amostras, Kaggle) → `data/raw/`
- [x] Registrado mapeamento das 5 condições originais → `normal`/`atenção`/`urgente` (em `docs/dataset.md`)

#### Pré-processamento (`src/preprocess.py`)
- [x] `clean_text(text)`: lowercase, remoção de pontuação/dígitos, normalização de espaços
- [x] `remove_stopwords(text)`: remove stopwords inglesas (`sklearn.ENGLISH_STOP_WORDS`)
- [x] `preprocess(text)`: composição `clean_text + remove_stopwords`
- [x] `preprocess_texts(texts)`: versão iterável, picklável (usada no `FunctionTransformer`)

#### Feature engineering + treino (`src/train.py`, CLI com argparse)
- [x] Args: `--data`, `--test-data`, `--model`, `--metrics`, `--report`, `--classifier`, `--test-size`, `--random-state`
- [x] Pipeline: `FunctionTransformer(preprocess_texts)` + `TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)` + classificador
- [x] Compara **3 classificadores** (RandomForest, LinearSVC, LogisticRegression) com `GridSearchCV`
- [x] `train_test_split(test_size=0.2, random_state=42, stratify=y)`
- [x] Avalia: accuracy + macro-F1 + weighted-F1 + `classification_report` por classe
- [x] `joblib.dump(pipeline, model_path)` — melhor pipeline serializado
- [x] Salva `metrics.json` + `classification_report.txt`

#### Validação
- [x] `python src/train.py` gera `models/model.pkl` (19 MB, sklearn 1.4.2)
- [x] Pipeline prediz corretamente condition_label (1–5) mapeado para urgência via `app/model_loader.py`
- [x] `predict_proba` disponível (LogisticRegression venceu — compatível com `skl2onnx`)
- [x] Holdout oficial: accuracy=0.6035, macro-F1=0.6045

#### Documentação e finalização
- [x] Métricas no README (tabela comparativa + resultados holdout)
- [x] `docs/metricas_modelo.txt` com `classification_report` completo
- [x] `models/metrics.json` com métricas estruturadas
- [x] `models/model.pkl` no `.gitignore` *(não commitado)*
- [ ] Commit: `feat(model): add preprocessing and train pipeline`; PR → `main`
- [ ] Comunicar a Dev A e Dev B que o modelo está disponível (e alinhar upload para o S3)

### ✅ Definition of Done — ETAPA 2
- `python src/train.py` gera `models/model.pkl` sem erro ✅
- Modelo prediz as 3 classes via mapeamento de urgência ✅
- `predict_proba` disponível ✅
- Métricas documentadas ✅
- `src/train.py` reutilizável por CLI (usado pela DAG na ETAPA 7) ✅
- PR aberto e revisado ⬜

---
---

## ETAPA 7 — DAG Airflow de treino/retreino (via ECS Fargate Task)

**Objetivo:** DAG que simula o ciclo de retreino: ingestão → treino → salvamento no S3. O treino roda como ECS Fargate Task.

**Entregável:** `dags/retrain_triagem_dag.py` + print do grafo verde em `docs/dag_execucao.png`.

**Dependências:** Requer ETAPA 2 (`src/train.py`) e a Task Definition de treino (ETAPA 10, Dev B). Para desenvolver a DAG localmente, a task de treino pode rodar em `PythonOperator` até o ECS estar pronto.

**Branch:** `etapa-7-dag-airflow`

---

### Checklist

#### Setup Airflow local
- [ ] Subir Airflow (standalone ou docker-compose oficial) e validar acesso à UI

#### DAG (`dags/retrain_triagem_dag.py`)
- [ ] `default_args` com `retries=2`, `retry_delay=timedelta(minutes=5)`
- [ ] DAG `retrain_triagem`, `schedule="@weekly"`, `catchup=False`, `tags=["triagem","retreino"]`
- [ ] **Task `ingest`:** lê CSV de `data/raw/` (ou do S3), valida colunas, loga contagem, salva em `data/processed/` (ou S3 processed)
- [ ] **Task `train`:** dispara **ECS Fargate Task** via `EcsRunTaskOperator` rodando `src/train.py` (fallback `PythonOperator` local durante o desenvolvimento)
- [ ] **Task `save`:** versiona artefato no **S3** (`model_<timestamp>`) e atualiza o `model.onnx`/`model.pkl` corrente
- [ ] Encadear: `ingest >> train >> save`

#### Execução e validação
- [ ] DAG aparece na UI sem erro de import
- [ ] Trigger manual → todas as tasks verdes
- [ ] Artefato atualizado no S3 após execução
- [ ] Print do grafo verde em `docs/dag_execucao.png`
- [ ] Commit: `feat(airflow): add retrain DAG (ingest, train via ECS, save to S3)`; PR → `main`

### ✅ Definition of Done — ETAPA 7
- DAG presente e executada end-to-end (tasks verdes) ⬜
- Artefato atualizado no S3 após a execução ⬜
- Print do grafo verde salvo ⬜
- `retries`/`retry_delay`/`catchup=False` configurados ⬜
- PR aberto e revisado ⬜

---
---

## ETAPA 9 — Otimização de latência: export ONNX e comparativo

**Objetivo:** exportar o pipeline para ONNX e comprovar ganho de latência com números.

**Entregável:** `models/model.onnx` + `docs/latencia_comparativo.md`.

**Dependências:** Requer ETAPA 2 (modelo) e ETAPA 5 (baseline medido, Dev B).

**Branch:** `etapa-9-otimizacao-onnx`

---

### Checklist

#### Export (`src/export_onnx.py`)
- [ ] Carregar `models/model.pkl`
- [ ] `initial_type = [("texto_input", StringTensorType([None, 1]))]`
- [ ] `convert_sklearn(pipeline, initial_types=..., target_opset=12)` → salvar `models/model.onnx`
- [ ] Logar o tamanho do arquivo

#### Paridade
- [ ] 100 amostras: comparar `pipeline.predict` vs `onnxruntime` — esperado 0 divergências
- [ ] Confirmar paridade antes do benchmark

#### Benchmark comparativo
- [ ] Rodar `scripts/benchmark.py --n 500` com `USE_ONNX=false` e `USE_ONNX=true` (mesma máquina/condições — alinhar com Dev B)
- [ ] `docs/latencia_comparativo.md`: tabela `Modelo | p50 | p95 | p99 | Throughput | Tamanho` + `% de ganho` em p95 + conclusão

#### Finalização
- [ ] Confirmar `*.onnx` no `.gitignore` *(já está: `*.onnx` no `.gitignore`)* ✅
- [ ] Commit: `feat(model): add ONNX export and latency comparison`; PR → `main`
- [ ] Coordenar com Dev A o upload do `model.onnx` para o S3 (consumido pelo serviço)

### ✅ Definition of Done — ETAPA 9
- `python src/export_onnx.py` gera `models/model.onnx` ⬜
- Paridade validada (0 divergências) ⬜
- `docs/latencia_comparativo.md` com tabela + % de ganho ⬜
- Benchmark nas mesmas condições do baseline da ETAPA 5 ⬜
- PR aberto e revisado ⬜

---

## ⚠️ Pontos em aberto — Dev C
- [x] Dataset definitivo: **Medical Abstracts TC Corpus** — mapeamento para 3 classes validado em `docs/dataset.md`
- [ ] `predict_proba` no ONNX: `skl2onnx` exporta como 2ª saída — garantir extração correta da confiança em `app/model_loader.py` (`_predict_onnx`)
- [x] Classificador: **LogisticRegression** venceu (macro-F1=0.609) — compatível com `skl2onnx` + `predict_proba`
- [ ] Alinhar com Dev B a Task Definition de treino (imagem ECR, comando, variáveis S3) antes da ETAPA 7
