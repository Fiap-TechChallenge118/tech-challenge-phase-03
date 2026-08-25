# TODO — Dev C: Matheus Ferreira

**Eixo de responsabilidade:** Dataset, Modelo NLP, Airflow e Otimização (ONNX)
**Fases cobertas:** FASE 1 → FASE 6 → FASE 8
**Peso na nota (PDF):** Modelagem e Otimização 20% + Orquestração Airflow 15% = **35%**

---

## FASE 1 — Dataset e modelo baseline de classificação de urgência

**Etapa PDF:** Etapa 4 — Otimização de Latência e Entrega (modelo base)

**Objetivo:** Ter um classificador de urgência treinado, avaliado e serializado como `models/model.pkl`, pronto para ser consumido pela API.

**Entregável:** `models/model.pkl` (pipeline completo TF-IDF + classificador) + métricas de avaliação documentadas no README.

**Dependências:**
- Requer: FASE 0 concluída (estrutura de pastas, `requirements.txt`)
- Bloqueia: FASE 3 (Docker precisa do modelo), FASE 6 (DAG chama `src/train.py`) e FASE 8 (ONNX parte do `.pkl`)

**Branch:** `fase-1-dataset-modelo-baseline`

---

### Checklist

#### Escolha e obtenção do dataset
- [ ] Escolher um dos datasets sugeridos pelo PDF (mínimo 2.000 amostras):
  - Opção A: **Medical Abstracts TC Corpus** (Kaggle) — textos de resumos médicos com classificação
  - Opção B: Recortes do **MIMIC-III** (acesso aberto via PhysioNet)
  - Opção C: Qualquer CSV público com coluna de texto (laudo/sintoma) + coluna de classificação
- [ ] Baixar o dataset e salvar o arquivo bruto em `data/raw/` (ex.: `data/raw/dataset.csv`)
- [ ] Se o download for via script, criar `data/raw/download.sh` ou `scripts/download_data.py` com a URL
- [ ] Verificar que o dataset tem ao menos 2.000 amostras — registrar a contagem

#### Mapeamento para as 3 classes de urgência
- [ ] Mapear as classes originais do dataset para as 3 categorias do projeto:
  - `normal` — condições não urgentes
  - `atenção` — condições que requerem acompanhamento
  - `urgente` — condições de risco imediato
- [ ] Documentar o mapeamento em um comentário em `src/preprocess.py`
- [ ] Verificar distribuição de classes após mapeamento — registrar o número de amostras por classe

#### Pré-processamento (`src/preprocess.py`)
- [ ] Criar `src/__init__.py` (vazio)
- [ ] Criar `src/preprocess.py` com a função `preprocess_text(text: str) -> str`:
  - [ ] Converter para minúsculas
  - [ ] Remover caracteres especiais e pontuação excessiva (manter letras, números e espaços)
  - [ ] Remover stopwords em português (usar `nltk.corpus.stopwords` ou lista manual)
  - [ ] Retornar o texto limpo como string
- [ ] Criar função `load_and_prepare(raw_path: str) -> tuple[pd.Series, pd.Series]`:
  - [ ] Ler o CSV com `pandas`
  - [ ] Aplicar `preprocess_text` na coluna de texto
  - [ ] Retornar `(X, y)` onde X é a série de textos e y é a série de labels

#### Pipeline de treinamento (`src/train.py`)
- [ ] Criar `src/train.py` como script CLI executável:
  - [ ] Aceitar argumentos via `argparse`:
    - `--data-path`: caminho para o CSV processado (padrão: `data/processed/dataset.csv`)
    - `--model-path`: onde salvar o `.pkl` (padrão: `models/model.pkl`)
    - `--random-state`: seed para reprodutibilidade (padrão: `42`)
  - [ ] Implementar o pipeline sklearn:
    ```python
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression  # ou LinearSVC ou RandomForest

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))
    ])
    ```
  - [ ] Usar `train_test_split` com `test_size=0.2` e `random_state` fixo
  - [ ] Treinar o pipeline no conjunto de treino
  - [ ] Avaliar no conjunto de teste e imprimir:
    - Accuracy
    - Precision, Recall e F1 por classe (`classification_report`)
  - [ ] Serializar o pipeline completo com `joblib.dump(pipeline, model_path)`
  - [ ] Logar (com `logging`) o caminho onde o modelo foi salvo
- [ ] Confirmar que o script pode ser chamado via linha de comando:
  ```bash
  python src/train.py --data-path data/processed/dataset.csv --model-path models/model.pkl
  ```

#### Validação do modelo
- [ ] Rodar `python src/train.py` e confirmar que `models/model.pkl` é gerado
- [ ] Verificar que o modelo carrega corretamente com `joblib.load("models/model.pkl")`
- [ ] Testar uma predição manual:
  ```python
  import joblib
  model = joblib.load("models/model.pkl")
  result = model.predict(["paciente com dor leve"])
  print(result)  # deve retornar array com uma das 3 classes
  ```
