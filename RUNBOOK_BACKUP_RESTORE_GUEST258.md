# +258 Guest v2.4.1 — Runbook de Backup e Recuperação

## Objectivo

Evitar perda de dados de clientes, proprietários, reservas, pagamentos, documentos KYC e comprovativos.

## Backup manual rápido

```bash
python manage.py guest258_backup --include-media
```

O comando cria uma pasta dentro de `backups/` contendo:

- `database.json`
- `manifest.json`
- `CHECKSUMS.sha256`
- cópia de `db.sqlite3`, se estiver em SQLite
- cópia de `media/`, se `--include-media` for usado e o storage for local

## Backup em PostgreSQL

Para PostgreSQL, usar também backup nativo do provedor ou `pg_dump`:

```bash
pg_dump "$DATABASE_URL" > guest258-postgres-backup.sql
```

## Frequência recomendada

Piloto:

- backup lógico diário;
- backup antes de cada deploy;
- backup antes de migrações novas.

Produção real:

- backup automático diário;
- retenção mínima de 14 a 30 dias;
- teste de recuperação mensal.

## Recuperar dados JSON

```bash
python manage.py loaddata database.json
```

## Recuperar media local

Copiar os ficheiros de `media/` do backup para a pasta `MEDIA_ROOT` configurada no ambiente.

## Atenção

Nunca guardar backups com documentos KYC ou comprovativos em locais públicos. Estes ficheiros podem conter dados sensíveis.
