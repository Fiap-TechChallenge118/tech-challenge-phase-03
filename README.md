# Triagem Médica — Sistema de Classificação de Urgência

<!-- Badge do CI será adicionado na ETAPA 6 -->
<!-- ![CI](https://github.com/ORG/REPO/actions/workflows/ci.yml/badge.svg) -->

> Classificação automática de urgência de laudos médicos (`normal` / `atenção` / `urgente`) via API REST, com pipeline de treino orquestrado, monitoramento e deploy em produção na AWS.

## Visão Geral

<!-- Preencher na ETAPA 11: o que o sistema faz, quem usa, visão de alto nível. -->

## Decisão Arquitetural

<!-- Preencher na ETAPA 3 (e revisar na ETAPA 11): análise batch vs real-time,
     justificativa de ECS Fargate + ALB para inferência e ECS Task para treino,
     diagrama Client → ALB → ECS Fargate Service → model.onnx (do S3). -->

## Pré-requisitos

<!-- Python 3.11+, Docker, Docker Compose, Terraform, credenciais AWS. -->

## Como Executar

### Desenvolvimento local

<!--
pip install -e ".[dev]"
uvicorn app.main:app --reload
-->

### Docker isolado

<!--
docker build -t triagem-api .
docker run -p 8000:8000 triagem-api
-->

### Stack completa (Docker Compose)

<!--
docker compose up
-->

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
