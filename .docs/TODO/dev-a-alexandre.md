# TODO — Dev A: Alexandre Araújo

**Eixo de responsabilidade:** API, Testes e Documentação
**Fases cobertas:** FASE 2 → FASE 4 → FASE 10
**Peso na nota (PDF):** Documentação 15% + Vídeo STAR 15% = **30%**

---

## FASE 2 — API FastAPI de triagem + decisão arquitetural de nuvem

**Etapa PDF:** Etapa 1 — Decisão Arquitetural e API Inicial

**Objetivo:** Construir a API REST de triagem que recebe o texto do laudo e devolve a classificação de urgência, e documentar a decisão de arquitetura de deploy em nuvem.

**Entregável:** `app/main.py` funcional + seção "Decisão Arquitetural" preenchida no `README.md`.

**Dependências:**
- Requer: FASE 0 concluída (estrutura de pastas, `requirements.txt`, branch strategy)
- Requer: `models/model.pkl` da FASE 1 — **até estar disponível, usar um mock que retorna classe fixa**
- Bloqueia: FASE 4 (testes dependem da API existir)

**Branch:** `fase-2-api-fastapi`

---

### Checklist

#### Configuração inicial
- [ ] Criar a branch `fase-2-api-fastapi` a partir de `main`
- [ ] Verificar que `fastapi` e `uvicorn` estão fixados no `requirements.txt`
- [ ] Criar o arquivo `app/__init__.py` (pode ficar vazio)

#### Schemas Pydantic (`app/schemas.py`)
- [ ] Criar classe `PredictRequest` com campo `texto: str`
  - [ ] Validar que `texto` não é vazio (usar `@validator` ou `Field(min_length=1)`)
  - [ ] Validar tamanho máximo (sugestão: `max_length=5000`)
- [ ] Criar classe `PredictResponse` com campos:
  - `classe: str` (valor: `"normal"`, `"atenção"` ou `"urgente"`)
  - `confianca: float` (probabilidade da classe predita, entre 0.0 e 1.0)
  - `tempo_ms: float` (tempo de inferência em milissegundos)

#### Carregamento do modelo (`app/model_loader.py`)
- [ ] Criar função `load_model()` que carrega `models/model.pkl` com `joblib.load()`
- [ ] O carregamento deve ocorrer **uma única vez** no startup da aplicação (não a cada request)
- [ ] Se `model.pkl` não existir, retornar um mock que sempre responde `{"classe": "normal", "confianca": 1.0}`
- [ ] Logar (com `logging`) qual modo está ativo: modelo real ou mock

#### Endpoints (`app/main.py`)
- [ ] Instanciar `app = FastAPI(title="Triagem Médica API", version="1.0.0")`
- [ ] Usar evento `@app.on_event("startup")` para chamar `load_model()` e guardar na instância
- [ ] Implementar `POST /predict`:
  - [ ] Receber `PredictRequest`, chamar o modelo, retornar `PredictResponse`
  - [ ] Medir o tempo de inferência com `time.perf_counter()` e preencher `tempo_ms`
  - [ ] Lançar `HTTPException(status_code=422)` se o texto vier vazio após strip
- [ ] Implementar `GET /health`:
  - [ ] Retornar `{"status": "ok", "model": "loaded"}` (ou `"mock"` se estiver em modo mock)
  - [ ] HTTP 200 em ambos os casos
- [ ] Configurar logging estruturado: usar `logging.getLogger(__name__)`, **sem nenhum `print()`**
- [ ] Adicionar exemplo de request no schema Pydantic para aparecer no Swagger (`/docs`)

#### Análise arquitetural no README
- [ ] Abrir `README.md` e localizar a seção "Decisão Arquitetural" (criada na FASE 0)
- [ ] Escrever análise **batch vs real-time** para o contexto de triagem clínica:
  - [ ] Explicar por que triagem hospitalar exige resposta síncrona (real-time), não batch
  - [ ] Citar consequência clínica de atraso (risco ao paciente)
- [ ] Escolher e justificar o provedor de nuvem e serviço gerenciado (ex.: AWS ECS Fargate, Azure Container Apps ou Google Cloud Run)
  - [ ] Justificar com base em: custo, simplicidade de deploy de container, escalabilidade
- [ ] Incluir diagrama textual simples da arquitetura (ex.: `Client → API Gateway → Container → Model`)

#### Validação local
- [ ] Subir a API localmente: `uvicorn app.main:app --reload`
- [ ] Acessar `http://localhost:8000/docs` e verificar que os schemas aparecem corretamente
- [ ] Testar `POST /predict` pelo Swagger com um exemplo de laudo preenchido
- [ ] Testar `GET /health` e confirmar retorno 200
- [ ] Confirmar que nenhum `print()` aparece no output — apenas logs estruturados

