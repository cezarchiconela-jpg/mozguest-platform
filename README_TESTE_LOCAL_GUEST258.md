# Teste local do +258 Guest

Este ficheiro explica como testar o +258 Guest localmente antes de actualizar o GitHub/Render.

## 1. Abrir a pasta do projecto

Depois de extrair o ZIP, abrir o PowerShell dentro da pasta onde existe o ficheiro `manage.py`.

## 2. Criar ambiente virtual

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a activação, executar uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois activar novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Criar ficheiro .env local

Copiar o conteúdo do ficheiro `.env.local.example` para um novo ficheiro chamado `.env`.

Ou, pelo PowerShell:

```powershell
Copy-Item .env.local.example .env
```

## 5. Validar o projecto

```powershell
python manage.py check
```

## 6. Criar a base de dados local

```powershell
python manage.py migrate
```

## 7. Criar utilizador administrador

```powershell
python manage.py createsuperuser
```

## 8. Preparar ficheiros estáticos

```powershell
python manage.py collectstatic --noinput
```

## 9. Arrancar o servidor local

```powershell
python manage.py runserver
```

Abrir no navegador:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/login/
- http://127.0.0.1:8000/properties/explorar/
- http://127.0.0.1:8000/258-admin/
- http://127.0.0.1:8000/admin/


## 9.1. Teste rápido da aplicação

```powershell
python manage.py guest258_smoke_test
```

Também pode abrir:

- http://127.0.0.1:8000/healthz/
- http://127.0.0.1:8000/readyz/

## 10. Checklist de teste manual

Testar:

- cadastro de cliente;
- cadastro de proprietário;
- login/logout;
- criação de propriedade;
- criação de quarto/unidade;
- upload de fotografias;
- definição de fotografia principal;
- pesquisa/exploração pública;
- pedido de reserva;
- aceitação/rejeição de reserva pelo proprietário;
- envio de comprovativo de pagamento;
- confirmação/rejeição de pagamento no +258 Admin;
- avaliações;
- mensagens;
- suporte;
- planos comerciais.
