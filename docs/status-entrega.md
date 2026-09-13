# Status de entrega — 13/09/2026

## Dev B — etapas 5, 6, 8 e 10

Implementação concluída: Docker multi-stage/não-root, baseline real, GitHub
Actions com publicação ECR, Compose com Prometheus/Grafana e infraestrutura
Terraform com inferência ECS Fargate atrás de ALB. README atualizado nas seções
sob responsabilidade B; captura do CI em `ci_execucao.png`.

Validação nesta revisão:

- 16 testes passaram (10 API, 3 benchmark, 3 validador de modelo).
- Ruff, actionlint, Terraform fmt/validate (infra e bootstrap) passaram.
- Compose retomado com três serviços ativos; API saudável, UID 10001;
  Prometheus target UP e configuração aprovada pelo promtool.
- API local e ALB retornaram `model=loaded`; `/predict` público respondeu
  HTTP 200 com classe, confiança e tempo; `/docs` público respondeu HTTP 200.
- CI do commit `8ab33fa`: [run 34726456994](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/runs/34726456994),
  cinco jobs concluídos com sucesso, incluindo publicação.
- Captura do Actions obtida da página pública e inspecionada visualmente.

A sessão AWS CLI expirou: não foi possível consultar novamente o ECS nem
executar plan com refresh. Evidências de apply/state e digest de 12/09 continuam
históricas; os endpoints públicos foram revalidados em 13/09. Não foi necessário
alterar recursos AWS para este fechamento.

## O que falta para finalizar o projeto

| Responsável | Entrega restante | Evidência de conclusão esperada |
|---|---|---|
| Dev C — etapa 7 | Implementar DAG Airflow com ingestão, treino e salvamento; integrar S3/ECS conforme contrato entregue | DAG executada de ponta a ponta, modelo salvo/versionado no S3 e `docs/dag_execucao.png` |
| Dev C — etapa 9 | Exportar modelo otimizado, validar paridade e medir nas mesmas condições do baseline | Exportador, artefato, comparação de 100 amostras e `docs/latencia_comparativo.md` com p50/p95/p99, throughput, tamanho e ganho |
| Dev A + C | Validar integração ONNX na API | Testes reais de classe/confiança e pré-processamento equivalentes ao sklearn |
| Dev A — etapa 11 | Consolidar README, preencher visão geral e reconciliar contrato de classes | Documentação coerente e comandos reproduzidos de um clone limpo |
| Dev A — etapa 11 | Gravar/publicar vídeo STAR de até 5 minutos | Link acessível e inserido no README |
| Time | Revisar/integrar mudanças na branch final e submeter | CI verde, repositório público, PRs revisados e recebimento no portal |

Achados que afetam a integração:

- `dags/` não contém DAG; não há `src/export_onnx.py`, `model.onnx`, comparativo
  de latência nem captura Airflow neste checkout.
- A Task Definition já entrega `DATA_BUCKET`, `DATA_KEY`, `MODEL_BUCKET` e
  `MODEL_KEY`, mas o treino atual não faz automaticamente download/upload S3.
  O `--help` no Fargate comprova infraestrutura, não execução de treinamento.
- A identidade que executar Airflow precisa das permissões de RunTask,
  DescribeTasks e PassRole descritas no guia; sua identidade ainda deve ser
  definida na integração da etapa 7.
- `_predict_onnx` em `app/model_loader.py` devolve o rótulo diretamente; um
  export das classes numéricas 1–5 precisará do mesmo mapeamento de urgência
  utilizado por sklearn e da seleção correta da probabilidade.
- O README diz que cinco condições substituem três urgências, enquanto a API
  sklearn ainda mapeia cinco condições para três urgências. A equipe deve
  reconciliar essa descrição com o contrato escolhido antes da entrega.
- EDA e métricas já existem; checklists A/C/geral contêm anotações antigas e
  precisam ser reconciliados com as evidências, sem refazer trabalho concluído.
- O CI publica somente na `develop`; ao integrar na branch final, revisar os
  gatilhos de validação. Não assumir `main`: os documentos e referências antigas
  também mencionam `master`.

## Operação após a demo

Janela AWS até **26/09/2026**. Definir o responsável pelo encerramento;
`enable_inference=false` com plan/apply remove Service/ALB e preserva buckets.
Tags não desligam recursos automaticamente. Procedimento completo, rollback
e contrato de integração: [guia Dev B](dev-b-operacao.md).