#### Finalização
- [ ] Commitar com mensagem semântica: `feat(api): add /predict and /health endpoints`
- [ ] Abrir PR de `fase-2-api-fastapi` → `main` e solicitar revisão

---

### ✅ Definition of Done — FASE 2
- `POST /predict` retorna `{classe, confianca, tempo_ms}` para um laudo válido
- `GET /health` retorna HTTP 200
- Schemas Pydantic rejeitam texto vazio com HTTP 422
- Nenhum `print()` no código — apenas `logging`
- Seção "Decisão Arquitetural" no README com análise batch vs real-time e justificativa de provedor
- PR aberto e revisado antes do merge

---

---

## FASE 4 — Testes automatizados e qualidade de código

**Etapa PDF:** Etapa 2 — CI/CD e Pipeline Automatizado

**Objetivo:** Criar a suíte de testes pytest e configurar o lint, para que a FASE 5 (CI/CD) apenas automatize o que já funciona localmente.

**Entregável:** Pasta `tests/` com todos os testes passando + `ruff` configurado no `pyproject.toml` sem erros em `app/` e `src/`.

**Dependências:**
- Requer: FASE 2 concluída (`app/main.py` existindo)
- Bloqueia: FASE 5 (o workflow CI/CD chama exatamente os comandos definidos aqui)

**Branch:** `fase-4-testes-lint`

---

### Checklist

#### Configuração do lint (`pyproject.toml`)
- [ ] Criar (ou abrir) `pyproject.toml` na raiz do repositório
- [ ] Adicionar seção `[tool.ruff]` com:
  ```toml
  [tool.ruff]
  line-length = 88
  select = ["E", "F", "W", "I"]
  exclude = ["dags/", "data/"]
  ```
- [ ] Rodar `ruff check app/ src/` e corrigir **todos** os erros antes de seguir
- [ ] Confirmar saída limpa: `All checks passed.`