- [ ] Verificar que `model.predict_proba()` está disponível (necessário para o campo `confianca` da API):
  - Se usar `LinearSVC`, substituir por `LogisticRegression` ou adicionar `CalibratedClassifierCV`

#### Documentação das métricas
- [ ] Registrar as métricas finais (accuracy, F1 por classe) em uma seção do README
- [ ] Salvar o `classification_report` completo em `docs/metricas_modelo.txt`

#### Processamento dos dados para a pasta `processed`
- [ ] Criar script ou trecho em `src/train.py` que salva o dataset pré-processado em `data/processed/dataset.csv`

#### Finalização
- [ ] Confirmar que `models/model.pkl` **não é commitado** (está no `.gitignore`)
- [ ] Commitar código-fonte: `feat(model): add preprocessing pipeline and train script`
- [ ] Abrir PR de `fase-1-dataset-modelo-baseline` → `main`
- [ ] Comunicar ao Dev A e Dev B que o `model.pkl` está disponível localmente

---

### ✅ Definition of Done — FASE 1
- `python src/train.py` roda sem erro e gera `models/model.pkl`
- O modelo prediz as 3 classes (`normal`, `atenção`, `urgente`)
- `model.predict_proba()` disponível (para o campo `confianca` da API)
- Métricas de avaliação (accuracy e F1) documentadas no README
- `src/train.py` aceita argumentos CLI (reutilizado pela DAG na FASE 6)
- PR aberto e revisado

---

---

## FASE 6 — DAG Airflow de treino/retreino do modelo

**Etapa PDF:** Etapa 2 — CI/CD e Pipeline Automatizado

**Objetivo:** Criar uma DAG Airflow que simula o ciclo de retreino completo: ingestão de dados → treino → salvamento do modelo.

**Entregável:** `dags/retrain_triagem_dag.py` + print da DAG executada com sucesso (grafo todo verde) em `docs/`.

**Dependências:**
- Requer: FASE 1 (`src/train.py` funcionando como script CLI)
- Bloqueia: (não bloqueia nenhuma outra fase diretamente, mas é entregável obrigatório do PDF)

**Branch:** `fase-6-dag-airflow`

---

### Checklist

#### Setup do Airflow local
- [ ] Escolher método de execução local (uma das opções abaixo):

  **Opção A — Standalone (mais simples para desenvolvimento):**
  ```bash
  pip install apache-airflow==2.9.1
  export AIRFLOW_HOME=~/airflow
  airflow standalone
  ```

  **Opção B — Docker Compose oficial do Airflow:**
  ```bash
  curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.9.1/docker-compose.yaml'
  mkdir -p ./dags ./logs ./plugins ./config
  docker compose -f docker-compose.yaml up airflow-init
  docker compose -f docker-compose.yaml up
  ```

- [ ] Acessar a Airflow UI em `http://localhost:8080` (usuário: `admin`, senha: informada no terminal)
- [ ] Confirmar que a UI carrega sem erro

#### DAG de retreino (`dags/retrain_triagem_dag.py`)
- [ ] Criar `dags/retrain_triagem_dag.py` com o seguinte esqueleto base:
  ```python
  from airflow import DAG
  from airflow.operators.python import PythonOperator
  from datetime import datetime, timedelta

  default_args = {
      "owner": "dev-c",
      "retries": 2,
      "retry_delay": timedelta(minutes=5),
  }

  with DAG(
      dag_id="retrain_triagem",
      default_args=default_args,
      schedule="@weekly",
      start_date=datetime(2024, 1, 1),
      catchup=False,
      tags=["triagem", "retreino"],
  ) as dag:
      ...
  ```

- [ ] Implementar **Task 1 — `ingest`:**
  - [ ] Função Python `ingest()` que:
    - [ ] Lê o CSV de `data/raw/dataset.csv` com pandas
    - [ ] Valida que as colunas necessárias existem (texto e label)
    - [ ] Loga a contagem de amostras
    - [ ] Salva o dataset validado em `data/processed/dataset.csv`
  - [ ] Criar `PythonOperator(task_id="ingest", python_callable=ingest)`

- [ ] Implementar **Task 2 — `train`:**
  - [ ] Função Python `train()` que:
    - [ ] Chama `src/train.py` via `subprocess.run` ou importa diretamente a lógica de treino
    - [ ] Usa os dados de `data/processed/dataset.csv`
    - [ ] Salva o modelo treinado em `models/model_temp.pkl` (arquivo temporário)
    - [ ] Loga as métricas de avaliação
  - [ ] Criar `PythonOperator(task_id="train", python_callable=train)`

