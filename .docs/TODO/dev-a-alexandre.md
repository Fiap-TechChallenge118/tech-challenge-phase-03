# TODO — Dev A: Alexandre Araújo

Revisão de 14/09/2026. Responsável por fundação, API, testes, README e vídeo.
Fonte: [requisitos oficiais](../content/tech-challenge.md).
Evidências: [auditoria](../../docs/status-entrega.md).

## ETAPA 0 — Fundação

- [x] Repositório público e estrutura de código, dados, modelos, testes e infraestrutura.
- [x] `pyproject.toml`, `.gitignore`, `.dockerignore`, `.env.example`, README e CONTRIBUTING.
- [x] Dependências de runtime/dev fixadas e constraints ONNX disponíveis.
- [x] Histórico de commits semânticos.
- [ ] Confirmar proteção e permissões na branch de entrega; o padrão remoto atual é `master`, e não `main`.
- [ ] Consolidar processo de contribuição/PR com a decisão de trabalhar em `develop`.

Convites, comunicações internas e revisão de PR não foram inferidos da existência
do código; confirmar administrativamente quando necessário.

## ETAPA 3 — API

- [x] `PredictRequest`: texto não vazio, até 5.000 caracteres.
- [x] `PredictResponse`: classe, confiança entre 0 e 1, tempo em ms.
- [x] Startup com download S3 ou artefato local; cache em memória.
- [x] ONNX como padrão; sklearn opcional; fallback mock identificado no health.
- [x] Pré-processamento e mapeamento das cinco condições para três urgências nos dois runtimes.
- [x] `/predict`, `/health`, `/metrics` e Swagger funcionando.
- [x] Logs de carregamento e inferência; métricas Counter/Histogram.
- [x] Decisão real-time + ECS/ALB no README.
- [x] API ONNX real validada no Fargate; cinco predições equivalentes ao sklearn.

## ETAPA 4 — Testes e lint

- [x] Ruff sem erros e pytest aprovado localmente e no CI.
- [x] Testes de health, resposta válida, campos obrigatórios, texto vazio/branco e limite de tamanho.
- [x] Fixture mock independente de S3 e do artefato de produção.
- [x] Teste adicional com ONNX real gerado durante o teste; valida classe/confiança e runtime padrão.
- [x] Suíte atual: 11 testes em `tests/`, mais 6 nos scripts (17 no CI).
- [x] Comandos de instalação, lint e testes documentados.

## ETAPA 11 — Consolidação e vídeo

- [x] README com visão geral, arquitetura real, execução, CI, monitoramento e URL de produção.
- [x] Atualização do estado ONNX e comparação de latência; links das evidências.
- [x] Distinção entre DAG local entregue e integração futura ECS/S3.
- [ ] Reproduzir todos os comandos em clone limpo (incluindo obtenção dos dados/modelo).
- [ ] Revisar todos os links públicos sem autenticação.
- [ ] Confirmar branch final com o time; preparar CI para ela caso seja `master`.
- [ ] Gravar Situation: problema e importância da resposta rápida (~45 s).
- [ ] Gravar Task: requisitos de API, latência, CI/CD, monitoramento e retreino (~45 s).
- [ ] Gravar Action: arquitetura, Actions, DAG, Grafana e otimização (~2 min).
- [ ] Gravar Result: comparativo de latência, demo e lições (~45 s).
- [ ] Publicar vídeo de até 5 minutos; testar acesso e inserir link no README.
- [ ] Concluir revisão/integração final com o time e confirmar submissão no portal.

**Etapa 11 ainda aberta.** Não foi encontrado link de vídeo no conteúdo revisado.

## Apoio à ETAPA 8

- [x] `/metrics` exposto; contagem de predições, latência e erros de inferência.
- [x] Prometheus local com target UP e dashboard provisionado com quatro painéis.