#### Configuração do pytest (`pyproject.toml`)
- [ ] Adicionar seção `[tool.pytest.ini_options]`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  ```
- [ ] Criar `tests/__init__.py` (vazio)

#### Fixture com modelo mock (`tests/conftest.py`)
- [ ] Criar `tests/conftest.py` com fixture `client`:
  - [ ] Fazer override da dependência de modelo com um mock que retorna `("normal", 0.95)`
  - [ ] Instanciar `TestClient(app)` do FastAPI
  - [ ] **Os testes não podem depender do `models/model.pkl` real**

#### Testes de healthcheck (`tests/test_health.py`)
- [ ] `test_health_returns_200`: GET `/health` retorna status code 200
- [ ] `test_health_body_has_status_key`: resposta contém chave `"status"`

#### Testes do endpoint de predição (`tests/test_predict.py`)
- [ ] `test_predict_valid_text_returns_valid_class`:
  - [ ] POST `/predict` com laudo válido (ex.: `"Paciente com dor torácica intensa"`)
  - [ ] Resposta HTTP 200
  - [ ] Campo `classe` é um de `["normal", "atenção", "urgente"]`
  - [ ] Campo `confianca` é float entre 0.0 e 1.0
  - [ ] Campo `tempo_ms` é float >= 0
- [ ] `test_predict_empty_text_returns_422`:
  - [ ] POST `/predict` com `{"texto": ""}` retorna HTTP 422
- [ ] `test_predict_blank_text_returns_422`:
  - [ ] POST `/predict` com `{"texto": "   "}` (só espaços) retorna HTTP 422
- [ ] `test_predict_missing_field_returns_422`:
  - [ ] POST `/predict` com payload `{}` (sem campo `texto`) retorna HTTP 422
- [ ] `test_predict_text_too_long_returns_422`:
  - [ ] POST `/predict` com texto de 6000 caracteres retorna HTTP 422

#### Execução local e validação
- [ ] Rodar `pytest -v` e confirmar **100% de testes passando**
- [ ] Rodar `ruff check app/ src/` e confirmar zero erros
- [ ] Anotar os comandos exatos usados (serão replicados no workflow da FASE 5):
  - `ruff check app/ src/`
  - `pytest -v`

#### Finalização
- [ ] Commitar: `test(api): add pytest suite and ruff lint config`
- [ ] Abrir PR de `fase-4-testes-lint` → `main`

---

### ✅ Definition of Done — FASE 4
- `pytest -v` passa com 100% (mínimo 7 testes)
- `ruff check app/ src/` retorna zero erros
- Nenhum teste usa o `model.pkl` real — todos usam fixture mock
- Comandos de lint e teste documentados (serão usados pelo Dev B na FASE 5)
- PR aberto e revisado

---

---

## FASE 10 — Consolidação final: README e vídeo STAR

**Etapa PDF:** (sem etapa específica — entregável transversal)

**Objetivo:** Garantir que o README está completo, coerente e navegável, e produzir o vídeo STAR de até 5 minutos demonstrando o projeto.

**Entregável:** `README.md` final + link do vídeo publicado e funcional.

**Dependências:**
- Requer: todas as fases anteriores concluídas (especialmente FASE 8 para os números de latência e FASE 9 para a URL pública)
- Bloqueia: submissão final

**Branch:** `fase-10-readme-video`

---

### Checklist

#### Revisão e consolidação do README
- [ ] Abrir `README.md` e percorrer todas as seções criadas nas fases anteriores:
  - [ ] Seção "Decisão Arquitetural" (escrita na FASE 2) — verificar se está atualizada com o deploy real da FASE 9
  - [ ] Seção "Como executar" — testar os comandos do zero em uma pasta limpa
  - [ ] Seção "Resultados de Latência" — colar tabela do `docs/latencia_comparativo.md` (FASE 8)
  - [ ] Seção "CI/CD" — incluir badge do workflow e link para o Actions
  - [ ] Seção "Monitoramento" — incluir print do dashboard Grafana
  - [ ] Seção "Deploy em Produção" — incluir URL pública (FASE 9) e passo a passo
  - [ ] Seção "Vídeo" — inserir link do vídeo publicado
- [ ] Verificar que todos os comandos do README estão funcionando (copiar e colar, não memorizar)
- [ ] Revisar ortografia e clareza — o README será lido pela banca avaliadora

#### Seção "Como executar" — garantir os 3 modos de execução documentados
- [ ] **Modo local (desenvolvimento):**
  ```bash
  pip install -r requirements.txt
  uvicorn app.main:app --reload
  ```
- [ ] **Modo Docker isolado:**
  ```bash
  docker build -t triagem-api .
  docker run -p 8000:8000 triagem-api
  ```
- [ ] **Modo stack completa (API + Prometheus + Grafana):**
  ```bash
  docker compose up
  ```

#### Roteiro do vídeo STAR
- [ ] **S — Situation (≈ 45s):** Descrever o problema clínico — hospital precisa de triagem automática de laudos, volume alto, risco de atraso
- [ ] **T — Task (≈ 45s):** Requisitos técnicos — latência aceitável, CI/CD funcional, monitoramento com Grafana, retreino com Airflow
- [ ] **A — Action (≈ 2min):** Mostrar na tela:
  - [ ] Arquitetura escolhida (diagrama do README)
  - [ ] Pipeline CI/CD rodando verde no GitHub Actions
  - [ ] `docker compose up` subindo a stack e Grafana com dados
  - [ ] DAG Airflow executada com sucesso (print do grafo verde)
  - [ ] Comparativo de latência sklearn vs ONNX (tabela do `docs/`)
- [ ] **R — Result (≈ 45s):** Apresentar os números — latência p95, ganho com ONNX, URL pública funcionando, lições aprendidas
- [ ] Revisar roteiro com o time antes de gravar

#### Gravação e publicação
- [ ] Gravar o vídeo com duração **máxima de 5 minutos** (requisito obrigatório do PDF)
- [ ] Publicar no YouTube (não listado ou público) ou outra plataforma indicada pela instituição
- [ ] Testar o link em **aba anônima** e confirmar que está acessível sem login
- [ ] Inserir o link no README

#### Finalização
- [ ] Commitar: `docs: finalize README and add video link`
- [ ] Abrir PR de `fase-10-readme-video` → `main`
- [ ] Confirmar com o time que o repositório está público e acessível

---

### ✅ Definition of Done — FASE 10
- README com todas as seções preenchidas, comandos testados e sem links quebrados
- Link do vídeo acessível em aba anônima
- Vídeo com duração ≤ 5 minutos seguindo o método STAR
- Repositório público com todos os merges concluídos

---

## ⚠️ Pontos em aberto — Dev A

- [ ] **Provedor de nuvem:** qual serviço usar na análise arquitetural da FASE 2? Confirmar com Dev B (que fará o deploy real na FASE 9) para garantir que a análise e o deploy sejam coerentes.
- [ ] **Limite de tamanho do texto:** o PDF não especifica. Valor sugerido aqui: 5.000 caracteres. Confirmar com o time.
- [ ] **Plataforma do vídeo:** o PDF não especifica. Confirmar com a instituição se YouTube é aceito ou se há portal específico para submissão.
- [ ] **Apoio na instrumentação do `/metrics`:** a FASE 7 (Dev B) requer que a API exponha `/metrics` com `prometheus_client`. Alinhar com Dev B quem escreve esse código — o plan.md coloca como responsabilidade do Dev B com "apoio do Dev A".
