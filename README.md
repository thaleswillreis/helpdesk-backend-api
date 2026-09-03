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

## Stack utilizada

- **Python 3.12**
- **FastAPI** — framework web
- **UV** — gerenciador de dependências e ambiente virtual
- **Ruff** — lint e formatação
- **Pytest** — testes automatizados
- **Docker** — containerização (em progresso)

## Arquitetura

O projeto é dividido em camadas:


- **Controllers/** - Exposição dos endpoints (rotas)
- **Services/** - Regras de negócio
- **Models/** - Acesso e modelagem de dados
- **Schemas/** - Contratos de entrada/saída da API (Pydantic)
- **Core/** - Configurações transversais


## Como rodar localmente
Obs: mudará conforme o avanço do projeto.
```bash
git clone https://github.com/thaleswillreis/helpdesk-backend-api.git
cd helpdesk-backend-api
uv sync
uv run uvicorn app.main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`, com documentação interativa em `http://127.0.0.1:8000/docs`.

## Status do desenvolvimento

O projeto está sendo construído de forma incremental, seguindo um backlog dividido em fases:

- [x] Fase 0 — Fundamentos e setup do projeto *(em andamento)*
- [x] Fase 1 — Identidade e acesso
- [ ] Fase 2 — Gestão de chamados
- [ ] Fase 3 — Atendimento
- [ ] Fase 4 — SLA
- [ ] Fase 5 — Base de conhecimento
- [ ] Fase 6 — Catálogo de serviços
- [ ] Fase 7 — Automação
- [ ] Fase 8 — Ativos/CMDB
- [ ] Fase 9 — Gestão e indicadores
- [ ] Fase 10 — Finalização

## Licença

A definir.