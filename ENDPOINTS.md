# Endpoints da API

Lista de todos os endpoints do Helpdesk Backend API, organizados por categoria. Para exploração interativa, use a documentação Swagger em `/docs`.

## Sumário

- [health](#health)
- [auth](#auth)
- [users](#users)
- [categories](#categories)
- [teams](#teams)
- [sla](#sla)
- [settings](#settings)
- [tickets](#tickets)
- [knowledge-base](#knowledge-base)
- [service-catalog](#service-catalog)
- [automation](#automation)
- [cmdb](#cmdb)
- [dashboard](#dashboard)

---

### health - Verificação de disponibilidade da API.

- **GET** `/health` - Verificação da saúde da API

---

### auth - Autenticação: login, refresh token e usuário autenticado.

- **POST** `/auth/login` - Autentica o usuário (e-mail/senha) e emite access + refresh token
- **POST** `/auth/refresh` - Emite um novo par de tokens a partir de um refresh token válido
- **GET** `/auth/me` - Retorna os dados do usuário autenticado

---

### users - Cadastro e gestão de usuários (restrito a administradores).

- **POST** `/users` - Cria um novo usuário (papel, nível e status VIP configuráveis). Restrito a administradores

---

### categories - Categorias e subcategorias de classificação de chamados.

- **POST** `/categories` - Cria uma categoria (prioridade padrão e equipe padrão). Restrito a administradores
- **GET** `/categories` - Lista todas as categorias
- **PATCH** `/categories/{category_id}` - Atualiza uma categoria existente. Restrito a administradores
- **POST** `/subcategories` - Cria uma subcategoria vinculada a uma categoria. Restrito a administradores
- **GET** `/subcategories` - Lista subcategorias, opcionalmente filtrando por categoria
- **PATCH** `/subcategories/{subcategory_id}` - Atualiza uma subcategoria existente. Restrito a administradores

---

### teams - Equipes de atendimento, membros e expediente.

- **POST** `/teams` - Cria uma nova equipe. Restrito a administradores
- **GET** `/teams` - Lista todas as equipes
- **PATCH** `/teams/{team_id}` - Atualiza uma equipe existente. Restrito a administradores
- **POST** `/teams/{team_id}/members` - Adiciona um técnico à equipe. Restrito a administradores
- **GET** `/teams/{team_id}/members` - Lista os técnicos membros da equipe
- **DELETE** `/teams/{team_id}/members/{user_id}` - Remove um técnico da equipe. Restrito a administradores
- **POST** `/teams/{team_id}/schedule` - Cadastra a janela de expediente de um dia da semana. Restrito a administradores
- **GET** `/teams/{team_id}/schedule` - Lista o expediente cadastrado da equipe (vazio = 24/7)
- **DELETE** `/teams/{team_id}/schedule/{schedule_id}` - Remove uma janela de expediente. Restrito a administradores

---

### sla - Políticas de SLA por prioridade.

- **POST** `/sla-policies` - Cria a política de SLA (prazos de resposta/solução) para uma prioridade. Restrito a administradores
- **GET** `/sla-policies` - Lista as políticas de SLA cadastradas. Restrito a admin/técnico
- **PATCH** `/sla-policies/{policy_id}` - Atualiza os prazos de uma política de SLA. Restrito a administradores

---

### settings - Configurações globais do sistema (ex.: limiar de risco de SLA).

- **GET** `/system-settings` - Consulta as configurações globais atuais. Restrito a admin/técnico
- **PATCH** `/system-settings` - Atualiza as configurações globais (ex.: limiar de risco de SLA). Restrito a administradores

---

### tickets - Ciclo de vida completo dos chamados: CRUD, histórico, comentários, anexos, SLA, vínculo com artigos e ativos, catálogo e aprovação.

- **POST** `/tickets` - Abre um novo chamado
- **GET** `/tickets` - Lista chamados visíveis ao usuário autenticado
- **GET** `/tickets/overview` - Lista chamados com filtros combinados (status, equipe, nível, data, situação de SLA). Restrito a admin/técnico
- **GET** `/tickets/{ticket_id}` - Consulta um chamado específico
- **PATCH** `/tickets/{ticket_id}` - Atualiza um chamado (status, prioridade, atribuição, equipe, nível). Restrito a admin/técnico
- **GET** `/tickets/{ticket_id}/history` - Consulta o histórico de alterações do chamado
- **GET** `/tickets/{ticket_id}/sla` - Consulta o status de SLA (resposta e solução) do chamado
- **POST** `/tickets/{ticket_id}/comments` - Adiciona um comentário (interno ou público) ao chamado
- **GET** `/tickets/{ticket_id}/comments` - Lista os comentários visíveis ao usuário
- **POST** `/tickets/{ticket_id}/attachments` - Envia um anexo para o chamado (armazenado no object storage)
- **GET** `/tickets/{ticket_id}/attachments` - Lista os anexos do chamado
- **GET** `/tickets/{ticket_id}/attachments/{attachment_id}/download` - Gera uma URL de download temporária para o anexo
- **POST** `/tickets/{ticket_id}/articles` - Vincula um artigo da base de conhecimento ao chamado. Restrito a admin/técnico
- **GET** `/tickets/{ticket_id}/articles` - Lista os artigos vinculados ao chamado
- **GET** `/tickets/{ticket_id}/articles/suggestions` - Sugere artigos relevantes (mesma categoria + relevância textual)
- **PATCH** `/tickets/{ticket_id}/articles/{article_id}` - Marca ou desmarca um artigo vinculado como a solução do chamado
- **DELETE** `/tickets/{ticket_id}/articles/{article_id}` - Remove o vínculo entre o chamado e o artigo
- **POST** `/tickets/catalog` - Abre um chamado a partir de um item do catálogo de serviços, validando o formulário
- **GET** `/tickets/{ticket_id}/catalog-answers` - Consulta as respostas do formulário de catálogo do chamado
- **POST** `/tickets/{ticket_id}/approve` - Aprova ou rejeita um chamado que está aguardando aprovação. Restrito a administradores
- **POST** `/tickets/{ticket_id}/assets` - Vincula manualmente um ativo do CMDB ao chamado. Restrito a admin/técnico
- **GET** `/tickets/{ticket_id}/assets/affected-suggestions` - Sugere ativos potencialmente afetados via grafo de dependências (só leitura)
- **GET** `/tickets/{ticket_id}/assets` - Lista os ativos vinculados ao chamado
- **DELETE** `/tickets/{ticket_id}/assets/{asset_id}` - Remove o vínculo entre o chamado e o ativo

---

### knowledge-base - Artigos da base de conhecimento, com busca full-text bilíngue.

- **POST** `/articles` - Cria um artigo (rascunho ou publicado). Restrito a admin/técnico
- **GET** `/articles` - Lista artigos visíveis ao usuário, opcionalmente filtrando por categoria
- **GET** `/articles/search` - Busca artigos por relevância (título, conteúdo e tags, com suporte a termos em português e inglês)
- **GET** `/articles/{article_id}` - Consulta um artigo específico
- **PATCH** `/articles/{article_id}` - Atualiza um artigo (inclusive publicar/despublicar). Restrito a admin/técnico

---

### service-catalog - Catálogo de serviços com formulários tipados e fluxo de aprovação.

- **POST** `/service-catalog` - Cria um item do catálogo de serviços. Restrito a administradores
- **GET** `/service-catalog` - Lista itens do catálogo visíveis ao usuário
- **GET** `/service-catalog/{item_id}` - Consulta um item específico do catálogo
- **PATCH** `/service-catalog/{item_id}` - Atualiza um item do catálogo (inclusive ativar/desativar). Restrito a administradores
- **POST** `/service-catalog/{item_id}/fields` - Adiciona um campo de formulário ao item. Restrito a administradores
- **GET** `/service-catalog/{item_id}/fields` - Lista os campos de formulário do item
- **PATCH** `/service-catalog/{item_id}/fields/{field_id}` - Atualiza um campo de formulário existente. Restrito a administradores
- **DELETE** `/service-catalog/{item_id}/fields/{field_id}` - Remove um campo de formulário do item. Restrito a administradores

---

### automation - Motor de regras de triagem e assinaturas de webhook.

- **POST** `/triage-rules` - Cria uma regra de triagem automática (condições e ações). Restrito a administradores
- **GET** `/triage-rules` - Lista as regras de triagem cadastradas. Restrito a admin/técnico
- **PATCH** `/triage-rules/{rule_id}` - Atualiza uma regra de triagem. Restrito a administradores
- **DELETE** `/triage-rules/{rule_id}` - Remove uma regra de triagem. Restrito a administradores
- **POST** `/webhook-subscriptions` - Cria uma assinatura de webhook. Restrito a administradores
- **GET** `/webhook-subscriptions` - Lista as assinaturas de webhook cadastradas. Restrito a administradores
- **PATCH** `/webhook-subscriptions/{subscription_id}` - Atualiza uma assinatura de webhook. Restrito a administradores
- **DELETE** `/webhook-subscriptions/{subscription_id}` - Remove uma assinatura de webhook. Restrito a administradores
- **GET** `/webhook-subscriptions/deliveries` - Lista o log de tentativas de entrega de webhook. Restrito a administradores

---

### cmdb - Ativos de TI e relacionamentos de dependência (CMDB).

- **POST** `/assets` - Cadastra um novo ativo. Restrito a admin/técnico
- **GET** `/assets` - Lista ativos, opcionalmente filtrando por tipo e/ou status. Restrito a admin/técnico
- **GET** `/assets/{asset_id}` - Consulta um ativo específico. Restrito a admin/técnico
- **PATCH** `/assets/{asset_id}` - Atualiza um ativo existente. Restrito a admin/técnico
- **POST** `/assets/relationships` - Cria um relacionamento de dependência entre dois ativos. Restrito a admin/técnico
- **GET** `/assets/{asset_id}/relationships` - Lista os relacionamentos do ativo (como origem e como destino). Restrito a admin/técnico
- **DELETE** `/assets/relationships/{relationship_id}` - Remove um relacionamento entre ativos. Restrito a admin/técnico

---

### dashboard - Indicadores agregados, KPIs e exportação de dados em CSV.

- **GET** `/dashboard/overview` - Retorna volume, cumprimento de SLA e tempo médio de atendimento no período. Restrito a admin/técnico
- **GET** `/kpis/trend` - Série temporal de volume e cumprimento de SLA (granularidade: dia/semana/mês). Restrito a admin/técnico
- **GET** `/kpis/technicians` - Desempenho individual de cada técnico com chamado resolvido no período. Restrito a admin/técnico
- **GET** `/exports/tickets.csv` - Exporta a lista de chamados filtrada em CSV. Restrito a admin/técnico
- **GET** `/exports/dashboard.csv` - Exporta o dashboard agregado em CSV. Restrito a admin/técnico
- **GET** `/exports/kpi-trend.csv` - Exporta a série temporal de KPIs em CSV. Restrito a admin/técnico
- **GET** `/exports/kpi-technicians.csv` - Exporta os KPIs por técnico em CSV. Restrito a admin/técnico