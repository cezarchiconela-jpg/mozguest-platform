# +258 Guest v2.2 — Checklist de Lançamento Controlado

## Antes de anunciar publicamente

- [ ] `python manage.py check` passa sem erros.
- [ ] `python manage.py migrate` aplicado.
- [ ] `python manage.py collectstatic --noinput` concluído.
- [ ] `python manage.py mozguest_production_check` revisto.
- [ ] PostgreSQL activo em produção.
- [ ] Storage de uploads definido.
- [ ] SMTP real configurado.
- [ ] Domínio HTTPS activo.
- [ ] Admin real criado.
- [ ] Página inicial abre.
- [ ] Pesquisa de alojamentos abre.
- [ ] MozAdmin abre.
- [ ] Painel financeiro abre.
- [ ] Liquidações abrem.
- [ ] Auditoria abre.

## Teste piloto mínimo

- [ ] Criar 1 proprietário real.
- [ ] Fazer KYC do proprietário.
- [ ] Criar 1 alojamento real.
- [ ] Adicionar quartos/unidades.
- [ ] Adicionar fotografias.
- [ ] Admin aprova alojamento.
- [ ] Criar 1 cliente de teste.
- [ ] Cliente solicita reserva.
- [ ] Proprietário aceita.
- [ ] Cliente paga em sandbox/manual.
- [ ] Admin confirma pagamento.
- [ ] Sistema cria liquidação.
- [ ] Admin marca liquidação como paga.
- [ ] Recibo do cliente abre.
- [ ] Recibo da liquidação abre.
- [ ] Notificações chegam.
- [ ] E-mails chegam.

## Depois do piloto

- [ ] Corrigir erros encontrados.
- [ ] Actualizar textos comerciais.
- [ ] Activar canais reais de pagamento apenas após teste controlado.
- [ ] Iniciar divulgação limitada.
