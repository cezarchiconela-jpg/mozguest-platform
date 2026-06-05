# Relatório — +258 Guest v2.2: Produção Final, Deploy, Storage, Backups e Lançamento Controlado

## Objectivo

Fechar a fase técnica de preparação para operação real controlada da +258 Guest, reforçando deploy, segurança operacional, backups, health checks, logs e documentação de produção.

## Melhorias aplicadas

### 1. Health checks

Foram adicionadas duas rotas técnicas:

- `/healthz/` — verifica se a aplicação Django está viva.
- `/readyz/` — verifica se a aplicação está pronta e se a base de dados responde.

Estas rotas ajudam no Render, monitorização e diagnóstico rápido.

### 2. Configuração de storage

O `settings.py` foi preparado para:

- storage local;
- disco persistente;
- storage S3 compatível.

Foram adicionadas variáveis para AWS S3, Cloudflare R2, Wasabi, Backblaze B2 ou outro serviço compatível com S3.

### 3. Logs operacionais

Foi adicionado logging estruturado para consola e ficheiro com rotação. Isto ajuda a acompanhar erros, incidentes e actividade técnica em produção.

### 4. Comando de verificação de produção

Novo comando:

```bash
python manage.py guest258_production_check
```

Ele verifica:

- `DEBUG`;
- `SECRET_KEY`;
- hosts permitidos;
- CSRF;
- HTTPS/cookies;
- base de dados;
- storage;
- e-mail;
- gateway de pagamento.

### 5. Comando de backup

Novo comando:

```bash
python manage.py guest258_backup --include-media
```

Cria backup lógico da base de dados, manifesto de media e checksums.

### 6. Smoke test

Novo comando:

```bash
python manage.py guest258_smoke_test
```

Valida rapidamente as páginas principais e evita publicar uma versão que nem sequer abre as rotas básicas.

### 7. Deploy Render

Foram adicionados:

- `build.sh`;
- `Procfile` actualizado;
- `render.yaml`;
- `README_DEPLOY_RENDER.md`.

### 8. Limpeza e segurança do repositório

Foi adicionado `.gitignore` para evitar envio de:

- base de dados local;
- ficheiros carregados;
- logs;
- backups;
- ambiente virtual;
- `.env`.

### 9. Runbook e checklist de lançamento

Foram adicionados:

- `RUNBOOK_BACKUP_RESTORE_+258 GUEST.md`;
- `CHECKLIST_LANCAMENTO_CONTROLADO_+258 GUEST.md`.

## Estado final

A v2.2 deixa a +258 Guest pronta para teste piloto online controlado, desde que sejam configurados correctamente:

- PostgreSQL;
- storage de uploads;
- SMTP real;
- domínio HTTPS;
- variáveis de ambiente;
- backup operacional.

## Recomendação

Depois de instalar a v2.2 localmente, executar:

```bash
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py guest258_smoke_test
```

Antes do lançamento online, executar no servidor:

```bash
python manage.py guest258_production_check
```
