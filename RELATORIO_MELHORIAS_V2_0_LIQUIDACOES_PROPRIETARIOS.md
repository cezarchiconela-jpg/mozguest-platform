# +258 Guest v2.0 — Liquidações aos Proprietários e Controlo de Pagamentos

## Objectivo

Esta versão cria a lógica financeira correcta para uma plataforma de reservas: o cliente paga à +258 Guest, a +258 Guest confirma o pagamento, separa a comissão da plataforma e cria o valor líquido a pagar ao proprietário.

## Nova lógica operacional

1. Cliente faz reserva.
2. Proprietário aceita a reserva.
3. Cliente paga à +258 Guest por M-Pesa, e-Mola, transferência ou comprovativo manual.
4. +258 Guest confirma o pagamento.
5. O sistema calcula automaticamente:
   - valor total pago pelo cliente;
   - comissão +258 Guest;
   - valor líquido do proprietário.
6. O sistema cria automaticamente uma liquidação ao proprietário.
7. A administração da +258 Guest marca a liquidação como paga ou coloca em retenção.
8. O proprietário vê o estado do valor a receber no seu painel.

## Funcionalidades adicionadas

- Novo modelo `OwnerPayout` para liquidações aos proprietários.
- Nova migração `payments.0003_ownerpayout`.
- Criação automática de liquidação quando um pagamento passa para `confirmed`.
- Página do proprietário para acompanhar liquidações:
  - `/pagamentos/proprietario/liquidacoes/`
- Página administrativa de tesouraria:
  - `/pagamentos/admin/liquidacoes/`
- Exportação CSV de liquidações:
  - `/pagamentos/admin/liquidacoes/exportar/`
- Sincronização manual de liquidações a partir de pagamentos confirmados:
  - `/pagamentos/admin/liquidacoes/sincronizar/`
- Acções administrativas:
  - marcar liquidação como paga;
  - colocar liquidação em retenção;
  - registar método de pagamento;
  - registar referência;
  - adicionar notas administrativas.
- Notificações automáticas para proprietários e equipa administrativa.
- Actualização dos painéis financeiro e +258 Admin com indicadores de liquidação.
- Ajuste dos textos de pagamento para deixar claro que o cliente deve pagar à +258 Guest.

## Segurança e confiança

Esta versão evita que o cliente pague directamente ao proprietário como fluxo principal. A plataforma passa a controlar o dinheiro, a confirmação da reserva e a comissão, aumentando a confiança do cliente e reduzindo risco operacional.

## Validação técnica realizada

Foram executados com sucesso:

```bash
python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Também foram testadas, com Django Test Client, as páginas:

- `/258-admin/`
- `/pagamentos/admin/liquidacoes/`
- `/pagamentos/admin/financeiro/`
- `/258-admin/pagamentos/?status=confirmed`
- `/pagamentos/proprietario/liquidacoes/`
- `/pagamentos/proprietario/financeiro/`

Foi ainda testado o fluxo:

```text
Pagamento confirmado → criação automática de liquidação → marcação administrativa como paga → notificação ao proprietário.
```

## Nota importante

Esta versão cria uma nova tabela. Portanto, depois de actualizar o projecto, é obrigatório executar:

```bash
python manage.py migrate
```
