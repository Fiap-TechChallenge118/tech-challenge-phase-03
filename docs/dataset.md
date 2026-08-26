# Dataset — Medical Abstracts TC Corpus

## Identificação

| Campo | Valor |
|---|---|
| Nome | Medical Abstracts TC Corpus |
| Fonte (Kaggle) | https://www.kaggle.com/datasets/saharalaa/medical-abstracts-tc-corpus |
| Fonte original (GitHub) | https://github.com/sebischair/Medical-Abstracts-TC-Corpus |
| Disponível também em | https://huggingface.co/datasets/TimSchopf/medical_abstracts |
| Licença | Creative Commons (ver repositório original) |
| Tarefa | Classificação de texto (multi-classe, 5 categorias) |
| Idioma | Inglês |

## Descrição

Coleção de resumos (abstracts) de artigos científicos da área médica, rotulados em 5 classes de condições clínicas. O corpus foi criado e publicado pelo grupo de pesquisa SEBIS (Technical University of Munich) como parte do trabalho:

> Schopf, T., Braun, D., & Matthes, F. (2023). **Evaluating Unsupervised Text Classification: Zero-Shot and Similarity-Based Approaches**. *Proceedings of the 2022 6th International Conference on Natural Language Processing and Information Retrieval (NLPIR '22)*, pp. 6–15. ACM. https://doi.org/10.1145/3582768.3582795

## Estrutura dos Arquivos

| Arquivo | Descrição |
|---|---|
| `medical_tc_train.csv` | Partição de treino — 11.550 amostras |
| `medical_tc_test.csv` | Partição de teste — 2.888 amostras |
| `medical_tc_labels.csv` | Mapeamento `condition_label` (inteiro) → nome da classe |

### Colunas dos CSVs de treino/teste

| Coluna | Tipo | Descrição |
|---|---|---|
| `medical_abstract` | string | Texto do resumo do artigo médico (entrada do modelo) |
| `condition_label` | int (1–5) | Rótulo numérico da classe |

### Arquivo de labels (`medical_tc_labels.csv`)

| `condition_label` | Classe original |
|---|---|
| 1 | Neoplasms |
| 2 | Digestive system diseases |
| 3 | Nervous system diseases |
| 4 | Cardiovascular diseases |
| 5 | General pathological conditions |

## Distribuição de Amostras

| Classe original | Treino | Teste | Total |
|---|---|---|---|
| Neoplasms | 2.530 | 633 | **3.163** |
| Digestive system diseases | 1.195 | 299 | **1.494** |
| Nervous system diseases | 1.540 | 385 | **1.925** |
| Cardiovascular diseases | 2.441 | 610 | **3.051** |
| General pathological conditions | 3.844 | 961 | **4.805** |
| **Total** | **11.550** | **2.888** | **14.438** |

> O dataset é **desbalanceado**: "General pathological conditions" representa ~33% das amostras enquanto "Digestive system diseases" representa ~10%. O pipeline de treino usa `class_weight="balanced"` para compensar.

## Mapeamento para as 3 Classes do Projeto

O challenge exige 3 classes de urgência (`normal`, `atenção`, `urgente`). As 5 classes originais são mapeadas conforme a criticidade clínica esperada:

| Classe original | `condition_label` | Classe do projeto | Justificativa |
|---|---|---|---|
| General pathological conditions | 5 | `normal` | Condições gerais, tipicamente menor urgência imediata |
| Digestive system diseases | 2 | `normal` | Condições gastrointestinais geralmente não emergenciais |
| Nervous system diseases | 3 | `atenção` | Condições neurológicas exigem monitoramento próximo |
| Neoplasms | 1 | `atenção` | Neoplasias requerem acompanhamento oncológico prioritário |
| Cardiovascular diseases | 4 | `urgente` | Condições cardiovasculares têm maior risco de emergência |

> **Nota:** Este mapeamento é uma simplificação para fins do challenge. Em um sistema clínico real, a classificação de urgência dependeria de critérios clínicos muito mais granulares.

## Como Obter o Dataset

### Opção 1 — Kaggle CLI
```bash
# Requer autenticação: ~/.kaggle/kaggle.json
kaggle datasets download -d saharalaa/medical-abstracts-tc-corpus -p data/raw/ --unzip
```

### Opção 2 — Download direto do GitHub
```bash
# Arquivos CSV disponíveis diretamente no repositório original
curl -L https://raw.githubusercontent.com/sebischair/Medical-Abstracts-TC-Corpus/main/medical_tc_train.csv \
     -o data/raw/medical_tc_train.csv

curl -L https://raw.githubusercontent.com/sebischair/Medical-Abstracts-TC-Corpus/main/medical_tc_test.csv \
     -o data/raw/medical_tc_test.csv

curl -L https://raw.githubusercontent.com/sebischair/Medical-Abstracts-TC-Corpus/main/medical_tc_labels.csv \
     -o data/raw/medical_tc_labels.csv
```

### Opção 3 — Hugging Face
```python
from datasets import load_dataset
ds = load_dataset("TimSchopf/medical_abstracts")
ds["train"].to_csv("data/raw/medical_tc_train.csv", index=False)
ds["test"].to_csv("data/raw/medical_tc_test.csv", index=False)
```

> Os arquivos `data/raw/` estão no `.gitignore` e **não são versionados** no repositório.

## Adequação ao Challenge

| Requisito | Atendido? | Detalhe |
|---|---|---|
| ≥ 2.000 amostras | ✅ | 14.438 amostras no total |
| Coluna de texto (laudo/sintoma) | ✅ | `medical_abstract` |
| Coluna de target (classificação) | ✅ | `condition_label` (mapeado para 3 classes) |
| Dataset público | ✅ | GitHub + Kaggle + Hugging Face |
| Licença compatível | ✅ | Creative Commons |

## Citação

```bibtex
@inproceedings{10.1145/3582768.3582795,
  author    = {Schopf, Tim and Braun, Daniel and Matthes, Florian},
  title     = {Evaluating Unsupervised Text Classification: Zero-Shot and Similarity-Based Approaches},
  year      = {2023},
  isbn      = {9781450397629},
  publisher = {Association for Computing Machinery},
  address   = {New York, NY, USA},
  url       = {https://doi.org/10.1145/3582768.3582795},
  doi       = {10.1145/3582768.3582795},
  booktitle = {Proceedings of the 2022 6th International Conference on Natural Language Processing and Information Retrieval},
  pages     = {6–15},
  series    = {NLPIR '22}
}
```
