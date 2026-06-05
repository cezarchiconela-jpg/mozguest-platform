# +258 Guest v1.3 - Melhorias no fluxo de reservas, pagamentos e notificações

## Objectivo da versão

Esta versão melhora a operação prática da +258 Guest para o ciclo real de funcionamento:

1. Cliente solicita reserva.
2. Proprietário recebe e analisa o pedido.
3. Proprietário aceita ou rejeita.
4. Cliente envia comprovativo apenas depois da reserva aceite.
5. Administração valida o pagamento.
6. Cliente e proprietário acompanham o estado da reserva e do pagamento.

A versão foi feita sem alterações de base de dados, para reduzir risco durante os testes locais.

## Melhorias principais

### 1. Reservas do cliente

- A página "Minhas reservas" foi transformada de tabela simples para cards mais claros e responsivos.
- Foram adicionados indicadores de reservas pendentes e aceites.
- Cada reserva mostra estado da reserva e estado do pagamento.
- O botão "Enviar pagamento" aparece apenas quando a reserva está aceite e ainda sem pagamento confirmado/enviado.
- O cliente recebe orientação para não pagar antes da aceitação da reserva.
- Foram mantidos os botões de mensagem, ver alojamento e cancelar reserva.

### 2. Reservas do proprietário

- A página "Reservas recebidas" foi redesenhada para cards profissionais.
- Foram adicionados contadores de total, pendentes, aceites e concluídas.
- Os filtros de estado agora funcionam no backend.
- Cada reserva mostra dados do cliente, alojamento, período, valor e estado de pagamento.
- As acções de aceitar, rejeitar e concluir continuam protegidas por POST + CSRF.

### 3. Pagamentos

- O envio de comprovativo foi redesenhado.
- A página agora mostra instruções claras de pagamento.
- Foram adicionadas variáveis de ambiente para números M-Pesa, e-Mola, dados bancários e nota de pagamento.
- O comprovativo passa a ser obrigatório quando ainda não existe comprovativo anexado.
- Foi adicionada pré-visualização da imagem do comprovativo antes do envio.
- O cliente já não consegue avançar para pagamento se a reserva ainda não estiver aceite.

### 4. Lista de pagamentos do proprietário

- A lista de pagamentos recebeu filtros funcionais por estado.
- A tabela mostra referência, comprovativo e estado de validação.
- Foram adicionados contadores de comprovativos enviados e pagamentos confirmados.

### 5. Notificações internas e e-mails

Foram adicionadas notificações para eventos importantes:

- Novo pedido de reserva enviado ao proprietário.
- Nova reserva criada enviada ao staff.
- Reserva aceite, rejeitada ou concluída enviada ao cliente.
- Reserva cancelada enviada ao proprietário.
- Comprovativo enviado ao proprietário e ao staff.
- Propriedade aprovada/rejeitada enviada ao proprietário.
- Pagamento confirmado/rejeitado enviado ao cliente e proprietário.

Em ambiente local, os e-mails usam o backend de consola, aparecendo no terminal. Em produção, dependem da configuração SMTP.

### 6. Formulário de reserva

- O formulário agora só mostra tipos de reserva que têm preço configurado no quarto/unidade.
- Quando o cliente está autenticado, o sistema tenta preencher nome, e-mail e telefone do perfil.

## Variáveis de ambiente adicionadas

Adicionar no `.env`, Render ou ambiente de produção conforme necessário:

```env
GUEST258_MPESA_NUMBER=
GUEST258_EMOLA_NUMBER=
GUEST258_BANK_DETAILS=
GUEST258_PAYMENT_NOTE=Use a referência da reserva no pagamento e envie o comprovativo em imagem legível.
```

## Testes recomendados

Depois de extrair a versão:

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

Depois testar:

- Cadastro de proprietário.
- Cadastro de propriedade, quarto e fotos.
- Aprovação da propriedade no +258 Admin.
- Cadastro de cliente.
- Criação de reserva.
- Aceitação da reserva pelo proprietário.
- Envio de comprovativo pelo cliente.
- Confirmação/rejeição do pagamento pelo +258 Admin.
- Notificações em todas as contas.

## Observação técnica

Foi feita validação de sintaxe Python com `compileall`. O teste final com `manage.py check` deve ser feito no computador local, onde as dependências Django já foram instaladas.
