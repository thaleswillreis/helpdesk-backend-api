# Helpdesk Backend API

![CI](https://github.com/thaleswillreis/helpdesk-backend-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Celery](https://img.shields.io/badge/Celery-5.4-37814A)
![License](https://img.shields.io/badge/license-MIT-green)

Backend de um sistema de abertura e gestão de chamados (Helpdesk/ITSM), desenvolvido em **Python** com **FastAPI**, seguindo uma arquitetura em camadas (Models, Services, Controllers).

## Sobre o projeto

O objetivo deste projeto de portfólio é desenvolver, de forma realista, o backend de uma ferramenta de service desk/ITSM completa — cobrindo desde o registro de chamados até automação, base de conhecimento, catálogo de serviços, CMDB e indicadores de gestão. O desenvolvimento seguiu um roteiro em 10 fases (Épicos), executadas de forma incremental e orientada a decisões deliberadas de arquitetura. Ao todo a API contém 85 endpoints que cobrem todas as principais funcionalidades que um sistema do tipo Helpdesk/ITSM deve conter para está apto a entrar em produção e ser plenamente utilizável.

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
  - [Endpoints da API](#endpoints-da-api)
  - [Melhorias Futuras / Próximos Passos](#melhorias-futuras--próximos-passos)
  - [Licença](#licença)
  - [Contribuindo](#contribuindo)

## Tecnologias Utilizadas

- **Python 3.12**
- **FastAPI** — framework web
- **SQLModel** + **Alembic** — ORM e migrations
- **PostgreSQL 16** — banco de dados relacional, incluindo full-text search nativo
- **RustFS** — object storage compatível com S3 (anexos), acessado pelo SDK `minio` como cliente S3
- **Redis** — broker/backend do Celery
- **Celery** (worker + beat) — processamento assíncrono e tarefas agendadas
- **PyJWT** + **Argon2** — autenticação (access/refresh token) e hashing de senha
- **httpx** — cliente HTTP para entrega de webhooks
- **UV** — gerenciador de dependências e ambiente virtual
- **Ruff** — lint (regras de erro real, sem formatação imposta)
- **Pytest** — testes automatizados (167 testes)
- **Docker / Docker Compose** — orquestração de todo o ambiente (API, banco, storage, fila, workers)
- **GitHub Actions** — integração contínua (lint, testes com infraestrutura real e build da imagem)
- **Caddy** — proxy reverso com HTTPS automático (deploy)

## Decisões de Arquitetura

- **PostgreSQL desde o início** (não SQLite), com todas as configurações de conexão centralizadas em `app/core/config.py`, com segredos obrigatórios (sem default fraco) para forçar falha explícita na inicialização se mal configurados.
- **Status, prioridade e nível de atendimento como enums fixos em Python** (não tabelas configuráveis) — o conjunto de valores é pequeno e estável, e enums tipados evitam erro de digitação em comparações de regra de negócio. Toda coluna enum usa um helper (`pg_enum_column`) que força a persistência do `.value` do enum, não o nome do membro Python (ver Problemas Enfrentados).
- **VIP como atributo booleano do usuário** (`is_vip`), não um papel/role — papel controla permissão (RBAC), VIP é um atributo de negócio independente, permitindo que um técnico também seja VIP sem conflito.
- **Escalonamento por nível (N1/N2/N3)** com regras de negócio explícitas: repasse só entre pares do mesmo nível ou para a fila do nível acima; rebaixar nível exige um papel de liderança (mapeado hoje para `admin`, representando qualquer função de decisão — gerente, supervisor, tech lead, PO).
- **SLA calculado sob demanda** (não armazenado), reconstruindo a linha do tempo do chamado a partir do histórico de auditoria — nunca reseta na troca de equipe/técnico, e pausa automaticamente durante `aguardando_solicitante` e `aguardando_aprovacao`.
- **Expediente configurável por equipe**, com a convenção de que uma equipe sem expediente cadastrado opera 24/7.
- **Object storage S3 com infraestrutura isolada** deste projeto — decisão deliberada de não reaproveitar a instância de outro projeto de portfólio. O cliente S3 é desacoplado do servidor: a troca de MinIO para RustFS (ver Problemas Enfrentados) exigiu mudanças apenas no módulo de storage, no compose e no CI, sem tocar nas regras de negócio.
- **Full-text search com configuração de busca customizada** (`helpdesk_ptbr`), copiando a configuração `portuguese` do Postgres mas remapeando tokens ASCII para `english_stem` — necessário para tratar corretamente termos técnicos em inglês (ex.: "router"/"routers") misturados com português.
- **Catálogo de serviços com formulários tipados e rastreáveis**: campos configuráveis por item (texto/número/seleção) e respostas armazenadas de forma estruturada, vinculadas ao chamado.
- **Fluxo de aprovação como status do ciclo de vida do chamado** (`aguardando_aprovacao`), não uma flag paralela — reaproveita o mesmo mecanismo de pausa de SLA já existente.
- **Motor de regras de triagem configurável via endpoint**, permitindo ajuste de comportamento (prioridade/equipe/nível, por categoria/palavra-chave/expediente) sem deploy.
- **Notificações via webhook, não e-mail**: decisão consciente para manter o projeto autocontido e demonstrável sem depender de infraestrutura externa paga (ver Melhorias Futuras).
- **Celery + Redis para automação**: aprovação por timeout, verificação periódica de transição de SLA (com deduplicação de alertas) e entrega de webhook com retry automático, todos rodando em processos worker/beat separados da API.
- **CMDB com relacionamento ativo-a-ativo seguindo o padrão de mercado "Impact Analysis"** (ServiceNow, Jira Service Management, Freshservice): o vínculo entre chamado e ativo é sempre manual; o sistema apenas sugere ativos potencialmente afetados navegando o grafo de dependências.
- **Dashboards e KPIs agregados em memória** sobre o cálculo de SLA sob demanda — limitação de performance documentada, mitigável no futuro por materialização periódica via Celery Beat.
- **Exportação de dados em CSV síncrona** — a versão assíncrona fica registrada como melhoria futura.
- **Lint com regras de erros reais** (`ruff` com E9, F e B): foca em nomes indefinidos, imports não usados, redefinições e armadilhas de código, sem impor estilo nem reformatar o código existente. Chamadas do FastAPI em valores default (`Depends`, `Query`, `File`) e a fábrica de dependência `require_role` são declaradas imutáveis para o bugbear.
- **CI que valida a cadeia de migrations em banco limpo**, além de lint, testes (contra Postgres, storage S3 e Redis reais, via o próprio `docker-compose.yml`) e build da imagem Docker.
- **Deploy em VPS única com Docker Compose**, com um compose de produção autônomo (`docker-compose.prod.yml`), migrations automáticas por um serviço de execução única, nenhuma porta interna publicada e HTTPS automático via Caddy. O guia completo está em `DEPLOY.md`.

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
  - 3.4 Colaboração: comentários internos/públicos com menções, e anexos via object storage

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

- [x] **Fase 10 — Finalização**
  - 10.1 Documentação (README e customização do Swagger)
  - 10.2 CI/CD: pipeline de lint, testes e build no GitHub Actions
  - 10.3 Deploy em ambiente demonstrável: guia didático em [`DEPLOY.md`](DEPLOY.md), com compose de produção e Caddyfile

## Como Reproduzir

```bash
git clone https://github.com/thaleswillreis/helpdesk-backend-api.git
cd helpdesk-backend-api

# 1. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env: preencha POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD e SECRET_KEY
# (gere segredos com: python3 -c "import secrets; print(secrets.token_hex(32))")

# 2. Suba a infraestrutura completa (banco, storage S3, fila e workers)
docker compose up -d db storage redis celery-worker celery-beat

# 3. Instale as dependências e aplique as migrations
uv sync
uv run alembic upgrade head

# 4. Crie o primeiro usuário administrador
uv run python -m scripts.create_admin

# 5. Suba a API
docker compose up -d --build
```

A API estará disponível em `http://127.0.0.1:8000`, com documentação interativa em `http://127.0.0.1:8000/docs`.
O console do storage (RustFS) fica em `http://127.0.0.1:9011`, com as credenciais definidas em `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` no seu `.env`. O serviço `storage-init` cria o bucket de anexos automaticamente.

### Rodando os testes

```bash
docker compose up -d db storage redis
uv run python -m scripts.create_bucket  # os testes de anexo dependem do bucket
uv run pytest -v
```

### Deploy em ambiente demonstrável

O guia completo de publicação em uma VPS (Docker Compose, HTTPS automático, backups e checklist de segurança) está em [`DEPLOY.md`](DEPLOY.md).

## Problemas Enfrentados

- **Conexão de rede entre containers vs. execução local.** Postgres e storage exigem hostnames diferentes dependendo de onde o código roda (`localhost` local vs. nome do serviço Docker). Resolvido mantendo o `.env` de desenvolvimento local e sobrescrevendo pontualmente essas variáveis no `docker-compose.yml`.
- **Migration tentando criar o mesmo tipo enum duas vezes.** A criação manual do tipo e a criação automática disparada pelo SQLAlchemy colidiram. Resolvido com `postgresql.ENUM(..., create_type=False)`.
- **Segredos com valor padrão fraco no código.** `postgres_password`, `minio_root_password` e `secret_key` tinham defaults hardcoded — corrigido tornando-os obrigatórios, fail-fast na inicialização.
- **Comparação entre datetime "aware" e "naive" no cálculo de SLA.** A coluna `DateTime` do Postgres não armazena fuso horário. Resolvido normalizando todo datetime vindo do banco para UTC-aware antes de comparar.
- **Perda de precisão de microssegundo em turnos que cruzam a meia-noite.** Um sentinela `time(23, 59, 59, 999999)` causava erro de arredondamento no cálculo de expediente. Corrigido resolvendo o sentinela para a meia-noite real do dia seguinte.
- **`GENERATED ALWAYS AS` do Postgres não aceita `to_tsvector` com idioma**, por não ser IMMUTABLE. Resolvido com uma coluna mantida por trigger `BEFORE INSERT OR UPDATE`.
- **Schema de testes divergente do schema de desenvolvimento.** O banco de testes é montado via `SQLModel.metadata.create_all()`, que não executa migrations — recursos puramente SQL precisaram ser replicados manualmente na fixture de setup.
- **Rótulos de enum divergentes conforme o método de criação do schema — bug sistêmico, não pontual.** Por padrão, o SQLAlchemy grava o *nome* do membro do enum Python (`ABERTO`), não seu `.value` (`aberto`), a menos que `values_callable` seja configurado. Isso ficou mascarado porque tanto o banco de testes (`create_all()`) quanto todas as comparações via ORM eram "consistentemente errados entre si". O problema foi corrigido pontualmente em `Ticket.status` ao ser descoberto via consulta com SQL bruto (Fase 7), mas só na validação manual da Tarefa 10.3, contra um Postgres real criado por migration, é que ficou claro que **todo campo enum do projeto** tinha o mesmo risco (prioridade, nível, status de artigo, tipos/status de ativos, entre outros) — um erro 500 ao criar uma categoria expôs isso. Corrigido de forma sistemática com um helper (`pg_enum_column`) aplicado a todas as colunas enum do projeto.
- **A configuração `portuguese` do Postgres não trata inglês tão bem quanto o esperado.** Corrigido com uma configuração de busca customizada (`helpdesk_ptbr`) remapeando tokens ASCII para `english_stem`.
- **Ordem de declaração de rotas no FastAPI causando colisão.** Endpoints com segmento fixo precisam ser declarados antes de rotas com parâmetro dinâmico no mesmo nível.
- **Arquivo de migration planejado mas nunca criado**, só descoberto ao aplicar uma migration posterior.
- **Definição duplicada de fixture no `conftest.py`**, onde a segunda sobrescreveu silenciosamente a primeira.
- **Import circular entre módulos de notificação e tarefas do Celery**, resolvido adiando o import para dentro da função que o usa.
- **Colisão de nomes de exceção entre services** importados sem alias no mesmo controller, corrigida com aliases explícitos.
- **Geração do nome de tabela pelo SQLModel a partir de nomes de classe compostos**, causando um erro de digitação numa migration por suposição manual — corrigido verificando `Model.__tablename__` antes de escrever a migration.
- **Testes que não verificavam o status code de uma chamada intermediária** antes de basear a asserção final nela, mascarando a causa real de falhas.
- **B008 do bugbear com o FastAPI.** Chamadas em valor default de parâmetro (`Depends(...)`) são um padrão do framework; a fábrica `require_role(...)`, usada dentro de `Depends`, também precisou ser declarada imutável na configuração do ruff.
- **Remoção das imagens do MinIO dos registros públicos (incidente de cadeia de suprimentos).** Em setembro de 2026 o MinIO apagou `minio/minio` e `minio/mc` do Docker Hub, e o Quay passou a bloquear pulls anônimos dias depois — a edição comunitária foi descontinuada. O CI falhou com uma mensagem enganosa (`pull access denied ... may require 'docker login'`), enquanto o ambiente local seguia funcionando por causa do cache, mascarando o problema. Resolvido substituindo o servidor por um mantido e compatível com S3 (RustFS), criando o bucket por script Python via SDK (sem depender do cliente `mc`), e validando compatibilidade com testes de integração reais, incluindo leitura via URL pré-assinada.
- **Uma única flag de HTTPS para dois clientes S3.** O cliente interno (upload, HTTP na rede Docker) e o público (download assinado, HTTPS via proxy) compartilhavam a mesma flag `minio_secure`. Separado em `minio_public_secure`, com região fixa (`us-east-1`) no cliente público para a assinatura não depender de consulta ao servidor.
- **Conta técnica sem hash de senha válido.** O usuário sistema (usado em aprovações automatizadas) tinha um valor que não é um hash Argon2 válido; um login com essa conta gerava `InvalidHashError` não tratado, resultando em 500 em vez de 401 — o que também vazaria a existência da conta pela diferença de resposta. Corrigido ampliando a captura de exceções no `verify_password`.

## Resultados Obtidos

O projeto entrega um backend de ITSM funcionalmente completo, cobrindo as 10 fases do roteiro do projeto original:

- Autenticação e RBAC completos, com hashing seguro (Argon2) e tokens JWT
- Ciclo de vida de chamados com escalonamento por nível, colaboração e histórico de auditoria
- Motor de SLA que respeita expediente por equipe, com pausas e sem reset em transferências
- Base de conhecimento com busca full-text bilíngue e vínculo rastreável com chamados
- Catálogo de serviços com formulários dinâmicos e fluxo de aprovação (manual e automatizado)
- CMDB com grafo de dependências entre ativos e análise de impacto
- Motor de automação configurável, notificações via webhook e tarefas agendadas via Celery
- Dashboards, KPIs e exportação de dados para gestão

Ao todo são 167 testes automatizados que foram construídos incrementalmente, cobrindo cada tarefa do roteiro, com o ambiente completo orquestrado via Docker Compose (API, PostgreSQL, RustFS, Redis, workers Celery). A stack de produção (Docker Compose + Caddy, HTTPS automático) foi validada localmente de ponta a ponta, incluindo autenticação, escrita no banco e download de anexo via URL assinada atravessando o proxy reverso.

   ## Endpoints da API

   A lista completa de endpoints, organizada por categoria, está em [`ENDPOINTS.md`](ENDPOINTS.md). Para exploração interativa, use o Swagger em `/docs`com o projeto em execução.

## Melhorias Futuras / Próximos Passos

- **Notificação por e-mail**, complementando o webhook já implementado — adiado por depender de infraestrutura SMTP externa.
- **Exportação assíncrona via Celery**, para relatórios muito grandes.
- **Limiar de risco de SLA configurável por prioridade/equipe** — hoje é uma configuração global única.
- **Papel "gerente" dedicado**, separado de `admin`, para decisões de liderança.
- **Materialização periódica do status de SLA** (via Celery Beat), para escalar a performance das agregações além do cálculo em memória atual.
- **Renomear as variáveis `MINIO_*`** para nomes neutros (ex.: `STORAGE_*`) — hoje o prefixo é herdado do SDK `minio`, embora o servidor seja o RustFS.
- **Espelhar ou fixar por digest as imagens de infraestrutura** em um registro próprio, para que a remoção de uma imagem pública vire uma notificação e não uma quebra de build.
- **Acompanhar a maturidade do RustFS** (versão 1.0 recente); SeaweedFS foi avaliado como alternativa.
- **Dockerfile de produção** com build multi-stage e usuário não privilegiado.
- **Deploy contínuo (CD)**: o CI valida o código, mas a publicação no servidor ainda é manual.
- **Padronização completa de lint e formatação** (limite de linha, ordenação de imports, `ruff format`), hoje fora do escopo do CI.
- **Observabilidade e backups automatizados** na operação em servidor.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## Contribuindo

Este é um projeto pessoal de portfólio, mas sugestões, correções e boas práticas são bem-vindas. Sinta-se à vontade para abrir uma *issue* ou um *pull request*.