# +258 Guest v1.8 — Comunicação, Notificações, Suporte e E-mails Operacionais

## Objectivo da versão

Esta versão melhora a capacidade operacional da +258 Guest, tornando o sistema mais preparado para funcionamento real com clientes, proprietários e administração. O foco foi reforçar comunicação, notificações, suporte e avisos por e-mail, sem alterar a base de dados.

## Melhorias implementadas

### 1. Comunicação entre cliente e proprietário

- Centro de mensagens redesenhado para trabalhar por reserva.
- Novos indicadores rápidos:
  - total de conversas;
  - mensagens não lidas;
  - reservas pendentes;
  - reservas aceites;
  - conversas com pagamento associado.
- Novo filtro “com pagamento”.
- Conversas recentes no painel lateral.
- Página de conversa com resumo operacional da reserva:
  - estado;
  - valor estimado;
  - número de mensagens;
  - próxima acção recomendada.
- Respostas rápidas adaptadas ao papel do utilizador:
  - cliente;
  - proprietário;
  - estado pendente;
  - estado aceite.
- Envio de e-mail automático à outra parte quando há nova mensagem, quando o e-mail estiver configurado.

### 2. Notificações internas

- Central de notificações melhorada com pesquisa por título, mensagem e link.
- Novos cartões de resumo:
  - total;
  - não lidas;
  - reservas;
  - pagamentos;
  - suporte.
- Alerta operacional quando existem notificações não lidas de reserva ou pagamento.
- Painel lateral com últimas notificações não lidas.
- Rotina diária recomendada para operação.

### 3. Suporte e reclamações

- Área de suporte redesenhada com visão mais clara.
- Novo indicador de tickets urgentes.
- Botão opcional para WhatsApp de suporte, configurável por variável de ambiente.
- Página de detalhe da reclamação com próxima acção recomendada.
- Criação de ticket agora gera:
  - notificação para staff;
  - e-mail para equipa de suporte, quando configurado;
  - e-mail de confirmação para o utilizador, quando configurado.
- Resposta administrativa agora envia:
  - notificação interna ao utilizador;
  - e-mail ao utilizador, se configurado.
- Painel administrativo de suporte melhorado com filtros, pesquisa e visão operacional.

### 4. Serviços de comunicação

Foram criadas funções auxiliares para:

- normalização de números de Moçambique para WhatsApp;
- geração de links WhatsApp;
- criação de mensagens padronizadas de reserva;
- criação de mensagens padronizadas de suporte;
- envio de e-mails simples;
- envio para múltiplos e-mails de suporte;
- geração de URLs absolutas usando domínio público ou request.

### 5. Variáveis de ambiente adicionadas

Foram adicionadas ao `.env.example` e `.env.local.example`:

```env
GUEST258_SUPPORT_WHATSAPP=
GUEST258_SUPPORT_EMAILS=
GUEST258_PUBLIC_BASE_URL=https://258guest.co.mz
GUEST258_EMAIL_NOTIFICATIONS_ENABLED=True
```

Em teste local:

```env
GUEST258_PUBLIC_BASE_URL=http://127.0.0.1:8000
```

## Validação técnica

A versão foi validada com:

```bash
python -m compileall -q .
python manage.py check
```

Resultado:

```text
System check identified no issues (0 silenced).
```

Também foram testadas com Django Test Client as páginas:

```text
/notificacoes/
/mensagens/
/suporte/
/suporte/novo/
/258-admin/suporte/
```

Todas responderam com sucesso.

## Observação importante

Esta versão não altera modelos nem cria novas migrações. Portanto, é segura para testar com a base de dados actual.

