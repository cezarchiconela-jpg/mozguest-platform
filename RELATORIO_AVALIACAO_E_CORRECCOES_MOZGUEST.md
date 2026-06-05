# +258 Guest — Avaliação e Correcções de Estabilização

## Objectivo desta versão
Esta versão prepara o projecto para uma entrada mais séria em funcionamento, corrigindo riscos técnicos imediatos e melhorando o fluxo de uso sem reescrever o sistema do zero.

## Correcções aplicadas

### 1. Segurança de produção
- `DEBUG` deixou de ficar activo por defeito.
- `SECRET_KEY` passou a ser obrigatória quando `DEBUG=False`.
- `ALLOWED_HOSTS` passou a ser obrigatório em produção.
- `CSRF_TRUSTED_ORIGINS` pode ser gerado automaticamente a partir dos hosts em HTTPS quando não for definido.
- Activadas configurações reforçadas de cookies seguros, HTTPS, HSTS, protecção contra sniffing e `X_FRAME_OPTIONS`.
- Login de utilizador `staff` agora entra no painel MozAdmin em vez de ir directamente para o Django Admin.

### 2. Media/uploads
- Criada variável `DJANGO_MEDIA_ROOT` para permitir usar persistent disk no Render.
- Criada variável `DJANGO_MEDIA_URL`.
- Criada variável `DJANGO_SERVE_MEDIA` para permitir servir media em ambiente controlado.
- Actualizado `config/urls.py` para servir media quando `DJANGO_SERVE_MEDIA=True`.

### 3. Acções sensíveis por POST
Foram corrigidas várias acções que alteravam dados por simples link GET. Agora exigem POST + CSRF:
- Aprovar/rejeitar propriedades.
- Aprovar/rejeitar avaliações.
- Confirmar/rejeitar pagamentos.
- Aceitar/rejeitar/concluir reservas.
- Cancelar reserva do cliente.
- Activar/desactivar quarto.
- Definir foto principal.
- Apagar foto.
- Apagar bloqueio de disponibilidade.
- Solicitar plano comercial.
- Activar/cancelar subscrição comercial.
- Marcar todas notificações como lidas.
- Adicionar/remover favoritos.

### 4. Reservas
- O formulário de reserva foi reorganizado em 3 passos: dados do cliente, período e observações.
- Adicionado cálculo visual do valor estimado em tempo real no lado do cliente.
- O backend agora rejeita tipo de reserva sem preço definido.
- Proprietário só pode aceitar/rejeitar reservas pendentes.
- Proprietário só pode concluir reservas aceites.

### 5. Pagamentos
- O cliente deixou de poder alterar livremente o valor da reserva.
- O valor pago passa a ser fixado pelo valor estimado da reserva.
- A comissão passa a ser obtida do plano comercial activo do proprietário.
- Validação reforçada do comprovativo de pagamento: imagem válida e limite de 5 MB.

### 6. Planos comerciais
- Criado `monetization/services.py` para centralizar regras de plano.
- Aplicado limite de propriedades por proprietário conforme plano activo.
- Aplicado limite de fotografias por propriedade conforme plano activo.
- Pedido duplicado de plano igual passou a ser bloqueado.
- Activar uma subscrição cancela outras subscrições activas do mesmo proprietário.

### 7. Limpeza recomendada do repositório
Esta versão deve ser publicada sem:
- `db.sqlite3`
- `media/`
- `staticfiles/`
- `__pycache__/`
- `*.pyc`
- ficheiros de backup e diagnóstico temporários

## Pontos ainda pendentes para fase seguinte
1. Migrar produção para PostgreSQL definitivo.
2. Definir estratégia final de armazenamento de media: Render Persistent Disk, Cloudinary, Supabase Storage ou S3.
3. Melhorar MozAdmin para listar clientes, proprietários, propriedades, reservas, pagamentos e suporte numa única área operacional.
4. Criar fluxo de pagamento mais formal com referência única por reserva.
5. Criar recibos/facturas simples em PDF.
6. Melhorar homepage, exploração de alojamentos e página de detalhe com foco comercial.
7. Criar dashboard executivo com métricas reais de conversão e ocupação.
8. Adicionar testes automatizados para reservas, pagamentos, planos e permissões.

## Variáveis mínimas no Render

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=uma-chave-longa-e-segura
DJANGO_ALLOWED_HOSTS=mozguest-platform.onrender.com,seudominio.com,www.seudominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://mozguest-platform.onrender.com,https://seudominio.com,https://www.seudominio.com
DATABASE_URL=postgresql://...
DJANGO_SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
DJANGO_MEDIA_ROOT=/opt/render/project/src/media
DJANGO_SERVE_MEDIA=True
```

## Nota importante
`DJANGO_SERVE_MEDIA=True` resolve a visualização dos ficheiros carregados em ambiente controlado, mas para operação séria é melhor usar armazenamento persistente ou externo. Sem persistent disk/Cloudinary/S3, uploads podem perder-se em novo deploy.
