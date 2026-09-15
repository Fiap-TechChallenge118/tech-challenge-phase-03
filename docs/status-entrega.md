# Auditoria de entrega — 14/09/2026

Fonte: [requisitos oficiais](../.docs/content/tech-challenge.md).
Revisão do código `d447ec1`, TODOs, CI, artefatos, dados oficiais e ambiente AWS.

## Conclusão

A base técnica obrigatória está implementada: API Docker, CI, DAG local,
monitoramento e otimização ONNX com comparativo. **A entrega ainda não está
completa:** falta o vídeo STAR com link acessível, a consolidação da branch de
submissão e a confirmação de envio no portal. A revisão corrigiu descrições
antigas do README e dos TODOs; os limites de validação estão indicados abaixo.

## Requisitos oficiais e evidências

| Requisito / entregável | Situação | Evidência e limite |
|---|---|---|
| API FastAPI em Docker; classificação por REST | Atendido | `app/`, `Dockerfile`, CI com smoke; ONNX real validado no Fargate |
| Decisão textual de nuvem, batch vs real-time | Atendido | README: inferência ECS/ALB; treino batch local; extensão ECS/S3 identificada como pendente |
| Baseline local de latência | Atendido | `docs/latencia_baseline.md` e `docs/benchmark_raw.json` |
| GitHub Actions com ≥2 automações no push | Atendido em develop | Lint, test, infra, build e publish verdes no [run 34908089669](https://github.com/Fiap-TechChallenge118/tech-challenge-phase-03/actions/runs/34908089669) |
| Workflow YAML + histórico semântico | Atendido | `.github/workflows/ci.yml`; commits recentes `feat`, `fix`, `docs` |
| DAG funcional: ingestão → treino → salvamento | Atendido por implementação e evidência registrada | `dags/retrain_triagem_dag.py`; `docs/dag_execucao.png` inspecionado: três tasks success. Execução histórica em 13/09; não reexecutada nesta auditoria |
| Scikit-learn, FastAPI, prometheus-client e Airflow | Atendido | `pyproject.toml`, `Dockerfile.airflow` e requirements da DAG |
| Compose API + Prometheus + Grafana | Atendido no ambiente existente | Três containers ativos; API saudável, target Prometheus UP, Grafana database OK; não equivale a clone limpo |
| Métricas e ≥3 painéis; print/JSON | Atendido | `/metrics`, `monitoring/dashboard.json` com quatro painéis e `docs/grafana_dashboard.png` |
| Classificador treinado; ≥2.000 amostras | Atendido | 14.438 linhas; treino reproduzido com métricas iguais às versionadas |
| Técnica de otimização + modelo otimizado | Atendido | `src/export_onnx.py`; ONNX publicado; paridade 2.888/2.888; [deploy](deploy_onnx.md) |
| Comparativo original vs otimizado | Atendido por evidência registrada | `docs/latencia_comparativo.md`: mesma máquina, p95 −24,6%; benchmark controlado não reexecutado nesta auditoria |
| README com execução clara | Revisado; aceite de clone limpo pendente | Corrigidos modo local, constraints, ONNX, treino local e estado do deploy |
| Vídeo ≤5 minutos, método STAR, link | Pendente obrigatório | Não há link no README nem nos documentos revisados |

Os pesos de avaliação são 20% modelo, 15% CI/CD, 15% Airflow, 20%
monitoramento, 15% README e 15% vídeo. Esta auditoria não estima nota nem
considera evidência histórica equivalente a uma nova execução.

## Achados e pendências

### Antes de submeter

1. **Dev A:** gravar/publicar o vídeo STAR, inserir o link e verificar duração
   e acesso sem autenticação. Demonstrar CI, DAG, dashboard e comparativo.
2. **Time:** definir a branch/link final. O repositório é público, mas a branch
   padrão é `master`; `develop` estava 29 commits à frente na revisão de
   `d447ec1`. Não existe `main` remota. O CI só valida push/PR para `develop`.
   Se houver integração em `master`, preparar os gatilhos/checks para essa
   branch antes do merge. Não houve merge nem alteração de proteção nesta auditoria.
3. **Dev A + time:** reproduzir as instruções em clone limpo, incluindo dados,
   treino/exportação, Compose e Airflow. A API usa mock quando o artefato falta;
   a demonstração precisa mostrar `model=loaded`.
4. **Time:** confirmar prazo institucional, enviar o link no portal e registrar
   recebimento. Não há evidência desses passos no repositório.

### Correções de documentação feitas nesta revisão

- TODOs reconciliados com DAG, EDA, comparativo, CI e deploy existentes.
- README descreve a DAG local entregue; ECS/S3 para retreino permanece extensão.
- Modelo ONNX e versão de produção registrados; referências antigas a sklearn
  em produção e ONNX ainda não implementado foram removidas do estado atual.
- EDA: 3.211 repetições de texto, **2.929 textos com múltiplos rótulos** e
  **988 textos em comum entre treino e teste oficiais**. Não há linhas inteiras
  duplicadas. Corrigidas as alegações de duplicatas apenas na mesma classe e
  de que estratificação elimina vazamento. As métricas reproduzem o split
  oficial; não demonstram generalização para textos inteiramente inéditos.

### Metas internas adicionais; não exigidas pelo enunciado

- **DAG → ECS → S3:** não implementada. A DAG usa PythonOperator/BashOperator,
  grava localmente e não exporta ONNX. A Task Definition de treino existe,
  mas não fornece ingestão/upload automáticos. A DAG local satisfaz o exemplo
  de pipeline simples exigido pelo enunciado.
- **Notebook EDA:** presente, com 16 células de código, todas sem execution_count
  e sem outputs. Executar e salvar evidência de execução continua pendente.
- **Branch protection e acessos do time:** marcações antigas não foram tratadas
  como confirmação atual; revisar a configuração da branch final.
- **Segredos:** busca por histórico de `*.env`, `*.key`, `*.tfstate*` não retornou
  arquivos. É verificação limitada por nomes, não auditoria completa de segredos.
- **Encerramento AWS:** janela até 26/09; procedimento documentado, responsável
  nominal e execução ao final ainda pendentes. Tags não desligam recursos.

## Validações desta revisão

- 17 testes e Ruff aprovados; Terraform fmt/validate e Compose válidos.
- CI completo aprovado; imagem por digest publicada no ECR.
- Retreino reproduzido; exportação/paridade completa aprovada.
- Deploy ECS revisão 3 concluído; plan posterior sem diferenças.
- Endpoints públicos e cinco predições equivalentes ao sklearn aprovados.
- Benchmark público: 100 chamadas, p95 197,117 ms incluindo rede; não comparar
  como ganho isolado com o baseline de outro dia.
- Stack local existente: Prometheus UP, Grafana OK; imagem local anterior
  preservada. Runtime ONNX atual verificado em produção.

Evidência de produção e rollback: [deploy_onnx.md](deploy_onnx.md).
Checklists atuais: [geral](../.docs/TODO/geral.md),
[Dev A](../.docs/TODO/dev-a-alexandre.md),
[Dev B](../.docs/TODO/dev-b-matheus-santos.md),
[Dev C](../.docs/TODO/dev-c-matheus-ferreira.md).
