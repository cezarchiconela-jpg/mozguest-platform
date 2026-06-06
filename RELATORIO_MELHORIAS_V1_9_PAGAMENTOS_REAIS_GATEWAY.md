# +258 Guest v1.9 — Pagamentos Reais, Gateway, Sandbox e Webhooks

## Objectivo

Preparar a +258 Guest para pagamentos reais sem bloquear o piloto operacional. A versão passa a ter uma arquitectura de gateway com M-Pesa e e-Mola, mantendo o envio manual de comprovativo como alternativa segura enquanto as credenciais oficiais não forem activadas.

## O que foi implementado

### 1. Nova camada de gateway

Foi criado o ficheiro:

```text
payments/gateways.py
```

A camada suporta:

- modo `sandbox`, para testes locais sem dinheiro real;
- modo `live`, para activação com credenciais oficiais;
- M-Pesa;
- e-Mola;
- consulta de estado;
- callback/webhook;
- payload genérico configurável por variáveis de ambiente.

> Nota importante: a integração live está preparada estruturalmente, mas o payload final deve ser ajustado quando a +258 Guest tiver a documentação oficial do provedor escolhido.

### 2. Nova tabela de transacções

Foi criado o modelo:

```text
PaymentTransaction
```

A transacção regista:

- gateway usado;
- estado da transacção;
- valor;
- número de telefone que autoriza o pagamento;
- referência única +258 Guest;
- referência externa do provedor;
- resposta do provedor;
- erros;
- data de callback;
- data de confirmação.

### 3. Nova migração

Foi adicionada a migração:

```text
payments/migrations/0002_alter_payment_status_paymenttransaction.py
```

Esta migração adiciona a tabela de transacções e novos estados de pagamento.

### 4. Novas rotas de pagamento

Foram adicionadas rotas para:

```text
/pagamentos/reserva/<id>/gateway/<gateway>/iniciar/
/pagamentos/transaccao/<id>/
/pagamentos/transaccao/<id>/consultar/
/pagamentos/transaccao/<id>/simular-sucesso/
/pagamentos/webhook/<gateway>/
/pagamentos/admin/transaccoes/
```

### 5. Fluxo do cliente

Na página de pagamento da reserva, o cliente agora vê:

- pagar com M-Pesa;
- pagar com e-Mola;
- enviar comprovativo manual.

Em modo sandbox, o cliente pode iniciar o pagamento e simular confirmação para testar o ciclo completo.

### 6. Fluxo administrativo

Foi criada a página administrativa:

```text
/pagamentos/admin/transaccoes/
```

Ela permite ver:

- total de transacções;
- transacções aguardando autorização;
- transacções pagas;
- transacções falhadas;
- gateway;
- referência +258 Guest;
- referência do provedor;
- telefone;
- data de callback;
- estado.

### 7. Webhook/callback

Foi implementado endpoint genérico:

```text
/pagamentos/webhook/mpesa/
/pagamentos/webhook/emola/
```

O webhook aceita JSON com referências e estado. Pode ser protegido com token configurado em:

```env
GUEST258_GATEWAY_CALLBACK_TOKEN=
```

Quando o callback indicar pagamento confirmado, o sistema:

- marca a transacção como paga;
- confirma o pagamento;
- regista referência externa;
- notifica cliente;
- notifica proprietário;
- actualiza relatórios financeiros.

### 8. Novas variáveis de ambiente

```env
GUEST258_PAYMENT_GATEWAY_MODE=sandbox
GUEST258_GATEWAY_CALLBACK_TOKEN=
MPESA_INITIATE_URL=
MPESA_QUERY_URL=
MPESA_TOKEN=
MPESA_API_KEY=
MPESA_SERVICE_PROVIDER_CODE=
EMOLA_INITIATE_URL=
EMOLA_QUERY_URL=
EMOLA_TOKEN=
EMOLA_API_KEY=
EMOLA_SERVICE_PROVIDER_CODE=
```

## Como testar localmente

Depois de extrair o projecto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.local.example .env -Force
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

Teste o ciclo:

1. Cliente tem reserva aceite.
2. Cliente abre `Minhas reservas`.
3. Clica em `Pagar / Enviar comprovativo`.
4. Escolhe M-Pesa ou e-Mola.
5. Informa número de telefone.
6. Inicia pagamento.
7. Em sandbox, clica em `Simular confirmação`.
8. Confirma se o pagamento passa para `Confirmado`.
9. Admin verifica `/pagamentos/admin/transaccoes/`.

## Validação feita

A versão passou em:

```text
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
```

Também foi testado o fluxo sandbox com:

- criação de transacção M-Pesa;
- estado aguardando autorização;
- simulação de confirmação;
- pagamento confirmado;
- página administrativa de transacções.

## Observação crítica

Esta versão deixa a +258 Guest tecnicamente preparada para pagamentos reais, mas a activação live exige:

- conta empresarial no provedor;
- credenciais oficiais;
- endpoints oficiais;
- callback público HTTPS;
- eventual adaptação do payload em `payments/gateways.py` conforme documentação do provedor.

Enquanto isso, a +258 Guest pode operar com:

- sandbox para teste;
- comprovativo manual para operação piloto;
- activação gradual de gateway real quando as credenciais estiverem disponíveis.
