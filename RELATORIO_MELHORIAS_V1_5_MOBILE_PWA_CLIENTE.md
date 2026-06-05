# Relatório de Melhorias — +258 Guest v1.5 Mobile, PWA e Experiência do Cliente

## Objectivo da versão

Esta versão melhora a utilização da +258 Guest no telemóvel e torna a jornada do cliente mais simples, rápida e amigável. A prioridade foi reforçar a experiência pública, o detalhe do alojamento, o formulário de reserva e a instalação como aplicação PWA, sem alterar a base de dados.

## Melhorias implementadas

### 1. Navegação mobile

- Criada barra inferior fixa para telemóvel com atalhos rápidos.
- Acesso rápido a Início, Explorar, Reservas/Painel, Central e Menu.
- Indicador de notificações visível na navegação mobile.
- Melhor adaptação a ecrãs com safe area, incluindo iPhone.

### 2. PWA e comportamento offline

- Actualizado `manifest.json` com melhor descrição e atalhos de aplicação.
- Criada página offline em `static/offline.html`.
- Actualizado `service-worker.js` para cache mais controlado.
- Evitado cache de páginas sensíveis, como reservas, pagamentos, mensagens, notificações, proprietário, admin e login.
- Adicionado aviso visual quando o utilizador fica offline.
- Criado banner flutuante para instalação da aplicação quando o navegador permite.

### 3. Página Explorar alojamentos

- Hero mais orientado ao uso mobile.
- Pesquisa principal mais simples e directa.
- Filtros avançados recolhíveis no telemóvel.
- Botões Lista/Mapa no telemóvel.
- Melhor experiência de localização “Perto de mim”.
- Cards de alojamento mais claros, com CTA de detalhes e WhatsApp.
- Empty state mantido e melhor integrado com localização.

### 4. Página de detalhe do alojamento

- Galeria melhorada com visual mais premium.
- Fotografias clicáveis com modal de ampliação.
- Secção “como funciona” em 3 passos: escolher, solicitar e pagar.
- CTA fixo no telemóvel para Reservar/WhatsApp.
- Quarto/unidade com cards mais claros, preços mais legíveis e botões directos.
- Reforçada a mensagem de que o cliente só deve pagar depois de a reserva ser aceite.

### 5. Formulário de reserva

- Formulário mais guiado e visual.
- Chips de preço por hora, dia, noite e mês.
- Botão mobile fixo para enviar pedido.
- Estimativa de valor sincronizada também no rodapé mobile.
- Datas mínimas configuradas automaticamente para evitar datas passadas no browser.
- Ajuda contextual muda conforme o tipo de reserva.
- Reforçado que o pedido de reserva ainda não é pagamento.

### 6. Interface geral

- Adicionado ficheiro `static/css/guest258-ui.css` para melhorias de UX reutilizáveis.
- Melhor comportamento do menu mobile.
- Menu mobile fecha ao seleccionar opção ou pressionar Escape.
- Mensagens do sistema desaparecem automaticamente depois de alguns segundos.
- Melhorias de toque em botões para telemóvel.

## Ficheiros principais alterados

- `templates/base.html`
- `templates/public/property_list.html`
- `templates/public/property_detail.html`
- `templates/bookings/booking_form.html`
- `static/css/guest258-ui.css`
- `static/service-worker.js`
- `static/manifest.json`
- `static/offline.html`

## Impacto técnico

- Não foram alterados modelos de dados.
- Não foram criadas novas migrações.
- A versão é segura para teste local com a mesma base de dados.
- As alterações são sobretudo de templates, CSS e JavaScript.

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

Testar especialmente:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/properties/explorar/`
- detalhe de um alojamento aprovado;
- pedido de reserva;
- navegação em janela estreita/mobile;
- instalação PWA no Chrome/Edge;
- comportamento offline básico.

## Próxima fase recomendada

A próxima versão deve focar em:

1. Melhorar onboarding do proprietário.
2. Tornar o cadastro de propriedade/quartos/fotos ainda mais assistido.
3. Criar assistente de aprovação para o admin.
4. Melhorar mensagens automáticas por e-mail.
5. Preparar armazenamento definitivo de imagens em produção.