- [ ] Implementar **Task 3 — `save`:**
  - [ ] Função Python `save()` que:
    - [ ] Gera um timestamp: `datetime.now().strftime("%Y%m%d_%H%M%S")`
    - [ ] Copia `models/model_temp.pkl` para `models/model_<timestamp>.pkl` (versão histórica)
    - [ ] Sobrescreve `models/model.pkl` com o novo modelo
    - [ ] Loga o caminho do artefato salvo
  - [ ] Criar `PythonOperator(task_id="save", python_callable=save)`

- [ ] Encadear as tasks na ordem correta:
  ```python
  ingest_task >> train_task >> save_task
  ```

#### Configuração e retries
- [ ] Confirmar que `retries=2` e `retry_delay=timedelta(minutes=5)` estão nos `default_args`
- [ ] Confirmar que `catchup=False` está definido na DAG
- [ ] Confirmar que `schedule` está definido (ex.: `"@weekly"` ou `"0 2 * * 0"`)

#### Execução e validação
- [ ] Copiar `dags/retrain_triagem_dag.py` para o diretório `dags/` do Airflow
- [ ] Aguardar a DAG aparecer na UI (pode levar 30s)
- [ ] Verificar que não há erros de import na UI (aba "DAGs" mostra a DAG sem ícone de erro)
- [ ] Executar a DAG manualmente: botão "Trigger DAG" na UI
- [ ] Aguardar todas as tasks ficarem verdes (status: `success`)
- [ ] Confirmar que `models/model.pkl` foi atualizado após a execução
- [ ] **Salvar print/screenshot do grafo com todas as tasks verdes em `docs/dag_execucao.png`**

#### Finalização
- [ ] Commitar: `feat(airflow): add retrain DAG with ingest, train and save tasks`
- [ ] Abrir PR de `fase-6-dag-airflow` → `main`

---

### ✅ Definition of Done — FASE 6
- `dags/retrain_triagem_dag.py` presente no repositório
- DAG executada com sucesso end-to-end (todas as tasks verdes)
- `models/model.pkl` atualizado após execução da DAG
- Print do grafo verde salvo em `docs/dag_execucao.png`
- `retries`, `retry_delay` e `catchup=False` configurados
- PR aberto e revisado

---

---

## FASE 8 — Otimização de latência: export ONNX e comparativo

**Etapa PDF:** Etapa 4 — Otimização de Latência e Entrega

**Objetivo:** Aplicar otimização de latência exportando o pipeline para ONNX Runtime e comprovar o ganho com números comparativos.

**Entregável:** `models/model.onnx` + tabela comparativa (sklearn vs ONNX) em `docs/latencia_comparativo.md`.

**Dependências:**
- Requer: FASE 1 (`models/model.pkl` treinado) e FASE 3 (baseline p50/p95/p99 medido)
- Apoio: Dev B executa o mesmo benchmark dentro do container para garantir condições iguais de medição
- Bloqueia: (não bloqueia outras fases, mas é critério de avaliação de 20%)

**Branch:** `fase-8-otimizacao-onnx`

---

### Checklist

#### Instalação e verificação das dependências
- [ ] Confirmar que `skl2onnx` e `onnxruntime` estão fixados no `requirements.txt` (Dev B adicionou na FASE 0)
- [ ] Instalar localmente: `pip install skl2onnx==1.17.0 onnxruntime==1.18.0`
- [ ] Verificar versão do sklearn usada no treino — ela determina o opset do ONNX:
  ```python
  import sklearn; print(sklearn.__version__)
  ```

#### Script de exportação (`src/export_onnx.py`)
- [ ] Criar `src/export_onnx.py` com as seguintes etapas:
  - [ ] Carregar o pipeline completo: `pipeline = joblib.load("models/model.pkl")`
  - [ ] Definir o tipo de entrada para `skl2onnx`:
    ```python
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import StringTensorType

    initial_type = [("texto_input", StringTensorType([None, 1]))]
    ```
  - [ ] Converter o pipeline:
    ```python
    onnx_model = convert_sklearn(pipeline, initial_types=initial_type, target_opset=12)
    ```
  - [ ] Salvar o modelo ONNX:
    ```python
    with open("models/model.onnx", "wb") as f:
        f.write(onnx_model.SerializeToString())
    ```
  - [ ] Logar o tamanho do arquivo gerado
- [ ] Rodar o script: `python src/export_onnx.py`
- [ ] Confirmar que `models/model.onnx` foi gerado sem erro

#### Validação de paridade de predições
- [ ] Criar script de validação (pode ser em `src/export_onnx.py` ou separado):
  - [ ] Carregar 100 amostras do dataset de teste
  - [ ] Obter predições com o pipeline sklearn: `pipeline.predict(amostras)`
  - [ ] Obter predições com o modelo ONNX:
    ```python
    import onnxruntime as rt
    sess = rt.InferenceSession("models/model.onnx")
    input_name = sess.get_inputs()[0].name
    pred_onnx = sess.run(None, {input_name: amostras.reshape(-1, 1)})[0]
    ```
  - [ ] Comparar as predições: as 100 amostras devem ter a **mesma classe** em ambos os modelos
  - [ ] Imprimir quantas divergências existem (esperado: 0)
