# Helpdesk Backend API

Backend de um sistema de abertura e gestão de chamados (helpdesk), desenvolvido em **Python** com **FastAPI**, seguindo uma arquitetura em camadas (Models, Services, Controllers).

> ⚠️ Projeto em desenvolvimento ativo, construído como parte de portfólio pessoal.

## Sobre o projeto

O objetivo é simular, de forma realista, o backend de uma ferramenta de service desk/ITSM, cobrindo desde o registro de chamados até automações, base de conhecimento e indicadores de gestão.

### Funcionalidades planejadas

- 🎫 **Gestão de chamados** — registro, classificação, acompanhamento e encerramento
- 👥 **Atendimento** — filas, equipes, técnicos, escalonamento e colaboração
- ⏱️ **SLA** — controle de prazos de resposta e solução
- 📚 **Base de conhecimento** — criação e disponibilização de soluções
- 🗂️ **Catálogo de serviços** — solicitações padronizadas
- ⚙️ **Automação** — triagem, notificações, aprovações e tarefas automáticas
- 💻 **Ativos/CMDB** — vínculo entre chamados e equipamentos/serviços
- 📊 **Gestão** — dashboards, indicadores e relatórios

### O que já está implementado

- **Autenticação e autorização**: login via JWT (access + refresh token), hashing de senha com Argon2, e RBAC por papel (admin, técnico, solicitante)
- **Gestão de chamados**: CRUD completo com regras de visibilidade por papel, categorias e subcategorias com prioridade padrão automática, e tratamento especial para solicitantes VIP
- **Histórico de auditoria**: toda alteração relevante em um chamado (status, prioridade, categoria, atribuição, equipe, nível) é registrada, com autor, data e comentário opcional
- **Equipes e atendimento**: equipes de técnicos (um técnico pode pertencer a várias), distribuição automática de chamados por categoria → equipe padrão, reatribuição livre entre equipes/técnicos
- **Escalonamento por nível**: técnicos e chamados possuem nível de atendimento (N1/N2/N3), com regras de repasse (só entre pares do mesmo nível ou para a fila do nível acima; rebaixar nível exige um papel de liderança/decisão — hoje mapeado para `admin`)
- **Colaboração**: comentários internos (visíveis só à equipe) e públicos (visíveis ao solicitante), com suporte a menção de usuários
- **Anexos**: upload de arquivos vinculados a um chamado, armazenados em object storage (MinIO), com validação de extensão e tamanho, e download via URL temporária pré-assinada

## Stack utilizada

- **Python 3.12**
- **FastAPI** — framework web
- **SQLModel** + **Alembic** — ORM e migrations
- **PostgreSQL** — banco de dados relacional
- **MinIO** — object storage (S3-compatible) para anexos
- **PyJWT** + **Argon2** — autenticação e hashing de senha
- **UV** — gerenciador de dependências e ambiente virtual
- **Ruff** — lint e formatação
- **Pytest** — testes automatizados
- **Docker / Docker Compose** — containerização de todo o ambiente (app, banco, object storage)

## Arquitetura

O projeto é dividido em camadas:

- **Controllers/** - Exposição dos endpoints (rotas)
- **Services/** - Regras de negócio
- **Models/** - Acesso e modelagem de dados
- **Schemas/** - Contratos de entrada/saída da API (Pydantic)
- **Core/** - Configurações transversais (banco, segurança, storage, papéis)

## Como rodar localmente

```bash
git clone https://github.com/thaleswillreis/helpdesk-backend-api.git
cd helpdesk-backend-api

# 1. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env se quiser mudar usuários/senhas padrão

# 2. Suba a infraestrutura (Postgres + MinIO)
docker compose up -d db minio minio-init

# 3. Instale as dependências e aplique as migrations
uv sync
uv run alembic upgrade head

# 4. Crie o primeiro usuário administrador
uv run python -m scripts.create_admin

# 5. Suba a API (via Docker, recomendado)
docker compose up -d --build
```

A API estará disponível em `http://127.0.0.1:8000`, com documentação interativa em `http://127.0.0.1:8000/docs`.

O console do MinIO (para inspecionar os anexos enviados) fica em `http://127.0.0.1:9011`, com as credenciais definidas em `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` no seu `.env`.

### Rodando os testes

```bash
docker compose up -d minio minio-init  # os testes de anexo dependem do MinIO
uv run pytest -v
```

## Status do desenvolvimento

O projeto está sendo construído de forma incremental, seguindo um backlog dividido em fases:

- [x] Fase 0 — Fundamentos e setup do projeto
- [x] Fase 1 — Identidade e acesso
- [x] Fase 2 — Gestão de chamados
- [x] Fase 3 — Atendimento
- [x] Fase 4 — SLA
- [ ] Fase 5 — Base de conhecimento
- [ ] Fase 6 — Catálogo de serviços
- [ ] Fase 7 — Automação
- [ ] Fase 8 — Ativos/CMDB
- [ ] Fase 9 — Gestão e indicadores
- [ ] Fase 10 — Finalização

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).