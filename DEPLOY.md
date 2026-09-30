# Guia de Deploy: VPS única com Docker Compose

Este guia descreve como publicar o Helpdesk Backend API em um único servidor Linux, usando Docker Compose e Caddy (HTTPS automático). É um guia didático: mostra as decisões e os cuidados de uma implantação real, sem a pretensão de manter uma instância pública no ar.

## Sumário

- [Guia de Deploy: VPS única com Docker Compose](#guia-de-deploy-vps-única-com-docker-compose)
  - [Sumário](#sumário)
  - [1. Visão geral da arquitetura](#1-visão-geral-da-arquitetura)
  - [2. O que foi validado e o que não foi](#2-o-que-foi-validado-e-o-que-não-foi)
  - [3. Validação local](#3-validação-local)
  - [4. Pré-requisitos](#4-pré-requisitos)
  - [5. Preparando o servidor](#5-preparando-o-servidor)
  - [6. DNS](#6-dns)
  - [7. Código e segredos](#7-código-e-segredos)
  - [8. Primeira subida](#8-primeira-subida)
  - [9. Criando o primeiro administrador](#9-criando-o-primeiro-administrador)
  - [10. Teste de fumaça](#10-teste-de-fumaça)
  - [11. Operação](#11-operação)
  - [12. Console do storage](#12-console-do-storage)
  - [13. Checklist de segurança](#13-checklist-de-segurança)
  - [14. Limitações conhecidas](#14-limitações-conhecidas)

## 1. Visão geral da arquitetura

```
Internet
   |
   v
 Caddy (portas 80/443, HTTPS automático)
   |-- api.seudominio.com   --> api:8000      (FastAPI / uvicorn)
   |-- files.seudominio.com --> storage:9000  (downloads via URL pré-assinada)

Rede interna do Docker (nenhuma porta publicada)
   api, celery-worker, celery-beat --> db (Postgres), redis, storage
   migrate       : roda "alembic upgrade head" uma vez a cada deploy
   storage-init  : cria o bucket de anexos (idempotente)
```

O storage é um servidor de objetos compatível com S3 (RustFS). A aplicação o acessa pelo SDK `minio`, usado como cliente S3; por isso as variáveis de ambiente mantêm o prefixo `MINIO_*`.

Por que dois domínios: as URLs de download de anexos são assinadas para o endereço público do storage. O navegador precisa alcançá-lo por HTTPS, e por isso ele passa pelo Caddy num subdomínio próprio.

O arquivo `docker-compose.prod.yml` é autônomo (não um override do compose de desenvolvimento) e declara `name: helpdesk-prod`. Assim ele nunca compartilha rede, containers ou volumes com a stack de desenvolvimento.

## 2. O que foi validado e o que não foi

**Verificado localmente, seguindo a seção 3:**
- build da imagem e subida completa da stack de produção;
- migrations automáticas pelo serviço `migrate` e criação do bucket pelo `storage-init`;
- healthchecks e ordem de inicialização;
- proxy reverso com HTTPS (certificado interno do Caddy, domínios `*.localhost`);
- login, upload de anexo e leitura do arquivo pela URL pré-assinada, com esquema `https`.

**Não validado (depende de um servidor real):**
- emissão de certificado Let's Encrypt (exige domínio público e DNS);
- regras de firewall do provedor de nuvem;
- backup e restauração em ambiente real;
- comportamento sob carga e dimensionamento (2 vCPU e 2 a 4 GB de RAM é uma estimativa).

## 3. Validação local

Rode a stack de produção na sua máquina, com domínios `*.localhost` (o Caddy usa uma autoridade certificadora interna para esses nomes).

```bash
# 1. Guarde o .env de desenvolvimento
cp .env .env.dev.bak

# 2. Crie um .env de teste para a stack de produção
cat > .env <<'EOF'
POSTGRES_USER=helpdesk
POSTGRES_PASSWORD=senha-local-de-teste
POSTGRES_DB=helpdesk
SECRET_KEY=chave-local-de-teste-nao-usar-em-producao
MINIO_ROOT_USER=helpdesk
MINIO_ROOT_PASSWORD=senha-storage-local
MINIO_BUCKET_NAME=helpdesk-attachments
MINIO_PUBLIC_ENDPOINT=files.localhost
MINIO_PUBLIC_SECURE=true
API_DOMAIN=api.localhost
FILES_DOMAIN=files.localhost
ACME_EMAIL=dev@example.com
EOF

# 3. Suba a stack (não colide com a de desenvolvimento: outro nome de projeto)
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps

# 4. Health check através do Caddy (-k aceita o certificado interno)
curl -k --resolve api.localhost:443:127.0.0.1 https://api.localhost/health

# 5. Crie um admin, entre em https://api.localhost/docs (aceite o aviso de
#    certificado), faça login e envie um anexo. A URL de download deve
#    começar com https://files.localhost/ e devolver o arquivo:
docker compose -f docker-compose.prod.yml exec api uv run --no-sync python -m scripts.create_admin
curl -k --resolve files.localhost:443:127.0.0.1 "<URL de download>"

# 6. Encerre (remove só os volumes desta stack) e restaure o .env de desenvolvimento
docker compose -f docker-compose.prod.yml down -v
mv .env.dev.bak .env
```

## 4. Pré-requisitos

- Um servidor Linux (Ubuntu LTS ou Debian estável) com IP público.
- Um domínio com acesso ao painel de DNS.
- Acesso SSH por chave.

## 5. Preparando o servidor

Use um usuário com `sudo`, não o `root`, no dia a dia.

**Firewall (UFW):**

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Atenção: portas publicadas pelo Docker contornam o UFW. Por isso o compose de produção publica somente 80/443 (Caddy) e o console do storage em `127.0.0.1`.

**SSH:** prefira autenticação por chave e desative a senha (`PasswordAuthentication no` em `/etc/ssh/sshd_config`, depois recarregue o serviço). Teste uma segunda sessão antes de fechar a atual.

**Docker:** instale o Docker Engine e o plugin Compose seguindo a documentação oficial (https://docs.docker.com/engine/install/) e confirme com `docker compose version`.

## 6. DNS

Crie dois registros `A` apontando para o IP do servidor:

- `api.seudominio.com`
- `files.seudominio.com`

Confirme a propagação antes da primeira subida, com `dig +short api.seudominio.com`. Tentativas repetidas com DNS errado podem esbarrar nos limites de taxa do Let's Encrypt.

## 7. Código e segredos

```bash
git clone https://github.com/thaleswillreis/helpdesk-backend-api.git
cd helpdesk-backend-api
cp .env.prod.example .env
chmod 600 .env
```

Preencha o `.env`. Gere os segredos com:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"      # SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(24))"  # senhas
```

Evite `$` nos valores (o Compose o interpreta como variável). O `.env` nunca deve ser versionado.

## 8. Primeira subida

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f caddy
```

Resultado esperado: `migrate` e `storage-init` encerrados com sucesso (exit 0), `api` saudável, e o Caddy registrando a obtenção dos certificados dos dois domínios.

## 9. Criando o primeiro administrador

```bash
docker compose -f docker-compose.prod.yml exec api uv run --no-sync python -m scripts.create_admin
```

## 10. Teste de fumaça

- `curl https://api.seudominio.com/health` deve retornar `{"status":"ok"}`.
- Abra `https://api.seudominio.com/docs`, faça login com o administrador criado e execute um fluxo curto: criar categoria, abrir chamado, enviar um anexo e abrir a URL de download (deve começar com `https://files.seudominio.com/` e devolver o arquivo).
- Confirme que o console do storage não está exposto: acessar `http://IP_DO_SERVIDOR:9011` de fora deve falhar.

## 11. Operação

**Logs:**

```bash
docker compose -f docker-compose.prod.yml logs -f api
```

A rotação de logs já está configurada (3 arquivos de 10 MB por serviço).

**Atualizar:**

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs migrate
```

O serviço `migrate` é recriado quando a imagem muda e aplica as migrations antes de a API subir.

**Rollback:** volte o código (`git checkout <commit-anterior>`) e refaça o `up -d --build`. As migrations não são revertidas automaticamente. Se a versão problemática trouxe uma migration, avalie o downgrade manual:

```bash
docker compose -f docker-compose.prod.yml run --rm migrate uv run --no-sync alembic downgrade -1
```

Alguns downgrades são com perda (por exemplo, valores de enum do Postgres não são removidos). Faça backup antes de qualquer deploy que inclua migration.

**Backup do Postgres:**

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U helpdesk -d helpdesk | gzip > backup-$(date +%F).sql.gz
```

Teste a restauração em um banco vazio (`gunzip -c backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U helpdesk -d <banco_de_teste>`) e copie os arquivos para fora do servidor: backup na mesma máquina não é backup.

**Backup dos anexos (storage):** para garantir consistência, pare o storage durante a cópia do volume:

```bash
docker compose -f docker-compose.prod.yml stop storage
docker run --rm -v helpdesk-prod_storage_data:/data -v "$(pwd)":/backup alpine \
  tar czf /backup/storage-$(date +%F).tar.gz -C /data .
docker compose -f docker-compose.prod.yml start storage
```

Enquanto o storage está parado, uploads e downloads de anexos falham. Para cópia sem parada, use uma ferramenta S3 (por exemplo, `aws s3 sync` apontando para o endpoint interno). O Redis é apenas broker de tarefas: perdê-lo descarta tarefas ainda não processadas, mas não dados de negócio.

## 12. Console do storage

O console escuta apenas em `127.0.0.1:9011` no servidor. Acesse por túnel SSH:

```bash
ssh -L 9011:127.0.0.1:9011 usuario@servidor
# depois abra http://localhost:9011 no seu navegador
```

## 13. Checklist de segurança

- SSH somente por chave, e usuário comum com `sudo`.
- UFW ativo com apenas 22, 80 e 443.
- Somente Caddy (80/443) e o console em `127.0.0.1` publicados.
- `.env` com `chmod 600`, fora do Git, com segredos únicos e fortes.
- Trocar o `SECRET_KEY` invalida todos os tokens emitidos.
- Senha do administrador forte, definida na criação.
- Imagens de infraestrutura com versão fixada (`rustfs/rustfs:1.0.0`); acompanhe as releases e atualize de forma deliberada.

## 14. Limitações conhecidas

- Os containers da aplicação rodam como `root` (a imagem não usa usuário não privilegiado nem build multi-stage).
- O RustFS é um projeto jovem (versão 1.0 em setembro de 2026). Acompanhe as releases e mantenha backups dos anexos.
- Dependência de registro público: em setembro de 2026 as imagens do MinIO foram removidas do Docker Hub, o que quebrou builds em máquinas sem cache. Espelhar as imagens de infraestrutura em um registro próprio evitaria esse risco.
- Servidor único: ponto único de falha, sem alta disponibilidade.
- Sem monitoramento nem alertas; backups são manuais.
- Sem deploy contínuo: o CI valida o código, mas a publicação é manual.