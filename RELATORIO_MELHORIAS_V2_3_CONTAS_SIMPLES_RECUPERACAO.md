# +258 Guest v2.3 — Contas Simples e Recuperação de Palavra-passe

## Objectivo

Reduzir a fricção no cadastro de clientes e proprietários, mantendo um nível mínimo de segurança e acrescentando recuperação de conta por e-mail.

## Melhorias aplicadas

### 1. Palavra-passe simplificada

- A política padrão da +258 Guest passou a aceitar palavra-passe com mínimo de 4 caracteres.
- Foram removidas, por defeito, as validações que bloqueavam passwords comuns, numéricas ou semelhantes ao nome do utilizador.
- A regra pode voltar a ser mais forte em produção com:

```env
GUEST258_SIMPLE_PASSWORDS=False
```

### 2. Cadastro mais fácil

- O campo “nome de utilizador” passou a ser opcional para clientes e proprietários.
- Se o utilizador deixar vazio, o sistema gera automaticamente um username a partir do e-mail, telefone ou nome.
- A confirmação da palavra-passe passou a ser opcional.
- Se a confirmação for preenchida, o sistema valida se coincide.
- Os textos dos formulários foram simplificados para orientar o utilizador.

### 3. Recuperação de conta

Foram adicionadas páginas completas de recuperação de palavra-passe:

```text
/password-reset/
/password-reset/enviado/
/password-reset/confirmar/<uidb64>/<token>/
/password-reset/concluido/
```

### 4. Login melhorado

- A página de login deixa claro que o utilizador pode entrar com e-mail ou nome de utilizador.
- Foi adicionado o link “Esqueci a palavra-passe”.

### 5. E-mail de recuperação

- Foi criado o template de e-mail de recuperação.
- Em ambiente local, com console backend, o link aparece no terminal.
- Em produção, exige SMTP real configurado no `.env`.

## Ficheiros principais alterados

```text
config/settings.py
accounts/forms.py
accounts/urls.py
templates/accounts/client_register.html
templates/accounts/owner_register.html
templates/accounts/login.html
templates/registration/password_reset_form.html
templates/registration/password_reset_done.html
templates/registration/password_reset_confirm.html
templates/registration/password_reset_complete.html
templates/registration/password_reset_email.html
templates/registration/password_reset_subject.txt
.env.example
.env.local.example
```

## Validação realizada

- `python manage.py check` passou sem erros.
- `python manage.py migrate --noinput` aplicado em base local.
- `python manage.py collectstatic --noinput` executado com sucesso.
- Testado cadastro de cliente com username vazio, password `1234` e confirmação vazia.
- Testado cadastro de proprietário com username vazio, password simples e confirmação vazia.
- Testadas as páginas de login, cadastro e recuperação de palavra-passe.

## Observação operacional

Para que a recuperação de palavra-passe funcione com clientes reais, é necessário configurar SMTP real:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=+258 Guest <no-reply@258guest.co.mz>
```
