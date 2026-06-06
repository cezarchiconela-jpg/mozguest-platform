# +258 Guest v2.1 — Auditoria, Recibos, KYC e Segurança Financeira

## Objectivo da versão

Esta versão reforça a +258 Guest para uma fase mais séria de operação real, especialmente porque o sistema passa a controlar dinheiro pago pelos clientes e valores a liquidar aos proprietários.

O foco desta versão foi fechar quatro áreas críticas:

1. Auditoria de acções sensíveis.
2. Recibos/comprovativos financeiros.
3. Verificação/KYC dos proprietários.
4. Cancelamentos, reembolsos e relatório financeiro diário.

## Principais melhorias implementadas

### 1. Auditoria operacional

Foi criado o modelo `AuditLog`, no módulo `dashboard`, para registar acções sensíveis, incluindo:

- aprovação/rejeição de propriedades;
- alteração de destaque de propriedades;
- aprovação/rejeição de avaliações;
- aceitação/rejeição/cancelamento/conclusão de reservas;
- confirmação/rejeição de pagamentos;
- liquidação paga ao proprietário;
- liquidação retida;
- verificação/rejeição/suspensão de proprietários;
- análise de cancelamento/reembolso.

Nova página administrativa:

```text
/258-admin/auditoria/
```

### 2. Verificação/KYC dos proprietários

O `OwnerProfile` foi reforçado com dados de verificação e liquidação:

- estado de verificação expandido;
- dados bancários para liquidação;
- número M-Pesa;
- número e-Mola;
- documento de identificação;
- comprovativo de NUIT;
- comprovativo de titularidade/autorização do alojamento;
- notas de verificação;
- data e utilizador que verificou.

Nova página do proprietário:

```text
/proprietario/verificacao/
```

Nova página administrativa:

```text
/258-admin/proprietarios/
```

### 3. Recibo de pagamento do cliente

Foi adicionada uma página de recibo +258 Guest para pagamentos confirmados:

```text
/pagamentos/recibo/<payment_id>/
```

O recibo mostra:

- número do pagamento;
- cliente;
- reserva;
- alojamento;
- valor pago;
- método;
- referência;
- estado confirmado.

A página é preparada para impressão ou guardar em PDF pelo navegador.

### 4. Comprovativo de liquidação ao proprietário

Foi adicionada uma página de comprovativo de liquidação:

```text
/pagamentos/proprietario/liquidacoes/<payout_id>/recibo/
```

Mostra:

- valor bruto pago pelo cliente;
- comissão +258 Guest;
- valor líquido pago ao proprietário;
- método de liquidação;
- referência;
- data de liquidação.

### 5. Cancelamentos e reembolsos

A reserva agora possui campos próprios para controlo de cancelamento/reembolso:

- cancelada por;
- motivo do cancelamento;
- data do cancelamento;
- estado de reembolso;
- valor de reembolso;
- referência;
- notas;
- utilizador que analisou;
- data de análise.

Nova página administrativa:

```text
/pagamentos/admin/cancelamentos-reembolsos/
```

Quando uma reserva paga é cancelada, o estado de reembolso passa para análise.

### 6. Relatório financeiro diário

Foi criada uma página para visão diária de movimentos financeiros:

```text
/pagamentos/admin/relatorio-diario/
```

Mostra:

- total recebido de clientes;
- comissão +258 Guest;
- valor dos proprietários;
- total já liquidado;
- total pendente;
- total retido;
- resumo por dia.

## Novas migrações

Esta versão cria novas migrações nos módulos:

```text
accounts
bookings
dashboard
```

Por isso, no teste local ou deploy, é obrigatório executar:

```powershell
python manage.py migrate
```

## Validação técnica realizada

Foram executados com sucesso:

```powershell
python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Também foram testadas com Django Test Client as páginas:

```text
/proprietario/verificacao/
/258-admin/proprietarios/
/258-admin/auditoria/
/pagamentos/admin/relatorio-diario/
/pagamentos/admin/cancelamentos-reembolsos/
/pagamentos/recibo/<id>/
/pagamentos/proprietario/liquidacoes/<id>/recibo/
```

## Observação importante

Esta versão aumenta bastante a segurança operacional, mas para produção real ainda é essencial configurar:

- PostgreSQL;
- armazenamento persistente/externo de media e comprovativos;
- domínio real em HTTPS;
- variáveis de ambiente de produção;
- credenciais oficiais de gateway de pagamento;
- backups da base de dados.
