# +258 Guest v2.4.1 — Deploy no Render e Produção Final

Este guia deve ser usado depois de o teste local passar sem erros.

## 1. Checklist antes do GitHub

Confirmar que o repositório **não contém**:

- `db.sqlite3`
- pasta `media/`
- pasta `staticfiles/`
- pasta `logs/`
- pasta `backups/`
- ficheiro `.env`
- ficheiros `__pycache__` e `.pyc`

A v2.4.1 inclui `.gitignore` para evitar estes ficheiros.

## 2. Comandos locais antes de enviar ao GitHub

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.local.example .env -Force
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py guest258_smoke_test
```

Se tudo passar, pode enviar ao GitHub.

## 3. Variáveis obrigatórias no Render

No serviço Web do Render, configurar:

```env
GUEST258_VERSION=2.4.1
GUEST258_ENVIRONMENT=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<gerada pelo Render ou manualmente>
DJANGO_ALLOWED_HOSTS=guest258.onrender.com,258guest.co.mz,www.258guest.co.mz
DJANGO_CSRF_TRUSTED_ORIGINS=https://guest258.onrender.com,https://258guest.co.mz,https://www.258guest.co.mz
DATABASE_URL=<PostgreSQL Render>
DB_SSL_REQUIRE=True
DJANGO_SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
GUEST258_PAYMENT_GATEWAY_MODE=sandbox
GUEST258_GATEWAY_CALLBACK_TOKEN=<token-longo-aleatorio>
GUEST258_PUBLIC_BASE_URL=https://258guest.co.mz
```

## 4. Build e start command

A v2.4.1 inclui:

- `build.sh`
- `Procfile`
- `render.yaml`

Build command recomendado:

```bash
./build.sh
```

Start command recomendado:

```bash
python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-2} --timeout 120 --log-file -
```

## 5. PostgreSQL

Em produção, usar PostgreSQL. Não usar SQLite para operação real.

Depois de configurar `DATABASE_URL`, validar:

```bash
python manage.py migrate --noinput
python manage.py guest258_production_check --strict
```

## 6. Storage de imagens, KYC e comprovativos

A v2.4.1 suporta duas opções:

### Opção A — Render Persistent Disk

Mais simples para piloto controlado.

Configurar:

```env
GUEST258_STORAGE_BACKEND=local
DJANGO_MEDIA_ROOT=/opt/render/project/src/media
DJANGO_SERVE_MEDIA=False
```

Neste caso, o ideal é servir `/media/` via Nginx/serviço externo ou configurar uma camada própria para ficheiros. Para piloto inicial pode funcionar com disco persistente, mas não é a solução mais escalável.

### Opção B — Storage S3 compatível

Melhor para produção.

Instalar dependências opcionais:

```bash
pip install -r requirements-storage-s3.txt
```

Configurar:

```env
GUEST258_STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>
AWS_STORAGE_BUCKET_NAME=<bucket>
AWS_S3_REGION_NAME=<regiao>
AWS_S3_ENDPOINT_URL=<endpoint-se-nao-for-aws>
AWS_S3_CUSTOM_DOMAIN=<dominio-cdn-opcional>
AWS_QUERYSTRING_AUTH=False
AWS_DEFAULT_ACL=private
```

## 7. SMTP real

Antes do lançamento real, substituir o console backend:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=+258 Guest <no-reply@258guest.co.mz>
EMAIL_HOST=<smtp>
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<senha-ou-app-password>
GUEST258_SUPPORT_EMAILS=suporte@258guest.co.mz,operacao@258guest.co.mz
```

## 8. Pagamentos reais

Enquanto não houver credenciais oficiais, manter:

```env
GUEST258_PAYMENT_GATEWAY_MODE=sandbox
```

Quando houver credenciais reais:

```env
GUEST258_PAYMENT_GATEWAY_MODE=live
MPESA_INITIATE_URL=
MPESA_QUERY_URL=
MPESA_TOKEN=
MPESA_API_KEY=
MPESA_SERVICE_PROVIDER_CODE=
```

Não activar `live` sem fazer uma transacção controlada de teste.

## 9. Health checks

A v2.4.1 inclui:

- `/healthz/` — confirma que a aplicação está viva.
- `/readyz/` — confirma que a aplicação e a base de dados estão prontas.

No Render, usar `/healthz/` como health check.

## 10. Pós-deploy

Depois do deploy:

```bash
python manage.py createsuperuser
python manage.py guest258_production_check
python manage.py guest258_smoke_test --host 258guest.co.mz
```

Depois abrir no navegador:

- `/`
- `/properties/explorar/`
- `/258-admin/`
- `/pagamentos/admin/financeiro/`
- `/pagamentos/admin/liquidacoes/`
- `/258-admin/auditoria/`