- [ ] Confirmar paridade antes de prosseguir com o benchmark

#### Adaptação da API para suportar ONNX (`app/model_loader.py`)
- [ ] Atualizar `app/model_loader.py` para:
  - [ ] Ler a variável de ambiente `USE_ONNX` (padrão: `"false"`)
  - [ ] Se `USE_ONNX=true`: carregar `models/model.onnx` com `onnxruntime.InferenceSession`
  - [ ] Se `USE_ONNX=false`: carregar `models/model.pkl` com `joblib.load` (comportamento atual)
  - [ ] Expor uma função `predict(text: str) -> tuple[str, float]` que abstrai qual runtime está sendo usado
- [ ] Atualizar `app/main.py` para usar a nova função `predict()` do `model_loader`
- [ ] Testar localmente com `USE_ONNX=true` e confirmar que `/predict` continua funcionando

#### Benchmark comparativo
- [ ] Usar o mesmo `scripts/benchmark.py` da FASE 3 (Dev B) com `--n 500`
- [ ] Rodar o benchmark com o modelo sklearn (dentro do container — pedir apoio ao Dev B):
  ```bash
  USE_ONNX=false python scripts/benchmark.py --n 500 --url http://localhost:8000/predict
  ```
- [ ] Rodar o benchmark com o modelo ONNX:
  ```bash
  USE_ONNX=true python scripts/benchmark.py --n 500 --url http://localhost:8000/predict
  ```
- [ ] Garantir que ambas as medições usam a **mesma máquina** e **mesmas condições**

#### Documentação comparativa (`docs/latencia_comparativo.md`)
- [ ] Criar `docs/latencia_comparativo.md` com:
  - [ ] Tabela comparativa com colunas: `Modelo | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (req/s) | Tamanho do artefato`
    - Linha 1: `sklearn (.pkl)`
    - Linha 2: `ONNX (.onnx)`
  - [ ] Coluna adicional: `% de ganho` em p95 (fórmula: `(sklearn_p95 - onnx_p95) / sklearn_p95 * 100`)
  - [ ] Especificação da máquina de teste (mesma da FASE 3)
  - [ ] Seção "Conclusão" com 2-3 frases sobre o resultado

#### Verificação de que `models/model.onnx` não é commitado
- [ ] Confirmar que `*.onnx` está no `.gitignore`
- [ ] Commitar apenas os scripts, não os artefatos binários

#### Finalização
- [ ] Commitar: `feat(model): add ONNX export script and latency comparison`
- [ ] Abrir PR de `fase-8-otimizacao-onnx` → `main`

---

### ✅ Definition of Done — FASE 8
- `python src/export_onnx.py` gera `models/model.onnx` sem erro
- Paridade de predições validada: 0 divergências entre sklearn e ONNX nas amostras de teste
- API funciona com `USE_ONNX=true` e `USE_ONNX=false`
- `docs/latencia_comparativo.md` com tabela comparativa incluindo % de ganho
- Benchmark realizado nas mesmas condições que o baseline da FASE 3
- PR aberto e revisado

---

## ⚠️ Pontos em aberto — Dev C

- [ ] **Dataset:** o PDF não especifica um dataset obrigatório. Se o Medical Abstracts TC Corpus (Kaggle) não tiver as 3 classes mapeáveis para `normal/atenção/urgente`, será necessário ajustar o mapeamento ou usar outro dataset. Validar antes de começar.
- [ ] **Método de inferência ONNX com `predict_proba`:** `skl2onnx` exporta `predict_proba` como segunda saída do ONNX. Verificar que a adaptação em `app/model_loader.py` extrai a probabilidade corretamente para preencher o campo `confianca`.
- [ ] **Airflow no repositório vs. instalação externa:** o plan.md menciona subir Airflow localmente para a FASE 6. Confirmar com Dev B se haverá um `docker-compose.airflow.yml` separado no repositório ou se cada dev gerencia a instalação individualmente.
- [ ] **Benchmark dentro do container (FASE 8):** o plan.md indica que Dev B apoia a medição dentro do container. Alinhar previamente para garantir que ambos usam a mesma máquina e o mesmo N.
- [ ] **`skl2onnx` com pipeline TF-IDF + LinearSVC:** se o classificador escolhido for `LinearSVC`, verificar a compatibilidade com `skl2onnx` — pode ser necessário usar `LogisticRegression` ou adicionar `CalibratedClassifierCV` para suporte a `predict_proba` e exportação ONNX.
