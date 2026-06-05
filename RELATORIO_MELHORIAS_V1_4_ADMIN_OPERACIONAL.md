# +258 Guest v1.4 — Admin Operacional e Controlo de Qualidade

## Objectivo da versão

Esta versão reforça o controlo interno da +258 Guest antes do início efectivo de funcionamento, melhorando a capacidade do administrador acompanhar reservas, propriedades, pagamentos e pontos críticos da operação.

A versão não altera a base de dados e não cria novas migrações.

## Melhorias implementadas

### 1. Novo Centro Operacional +258 Guest

O painel `/258-admin/` foi redesenhado para funcionar como centro de comando da plataforma, incluindo:

- número total de acções pendentes;
- propriedades pendentes;
- reservas pendentes;
- comprovativos de pagamento por validar;
- avaliações pendentes;
- utilizadores totais;
- clientes e proprietários cadastrados;
- propriedades aprovadas, rejeitadas, suspensas e em destaque;
- reservas aceites, concluídas, canceladas e rejeitadas;
- valores financeiros confirmados;
- lista de reservas recentes;
- lista de propriedades recentes;
- alertas de propriedades sem fotografias;
- alertas de propriedades sem quartos/unidades.

### 2. Nova área administrativa de reservas

Foi criada a página:

`/258-admin/reservas/`

Esta página permite ao administrador:

- ver todas as reservas da plataforma;
- filtrar por estado;
- pesquisar por cliente, telefone, e-mail, propriedade, cidade ou quarto;
- ver dados do cliente;
- ver propriedade e proprietário;
- ver estado da reserva;
- ver estado do pagamento associado;
- abrir a conversa da reserva;
- abrir o alojamento público;
- abrir edição avançada no Django Admin.

### 3. Gestão de propriedades melhorada

A página `/258-admin/propriedades/` deixou de mostrar apenas pendentes e passou a funcionar como gestão operacional completa, com:

- filtros por estado;
- pesquisa por nome, cidade, bairro, proprietário ou e-mail;
- cartões com detalhes da propriedade;
- contagem de quartos/unidades;
- contagem de fotografias;
- estado de verificação;
- estado de destaque;
- botão para aprovar e verificar;
- botão para rejeitar;
- botão para colocar/remover destaque;
- link para ver a página pública;
- link para edição avançada no Django Admin.

### 4. Gestão de pagamentos melhorada

A página `/258-admin/pagamentos/` foi melhorada com:

- filtros por estado;
- pesquisa por cliente, referência, propriedade e proprietário;
- visão em cartões;
- valores separados entre valor pago, comissão +258 Guest e valor do proprietário;
- estado do pagamento com cores claras;
- acesso rápido ao comprovativo;
- acções de confirmar/rejeitar;
- acesso à reserva relacionada;
- acesso ao Django Admin.

### 5. Navegação administrativa melhorada

Foi adicionado o atalho `Reservas Admin` nos menus administrativos para facilitar o acesso rápido à nova central de reservas.

## Como testar

Depois de extrair a versão, executar:

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

Testar principalmente:

- `/258-admin/`
- `/258-admin/propriedades/`
- `/258-admin/propriedades/?status=all`
- `/258-admin/reservas/`
- `/258-admin/pagamentos/`
- `/pagamentos/admin/financeiro/`

## Observação técnica

Esta versão foi criada para melhorar operação e controlo sem aumentar risco estrutural. Por isso, não foram alterados modelos de base de dados.
