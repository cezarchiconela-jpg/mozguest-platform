# +258 Guest v2.4.1 — Rebranding Limpo

Esta versão faz a limpeza profunda do rebranding para alinhar o sistema com o nome comercial **+258 Guest**.

## Alterações principais

- Removidas referências restantes a nomes antigos nos ficheiros visíveis e técnicos.
- Painel operacional passou de rota antiga para:
  - `/258-admin/`
  - `/258-admin/propriedades/`
  - `/258-admin/reservas/`
  - `/258-admin/pagamentos/`
  - `/258-admin/auditoria/`
  - `/258-admin/proprietarios/`
- Prefixo técnico de variáveis de ambiente alterado para `GUEST258_`.
- Comandos de gestão renomeados para:
  - `guest258_production_check`
  - `guest258_backup`
  - `guest258_smoke_test`
- Ficheiro CSS da plataforma renomeado para `guest258-ui.css`.
- Cache PWA renomeada para `guest258-cache`.
- Ficheiros CSV, logs, backups, documentos e exemplos `.env` foram alinhados com a nova marca.
- `render.yaml` foi actualizado para o serviço e base de dados `guest258`.
- A marca visível continua como **+258 Guest** com o slogan:
  - `Reserve estadias com confiança em Moçambique.`

## Validação

A versão passou nos seguintes testes:

```powershell
python -m compileall -q .
DJANGO_DEBUG=True python manage.py check
DJANGO_DEBUG=True python manage.py migrate --noinput
DJANGO_DEBUG=True python manage.py collectstatic --noinput
DJANGO_DEBUG=True python manage.py guest258_smoke_test
```

Resultado do teste rápido:

- `/` — 200
- `/login/` — 200
- `/cadastro/cliente/` — 200
- `/cadastro/proprietario/` — 200
- `/properties/explorar/` — 200
- `/institucional/sobre/` — 200
- `/institucional/termos/` — 200
- `/institucional/privacidade/` — 200
- `/healthz/` — 200
- `/readyz/` — 200

## Nota operacional

A partir desta versão, usar os novos nomes nas variáveis de ambiente e comandos. Exemplos:

```env
GUEST258_VERSION=2.4.1
GUEST258_ENVIRONMENT=production
GUEST258_PUBLIC_BASE_URL=https://258guest.co.mz
GUEST258_PAYMENT_GATEWAY_MODE=sandbox
```

```powershell
python manage.py guest258_production_check
python manage.py guest258_smoke_test
python manage.py guest258_backup --include-media
```
