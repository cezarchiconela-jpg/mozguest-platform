# +258 Guest v1.7 — Página Pública, Confiança, Avaliações e Conversão

## Objectivo da versão

Esta versão aprofunda a experiência do cliente na página pública do alojamento, reforçando confiança, clareza de preços, avaliações e acções de conversão para reserva/WhatsApp.

## Melhorias implementadas

### 1. Página pública do alojamento redesenhada
- Hero mais forte e comercial.
- Preços resumidos logo no topo.
- Botões directos para reservar e contactar via WhatsApp.
- Galeria ampliada mantendo modal de visualização.
- Blocos explicativos de fluxo seguro: escolher, solicitar, pagar depois de aceite.

### 2. Confiança e transparência
- Novo bloco “Confiança e transparência”.
- Badges automáticos para:
  - propriedade verificada;
  - localização no mapa;
  - galeria com fotografias reais;
  - contacto directo;
  - unidades disponíveis;
  - avaliações aprovadas.

### 3. WhatsApp mais seguro
- Normalização automática de números de WhatsApp para links `wa.me`.
- Suporte a formatos locais comuns de Moçambique.
- Mensagem pré-preenchida mais profissional.

### 4. Quartos/unidades com maior foco em conversão
- Cada quarto mostra o menor preço disponível.
- Preços são apresentados como opções claras.
- Botões de “Solicitar reserva” e “Perguntar no WhatsApp” mais evidentes.
- Melhor separação visual de comodidades como Wi-Fi, ar condicionado, estacionamento e WC privativo.

### 5. Avaliações melhoradas
- Resumo de avaliação com nota média e classificação textual.
- Distribuição por estrelas.
- Médias por categoria:
  - limpeza;
  - segurança;
  - localização;
  - conforto;
  - atendimento;
  - preço/qualidade.
- Formulário de avaliação redesenhado e mais claro.

### 6. Pesquisa pública melhorada
- Cards de alojamento passam a mostrar pequenos sinais de confiança.
- WhatsApp dos cards usa URL normalizada.
- Descrição com melhor controlo visual para evitar cards desequilibrados.

### 7. Reserva com reforço de segurança
- Adicionado bloco explicando o fluxo seguro +258 Guest no formulário de reserva.
- Cliente é novamente orientado a não pagar antes da confirmação do proprietário.

## Validação executada

- `python manage.py check` passou sem erros.
- Migrações aplicadas localmente em base de teste.
- Páginas renderizadas com Django Test Client:
  - `/`
  - `/properties/explorar/`
  - `/properties/1/`
  - `/reservas/novo/1/`
- A página de avaliação redirecciona correctamente para login quando o utilizador não está autenticado.

## Observação técnica

Esta versão não altera modelos de base de dados e não exige novas migrações.
