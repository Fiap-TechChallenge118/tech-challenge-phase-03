# Capturas e evidências — 15/09/2026

Evidências renovadas a partir do código `341746d` (API ONNX integrada).
Capturas feitas das aplicações reais e inspecionadas visualmente.

| Arquivo | Evidência |
|---|---|
| `ci_execucao.png` | GitHub Actions run `34914969894`: lint, test, infra, build e publish aprovados no commit `341746d` |
| `grafana_dashboard.png` | API local reconstruída com ONNX; tráfego real nas três classes, quatro painéis com dados e zero erros de inferência |
| `dag_execucao.png` | Airflow 2.10.5: run `evidence-20260914-onnx`, ingest/train/save em success |
| `eda_class_distribution.png` | Distribuição das cinco condições nos splits oficiais |
| `eda_text_length.png` | Distribuição de comprimento dos textos |
| `eda_length_by_class.png` | Comprimento por condição |
| `eda_urgency_distribution.png` | Distribuição após o mapeamento para urgência |

## Rastreabilidade

- CI: [execução capturada](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/runs/34914969894).
  O commit que adiciona os prints será posterior à execução retratada.
- Grafana: janela fixa 15/09/2026, 01:08–01:13 UTC (14/09, 22:08–22:13 em
  São Paulo). Os dados são do runtime ONNX local, confirmado pelo log de startup.
- Carga: 500 chamadas de benchmark + 20 warmup e tráfego adicional para
  alimentar os painéis. [Dados brutos](benchmark_local_onnx.json).
- Airflow: execução manual encerrada às 01:09:26 UTC em 15/09; os estados
  foram extraídos pela CLI e conferidos na interface. [Estados](airflow_execucao.json).
  A DAG treinou/versionou `.pkl` local; não atualizou o modelo S3 de produção.
- Notebook: 16 células de código executadas sem erro; outputs salvos no
  [arquivo](../notebooks/01_eda.ipynb). Os gráficos foram regenerados pelo
  próprio notebook. Ajustado o limite vertical do gráfico de urgência para
  que a anotação da primeira barra não se sobreponha ao título.
- Produção: `/health` revalidado em 15/09 com `status=ok` e `model=loaded`.
  Release ONNX e benchmark AWS documentados em [deploy_onnx.md](deploy_onnx.md).

## Interpretação dos números

O benchmark HTTP local registrou p50 3,647 ms, p95 5,944 ms e p99 7,506 ms,
com 261,963 req/s. A máquina também executava Airflow; esta validação não é
uma repetição controlada do comparativo sklearn/ONNX.
O painel p95 usa estimativa a partir dos buckets do histograma de inferência,
enquanto o benchmark mede a duração HTTP. Os números não são intercambiáveis.

## Pendências que permanecem

Vídeo STAR e link público, reprodução completa em clone limpo, consolidação
da branch de submissão e envio no portal. A renovação das evidências conclui
a execução do notebook e a revalidação local da DAG; não comprova esses outros passos.
