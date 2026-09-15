# TODO — Dev C: Matheus Ferreira

Revisão de 15/09/2026. Dataset, EDA, modelo, Airflow e ONNX.
Fonte: [requisitos oficiais](../content/tech-challenge.md).
Evidências: [auditoria](../../docs/status-entrega.md).

## ETAPA 1 — EDA

- [x] `notebooks/01_eda.ipynb` presente, com 16 células de código.
- [x] Distribuição de classes, comprimento de textos, nulos, duplicatas e amostras analisados no código.
- [x] `docs/eda_resumo.md` e gráficos presentes.
- [x] Mapeamento das cinco condições para três urgências documentado e aplicado na API.
- [x] Auditoria reproduziu 14.438 linhas, zero nulos e 3.211 repetições de texto.
- [x] Corrigida documentação: 2.929 textos com múltiplos rótulos e 988 textos comuns entre treino/teste oficiais.
- [x] Notebook executado do início ao fim: 16 células concluídas, outputs salvos e quatro gráficos renovados.
- [ ] Avaliar split agrupado por texto e tratamento dos múltiplos rótulos como melhoria de avaliação; métricas atuais são do split oficial.

Estratificação não elimina sobreposição de textos. Não declarar duplicatas
apenas na mesma classe nem ausência de vazamento com base nesse split.

## ETAPA 2 — Dataset e modelo

- [x] Dataset público Medical Abstracts TC Corpus; download automatizado.
- [x] Limpeza, lowercase, stopwords e funções pickláveis em `src/preprocess.py`.
- [x] Pipeline de pré-processamento, TF-IDF e classificador; CLI de treino.
- [x] Código compara RandomForest, LinearSVC e LogisticRegression; GridSearchCV para modelos lineares.
- [x] Split estratificado 0,2, seed 42; accuracy, F1 e relatórios por condição.
- [x] LogisticRegression `C=0.3`, `class_weight=balanced`, `predict_proba` nativo.
- [x] Configuração atual ONNX: `sublinear_tf=False`, `token_pattern=r"[a-zA-Z0-9_]+"`.
- [x] Modelo atual reproduzido em sklearn 1.9.0: holdout accuracy 0,6083795, macro-F1 0,6110232.
- [x] Métricas/relatório versionados; `.pkl` e `.onnx` ignorados pelo Git.
- [x] API mapeia condition_label 1–5 para urgência, preservando confiança da condição predita.

## ETAPA 7 — Airflow

### Entrega oficial local

- [x] `Dockerfile.airflow` e `docker-compose.airflow.yml` para Airflow standalone.
- [x] DAG `retrain_triagem_dag`, diário às 03:00, `catchup=False`, retries=2, retry_delay=2 min.
- [x] `ingest`: lê CSV, valida colunas/nulos/rótulos e salva dados processados.
- [x] `train`: BashOperator chama `python -m src.train --classifier logistic`.
- [x] `save`: versiona `.pkl`, métricas e relatório locais; atualiza manifesto.
- [x] Encadeamento `ingest >> train >> save`.
- [x] Print `docs/dag_execucao.png` renovado: run `evidence-20260914-onnx` com três tasks success; estados em `docs/airflow_execucao.json`.
- [ ] Reexecutar em clone limpo para aceite final; a DAG foi reexecutada com sucesso no checkout atual.

### Extensão interna ECS/S3 — ainda não entregue

- [ ] Integrar `EcsRunTaskOperator` ou equivalente, com permissões RunTask/PassRole.
- [ ] Implementar download dos dados e upload/versionamento no S3 antes da task encerrar.
- [ ] Exportar/validar ONNX no ciclo de retreino e definir promoção para inferência.
- [ ] Executar fluxo completo na AWS e registrar modelo atualizado no S3.

A DAG local atende ao pipeline simples pedido no enunciado. A extensão AWS
foi prevista no plano interno, mas não deve ser descrita como implementada.
O Compose atual não tem volume persistente para o banco/metadados Airflow.

## ETAPA 9 — ONNX e latência

- [x] `src/export_onnx.py` carrega `.pkl` e exporta `tfidf → clf` via skl2onnx.
- [x] Entrada StringTensor `[None, 1]`; saída rótulo + matriz de probabilidades (`zipmap=False`).
- [x] Pré-processamento Python aplicado antes do runtime na API.
- [x] Paridade integral revalidada: 2.888/2.888, zero divergências; max Δprobabilidade 2,65×10⁻⁷.
- [x] `docs/latencia_comparativo.md`: medições na mesma máquina, 500 chamadas, p95 −24,6%.
- [x] Tabela p50/p95/p99, throughput, tamanho e conclusão; benchmark controlado é evidência registrada em 13/09.
- [x] ONNX 8.742.267 bytes publicado em S3 e usado em produção; [release](../../docs/deploy_onnx.md).
- [x] Extração de classe/confiança da API testada com ONNX real local e no Fargate.
- [x] Código integrado na `develop`; não houve PR/merge para `master` nesta revisão.

## Pendências finais do responsável

- [x] Executar/salvar notebook e renovar prints da DAG/EDA.
- [ ] Reproduzir Airflow em clone limpo.
- [ ] Confirmar com o time se a extensão ECS/S3 fica fora da entrega acadêmica atual.
- [ ] Apoiar Dev A no vídeo com grafo Airflow e comparação de latência.
