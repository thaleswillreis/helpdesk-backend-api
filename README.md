# Helpdesk Backend API

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Celery](https://img.shields.io/badge/Celery-5.4-37814A)
![License](https://img.shields.io/badge/license-MIT-green)

Backend de um sistema de abertura e gestão de chamados (Helpdesk/ITSM), desenvolvido em **Python** com **FastAPI**, seguindo uma arquitetura em camadas (Models, Services, Controllers).

## Sobre o projeto

O objetivo deste projeto de portfólio é desenvolver, de forma realista, o backend de uma ferramenta de service desk/ITSM completa — cobrindo desde o registro de chamados até automação, base de conhecimento, catálogo de serviços, CMDB e indicadores de gestão. O desenvolvimento seguiu um roteiro em 10 fases (Épicos e Histórias de Usuários), executadas de forma incremental e orientada a decisões deliberadas de arquitetura.

## Sumário

- [Helpdesk Backend API](#helpdesk-backend-api)
  - [Sobre o projeto](#sobre-o-projeto)
  - [Sumário](#sumário)
  - [Tecnologias Utilizadas](#tecnologias-utilizadas)
  - [Decisões de Arquitetura](#decisões-de-arquitetura)
  - [Fases do Projeto](#fases-do-projeto)
  - [Como Reproduzir](#como-reproduzir)
    - [Rodando os testes](#rodando-os-testes)
    - [Deploy em ambiente demonstrável](#deploy-em-ambiente-demonstrável)
  - [Problemas Enfrentados](#problemas-enfrentados)
  - [Resultados Obtidos](#resultados-obtidos)
  - [Melhorias Futuras / Próximos Passos](#melhorias-futuras--próximos-passos)
  - [Licença](#licença)
  - [Contribuindo](#contribuindo)

## Tecnologias Utilizadas

- **Python 3.12**
- **FastAPI** — framework web
- **SQLModel** + **Alembic** — ORM e migrations
- **PostgreSQL 16** — banco de dados relacional, incluindo full-text search nativo
- **MinIO** — object storage (S3-compatible) para anexos, infraestrutura própria do projeto
- **Redis** — broker/backend do Celery
- **Celery** (worker + beat) — processamento assíncrono e tarefas agendadas
- **PyJWT** + **Argon2** — autenticação (access/refresh token) e hashing de senha
- **httpx** — cliente HTTP para entrega de webhooks
- **UV** — gerenciador de dependências e ambiente virtual
- **Ruff** — lint e formatação
- **Pytest** — testes automatizados (~160 testes)
- **Docker / Docker Compose** — orquestração de todo o ambiente (API, banco, storage, fila, workers)

## Decisões de Arquitetura

- **PostgreSQL desde o início** (não SQLite), com todas as configurações de conexão centralizadas em `app/core/config.py`, com segredos obrigatórios (sem default fraco) para forçar falha explícita na inicialização se mal configurados.
- **Status, prioridade e nível de atendimento como enums fixos em Python** (não tabelas configuráveis) — o conjunto de valores é pequeno e estável, e enums tipados evitam erro de digitação em comparações de regra de negócio.
- **VIP como atributo booleano do usuário** (`is_vip`), não um papel/role — papel controla permissão (RBAC), VIP é um atributo de negócio independente, permitindo que um técnico também seja VIP sem conflito.
- **Escalonamento por nível (N1/N2/N3)** com regras de negócio explícitas: repasse só entre pares do mesmo nível ou para a fila do nível acima; rebaixar nível exige um papel de liderança (mapeado hoje para `admin`, representando qualquer função de decisão — gerente, supervisor, tech lead, PO).
- **SLA calculado sob demanda** (não armazenado), reconstruindo a linha do tempo do chamado a partir do histórico de auditoria — nunca reseta na troca de equipe/técnico, e pausa automaticamente durante `aguardando_solicitante` e `aguardando_aprovacao`.
- **Expediente configurável por equipe**, com a convenção de que uma equipe sem expediente cadastrado opera 24/7 — sem necessidade de um flag extra.
- **MinIO com infraestrutura isolada** deste projeto — decisão deliberada de não reaproveitar a instância de outro projeto de portfólio, mantendo cada projeto com sua própria stack.
- **Full-text search com configuração de busca customizada** (`helpdesk_ptbr`), copiando a configuração `portuguese` do Postgres mas remapeando tokens ASCII para `english_stem` — necessário para tratar corretamente termos técnicos em inglês (ex.: "router"/"routers") misturados com português.
- **Catálogo de serviços com formulários tipados e rastreáveis**: campos configuráveis por item (texto/número/seleção) e respostas armazenadas de forma estruturada, vinculadas ao chamado — não como texto livre.
- **Fluxo de aprovação como status do ciclo de vida do chamado** (`aguardando_aprovacao`), não uma flag paralela — reaproveita o mesmo mecanismo de pausa de SLA já existente.
- **Motor de regras de triagem configurável via endpoint** (condições de categoria/palavra-chave/expediente → ações de prioridade/equipe/nível), permitindo ajuste de comportamento sem deploy.
- **Notificações via webhook, não e-mail**: decisão consciente para manter o projeto autocontido e demonstrável sem depender de infraestrutura externa paga (ver Melhorias Futuras).
- **Celery + Redis para automação**: aprovação por timeout, verificação periódica de transição de SLA (com deduplicação de alertas) e entrega de webhook com retry automático, todos rodando em processos worker/beat separados da API.
- **CMDB com relacionamento ativo-a-ativo seguindo o padrão de mercado "Impact Analysis"** (ServiceNow, Jira Service Management, Freshservice): o vínculo entre chamado e ativo é sempre manual; o sistema apenas sugere ativos potencialmente afetados navegando o grafo de dependências, sem nunca vincular automaticamente.
- **Dashboards e KPIs agregados em memória** sobre o cálculo de SLA sob demanda — limitação de performance documentada e conhecida, mitigável no futuro por materialização periódica via Celery Beat.
- **Exportação de dados em CSV síncrona** — a versão assíncrona (para relatórios muito grandes) fica registrada como melhoria futura.

## Fases do Projeto

- [x] **Fase 0 — Fundamentos e Setup**
  - 0.1 Criação do projeto e configuração do ambiente (UV, VSCode)
  - 0.2 Configuração base do FastAPI e arquitetura em camadas
  - 0.3 Configuração do banco de dados e ORM (SQLModel + Alembic, PostgreSQL)
  - 0.4 Dockerização do ambiente de desenvolvimento
  - 0.5 Setup de testes automatizados (Pytest)

- [x] **Fase 1 — Identidade e Acesso**
  - 1.1 Modelagem de Usuários, Papéis e Permissões
  - 1.2 Autenticação via JWT (access + refresh token, Argon2)
  - 1.3 Autorização (RBAC) e endpoint de criação de usuário restrito a admin

- [x] **Fase 2 — Gestão de Chamados (Core)**
  - 2.1 Modelagem de dados de chamados (status, prioridade, nível)
  - 2.2 CRUD de chamados com regras de visibilidade por papel
  - 2.3 Categorias/subcategorias com prioridade padrão automática e tratamento de solicitante VIP
  - 2.4 Histórico de auditoria por campo alterado

- [x] **Fase 3 — Atendimento**
  - 3.1 Equipes e técnicos (vínculo N:N)
  - 3.2 Filas automáticas por categoria → equipe padrão
  - 3.3 Escalonamento por nível de atendimento (N1/N2/N3)
  - 3.4 Colaboração: comentários internos/públicos com menções, e anexos via MinIO

- [x] **Fase 4 — SLA**
  - 4.1 Políticas de SLA por prioridade e expediente configurável por equipe
  - 4.2 Cálculo de tempo útil (respeitando expediente, pausas e trocas de equipe)
  - 4.3 Limiar de risco configurável e listagem de monitoramento com filtros combinados

- [x] **Fase 5 — Base de Conhecimento**
  - 5.1 Artigos com rascunho/publicado, reaproveitando categorias de chamados
  - 5.2 Busca full-text bilíngue (português + inglês) com tags
  - 5.3 Vínculo de artigos a chamados, com marcação exclusiva de artigo-solução e sugestão automática

- [x] **Fase 6 — Catálogo de Serviços**
  - 6.1 Modelagem do catálogo de serviços
  - 6.2 Solicitações padronizadas com formulários tipados e rastreabilidade
  - 6.3 Fluxo de aprovação (manual, automática por VIP, e por timeout)

- [x] **Fase 7 — Automação**
  - 7.1 Motor de regras de triagem configurável (condições e ações)
  - 7.2 Notificações via webhook (Celery + Redis)
  - 7.3 Aprovações automatizadas (VIP e timeout)
  - 7.4 Tarefas agendadas: verificação periódica de transições de SLA

- [x] **Fase 8 — Ativos/CMDB**
  - 8.1 Modelagem de ativos e relacionamentos de dependência
  - 8.2 Vínculo de ativos a chamados com sugestão de impacto (Impact Analysis)

- [x] **Fase 9 — Gestão e Indicadores**
  - 9.1 Dashboard agregado (volume, cumprimento de SLA, tempo médio)
  - 9.2 KPIs de série temporal e desempenho individual por técnico
  - 9.3 Exportação de dados em CSV sob demanda

- [ ] **Fase 10 — Finalização**
  - [x] 10.1 Documentação (README, customização do Swagger)
  - [ ] 10.2 CI/CD (pipeline de lint/testes)
  - [ ] 10.3 Deploy em ambiente demonstrável (guia em `DEPLOY.md`)

## Como Reproduzir

```bash
git clone https://github.com/thaleswillreis/helpdesk-backend-api.git
cd helpdesk-backend-api

# 1. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env: preencha POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD e SECRET_KEY
# (gere o SECRET_KEY com: python -c "import secrets; print(secrets.token_hex(32))")

# 2. Suba a infraestrutura completa (banco, object storage, fila e workers)
docker compose up -d db minio minio-init redis celery-worker celery-beat

# 3. Instale as dependências e aplique as migrations
uv sync
uv run alembic upgrade head

# 4. Crie o primeiro usuário administrador
uv run python -m scripts.create_admin

# 5. Suba a API
docker compose up -d --build
```

A API estará disponível em `http://127.0.0.1:8000`, com documentação interativa em `http://127.0.0.1:8000/docs`.
O console do MinIO fica em `http://127.0.0.1:9011`.

### Rodando os testes

```bash
docker compose up -d minio minio-init  # os testes de anexo dependem do MinIO
uv run pytest -v
```

### Deploy em ambiente demonstrável

Um guia de deploy será disponibilizado em [`DEPLOY.md`](DEPLOY.md) ao concluir a Tarefa 10.3.

## Problemas Enfrentados

- **Conexão de rede entre containers vs. execução local.** Postgres e MinIO exigem hostnames diferentes dependendo de onde o código roda (`localhost` local vs. nome do serviço Docker). Resolvido mantendo o `.env` de desenvolvimento local e sobrescrevendo pontualmente essas variáveis no `docker-compose.yml`, via `environment:` no serviço `api`.
- **Migration tentando criar o mesmo tipo enum duas vezes.** A criação manual do tipo e a criação automática disparada pelo SQLAlchemy ao usar o enum como tipo de coluna colidiram. Resolvido com `postgresql.ENUM(..., create_type=False)`.
- **Segredos com valor padrão fraco no código.** Uma revisão de segurança identificou que `postgres_password`, `minio_root_password` e `secret_key` tinham defaults hardcoded — corrigido tornando-os obrigatórios, fazendo a aplicação falhar explicitamente (fail-fast) se não configurados.
- **Comparação entre datetime "aware" e "naive" no cálculo de SLA.** A coluna `DateTime` do Postgres não armazena fuso horário; valores lidos de volta via SQLAlchemy retornam sem `tzinfo`. Resolvido normalizando todo datetime vindo do banco para UTC-aware antes de comparar.
- **Perda de precisão de microssegundo em turnos que cruzam a meia-noite.** Um sentinela `time(23, 59, 59, 999999)` para "fim do dia" causava erro de arredondamento no cálculo de expediente. Corrigido resolvendo o sentinela para a meia-noite real do dia seguinte.
- **`GENERATED ALWAYS AS` do Postgres não aceita `to_tsvector` com idioma**, por não ser uma expressão IMMUTABLE. Resolvido com uma coluna comum mantida por trigger `BEFORE INSERT OR UPDATE` — a abordagem clássica do Postgres para full-text search.
- **Schema de testes divergente do schema de desenvolvimento.** O banco de testes é montado via `SQLModel.metadata.create_all()`, que não executa migrations — recursos puramente SQL (trigger, índice GIN, configuração de busca) precisaram ser replicados manualmente na fixture de setup dos testes.
- **Enum do Postgres com rótulos diferentes conforme o método de criação do schema.** Por padrão, o SQLAlchemy grava o *nome* do membro do enum Python (`ABERTO`), não seu `.value` (`aberto`), a menos que `values_callable` seja configurado — isso ficou mascarado enquanto todas as comparações passavam pelo ORM, e só apareceu ao introduzir uma consulta com literal SQL cru. Corrigido configurando `values_callable` explicitamente na coluna.
- **A configuração `portuguese` do Postgres não trata inglês tão bem quanto o esperado.** Buscar "routers" não encontrava "router", pois o mesmo dicionário português é aplicado a todos os tokens. Corrigido com uma configuração de busca customizada (`helpdesk_ptbr`) remapeando tokens ASCII para `english_stem`.
- **Ordem de declaração de rotas no FastAPI causando colisão.** Endpoints com segmento fixo (`/tickets/overview`, `/articles/search`) precisam ser declarados antes de rotas com parâmetro dinâmico (`/tickets/{id}`) no mesmo nível, pois o roteamento segue a ordem de declaração, não a mais específica.
- **Arquivo de migration planejado mas nunca criado**, gerando um "elo perdido" na cadeia de revisões do Alembic — só descoberto ao tentar aplicar uma migration posterior. Reforçou o hábito de conferir a lista de arquivos criados contra o que foi de fato solicitado antes de rodar `alembic upgrade head`.
- **Definição duplicada de fixture no `conftest.py`**, onde a segunda definição sobrescreveu silenciosamente a primeira (comportamento padrão do Python, não do pytest) — corrigido consolidando em uma única definição.
- **Import circular entre módulos de notificação e tarefas do Celery**, causado pela necessidade de `celery_app.py` importar todos os módulos de tarefas para o worker reconhecê-las. Resolvido adiando o import de `send_webhook_notification` para dentro da função que o usa.
- **Colisão de nomes de exceção entre services** (`DuplicateLinkError`, `LinkNotFoundError` definidos de forma idêntica em `ticket_article_service` e `ticket_asset_service`), importados sem alias no mesmo controller — o segundo import sobrescreveu silenciosamente o primeiro, fazendo um `except` capturar o tipo errado. Corrigido com aliases explícitos nos imports.
- **Geração do nome de tabela pelo SQLModel a partir de nomes de classe compostos** (`TicketCatalogAnswer` → `ticketcataloganswer`) gerou um erro de digitação numa migration por suposição manual — corrigido verificando o nome real via `Model.__tablename__` antes de escrever a migration.
- **Testes que não verificavam o status code de uma chamada intermediária** (`PATCH` de setup) antes de basear a asserção final nela — um padrão que se repetiu mais de uma vez, sempre mascarando a causa real de uma falha atrás de uma asserção distante. Reforçou o hábito de sempre validar `status_code` em chamadas de setup dentro de um teste.

## Resultados Obtidos

O projeto entrega um backend de ITSM funcionalmente completo, cobrindo as 10 fases do roteiro original e 85 endpoints cobrindo as mais diversas funcionalidades:

- Autenticação e RBAC completos, com hashing seguro (Argon2) e tokens JWT
- Ciclo de vida de chamados com escalonamento por nível, colaboração e histórico de auditoria
- Motor de SLA que respeita expediente por equipe, com pausas e sem reset em transferências
- Base de conhecimento com busca full-text bilíngue e vínculo rastreável com chamados
- Catálogo de serviços com formulários dinâmicos e fluxo de aprovação (manual e automatizado)
- CMDB com grafo de dependências entre ativos e análise de impacto
- Motor de automação configurável, notificações via webhook e tarefas agendadas via Celery
- Dashboards, KPIs e exportação de dados para gestão

Ao longo do desenvolvimento, ~160 testes automatizados foram construídos incrementalmente, cobrindo cada tarefa do roteiro, com o ambiente completo orquestrado via Docker Compose (API, PostgreSQL, MinIO, Redis, workers Celery).

## Melhorias Futuras / Próximos Passos

- **Notificação por e-mail**, complementando o webhook já implementado — adiado por depender de infraestrutura SMTP externa (paga ou de terceiros), enquanto o webhook é autocontido e demonstrável sem custo.
- **Exportação assíncrona via Celery**, para relatórios muito grandes, com download disponibilizado após processamento em background.
- **Limiar de risco de SLA configurável por prioridade/equipe** — hoje é uma configuração global única.
- **Papel "gerente" dedicado**, separado de `admin`, para decisões de liderança (hoje `admin` acumula os dois sentidos).
- **Materialização periódica do status de SLA** (via Celery Beat), para escalar a performance das agregações de dashboard/KPI/monitoramento além do cálculo em memória atual.
- **CI/CD** (Tarefa 10.2) e **guia de deploy documentado** (Tarefa 10.3) — próximos passos imediatos do roteiro.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## Contribuindo

Este é um projeto pessoal de portfólio, mas sugestões, correções e boas práticas são bem-vindas. Sinta-se à vontade para abrir uma *issue* ou um *pull request*.