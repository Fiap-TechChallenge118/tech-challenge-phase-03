# Comparativo de latência — sklearn (.pkl) vs ONNX Runtime (.onnx)

**Etapa de otimização de latência (ONNX) — Dev C (Matheus Ferreira)** · 13/09/2026

## Objetivo

Exportar o pipeline treinado para ONNX e medir o ganho do ONNX Runtime em
relação ao `.pkl` (sklearn), mantendo **paridade de predição**.

## Retreino para compatibilidade ONNX

Durante a exportação, o `skl2onnx 1.17` apresentou duas fidelidades imperfeitas
que causavam 1% de divergência (2/200 amostras) em relação ao sklearn:

1. **`sublinear_tf=True`** → o ONNX implementa `log(tf+1)`, enquanto o sklearn
   usa `1+log(tf)` (divergência em documentos com termos repetidos, `tf≥2`).
2. **`token_pattern` default** (`\b\w\w+\b`) → o ONNX o reescreve como
   `[a-zA-Z0-9_]+` com `mincharnum=1`, perdendo a regra de "mínimo 2 caracteres".

Para garantir **paridade exata**, o modelo foi retreinado com
`sublinear_tf=False` e `token_pattern=r"[a-zA-Z0-9_]+"` (1+ caractere), idêntico
ao comportamento do ONNX. A mudança é neutra em qualidade — na verdade,
melhorou levemente o holdout:

| Métrica (holdout, 2.888 laudos) | Baseline (FASE 3) | Retreinado (ONNX-compatível) |
|---|---:|---:|
| Acurácia | 0,604 | **0,608** |
| Macro-F1 | 0,605 | **0,611** |

## Paridade de predição

Comparação classe-a-classe entre `model.pkl` (sklearn) e `model.onnx` (ONNX
Runtime) sobre as 2.888 amostras do test set oficial:

| Amostras | Classes idênticas | Divergências | max\|Δ proba\| |
|---:|---:|---:|---:|
| 2.888 | 2.888 (100%) | 0 | 2,2×10⁻⁷ |

A diferença máxima de probabilidade é da ordem do arredondamento `float32`,
confirmando paridade exata.

> O artefato ONNX exporta apenas `tfidf → clf`; o pré-processamento (regex +
> stopwords) permanece em Python, aplicado antes da inferência — o mesmo fluxo
> validado pela checagem de paridade e usado por `app/model_loader.py`.

## Metodologia do benchmark

Mesmo protocolo da Etapa 5 (`scripts/benchmark.py`): 500 requisições HTTP
sequenciais com conexão persistente, 20 de aquecimento, três textos fixos,
`/health` com `model=loaded`, timeout de 10 s. Percentis por interpolação
linear; throughput = N / tempo total.

- **Máquina (esta execução):** Windows 11 Pro, Docker Desktop, Linux x86_64
  (WSL2), Python 3.11.
- `.pkl` e `.onnx` medidos na **mesma máquina e configuração**, alternando
  apenas `USE_ONNX` e reiniciando a API (contadores Prometheus zerados).

## Resultados

| Métrica | `.pkl` (sklearn) | `.onnx` (ONNX Runtime) | Ganho |
|---|---:|---:|---:|
| p50 (ms) | 2,340 | 1,776 | **−24,1%** |
| p95 (ms) | 3,119 | 2,353 | **−24,6%** |
| p99 (ms) | 3,652 | 3,535 | −3,2% |
| Throughput (req/s) | 411,8 | 524,6 | **+27,4%** |
| Tamanho do artefato | 10,98 MB (10.984.292 B) | 8,74 MB (8.742.267 B) | **−20,4%** |

O ONNX Runtime reduz a latência mediana e p95 em ~24% e eleva o throughput em
~27%. O p99 é a métrica mais ruidosa com 500 amostras (3,2%): a cauda é dominada
pelo transporte HTTP, não pela inferência.

## Referência — baseline FASE 3 (Etapa 5)

| Medida | Resultado |
|---|---|
| `.pkl` p50 / p95 / p99 (macOS ARM64) | 1,697 / 2,164 / 2,570 ms |
| Throughput (macOS ARM64) | 575,988 req/s |

Os números absolutos da Etapa 5 foram medidos em macOS ARM64 e não são
diretamente comparáveis a esta execução (Windows/WSL2 x86_64); por isso o
comparativo acima mede `.pkl` e `.onnx` na mesma máquina. O ganho relativo do
ONNX é o resultado relevante.

## Conclusão

A exportação ONNX atingiu **paridade exata** (2.888/2.888) e entregou ganho
consistente de latência: **−24% no p50/p95, +27% de throughput** e artefato
**20% menor**. O custo foi retreinar com uma configuração de TF-IDF
ONNX-compatível, que — além de eliminar a divergência — elevou levemente o
macro-F1 do holdout (0,605 → 0,611). Recomenda-se operar com `USE_ONNX=true`
em produção.
