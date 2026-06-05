# +258 Guest v1.6 — Proprietário Assistido

## Objectivo da versão

Esta versão melhora a experiência do proprietário, tornando o cadastro e preparação de alojamentos mais simples, guiado e operacional. O foco foi reduzir dúvidas, aumentar a qualidade das propriedades publicadas e acelerar a aprovação pela administração.

## Melhorias implementadas

### 1. Assistente de preparação do alojamento

Foi criada uma nova página operacional por propriedade:

```text
/proprietario/propriedades/<id>/preparar/
```

Esta página apresenta um checklist automático com progresso percentual, avaliando:

- dados básicos e descrição;
- localização;
- contactos;
- quartos/unidades;
- preços;
- galeria com pelo menos 3 fotos;
- foto principal;
- aprovação pela +258 Guest.

O sistema indica a próxima acção recomendada para o proprietário.

### 2. Lista de propriedades melhorada

A página “Minhas propriedades” agora mostra:

- quantidade total de propriedades;
- quantas estão prontas/aprovadas;
- quantas precisam de atenção;
- progresso de preparação por alojamento;
- próxima acção pendente;
- botão directo “Preparar”.

### 3. Cadastro e edição de quartos/unidades melhorado

O formulário de quartos foi reorganizado em secções:

1. identificação da unidade;
2. preços;
3. comodidades;
4. fotografias.

Também foi adicionada validação para impedir unidades sem qualquer preço definido.

### 4. Duplicação de quartos/unidades

Foi criada a acção:

```text
/proprietario/quartos/<id>/duplicar/
```

Isto permite ao proprietário duplicar rapidamente uma unidade parecida e editar apenas o nome ou pequenos detalhes.

### 5. Upload múltiplo de fotografias da propriedade

A página de adicionar fotografia foi melhorada para permitir várias imagens de uma só vez, com:

- selecção múltipla;
- pré-visualização antes do envio;
- associação opcional a um quarto/unidade;
- legenda comum;
- opção para definir a primeira foto como principal;
- respeito ao limite de fotos do plano comercial.

### 6. Galeria de fotos melhorada

A galeria agora destaca melhor:

- foto principal;
- fotos gerais;
- fotos associadas a quartos/unidades;
- data de carregamento;
- acções para definir principal ou apagar.

### 7. Regras de qualidade para propriedades

O formulário de propriedade agora exige:

- pelo menos um contacto: telefone, WhatsApp ou e-mail;
- descrição minimamente útil, com pelo menos 60 caracteres.

Isto evita alojamentos pobres em informação e melhora a confiança do cliente.

## Alterações técnicas

- Não houve alteração na base de dados.
- Não foram criadas novas migrações.
- Foram alterados templates, formulários, views e rotas.
- A versão foi validada com `python manage.py check` em ambiente Django.
- As principais páginas do proprietário foram testadas com Django Test Client.

## Páginas principais para testar

```text
/proprietario/propriedades/
/proprietario/propriedades/<id>/preparar/
/proprietario/propriedades/<id>/quartos/
/proprietario/propriedades/<id>/quartos/novo/
/proprietario/quartos/<id>/editar/
/proprietario/propriedades/<id>/fotos/
/proprietario/propriedades/<id>/fotos/nova/
```

## Recomendação para a próxima fase

A próxima fase recomendada é a v1.7, focada em confiança pública e conversão:

- selo de alojamento verificado;
- página pública mais persuasiva;
- melhoria das avaliações;
- destaque de regras, segurança, higiene e localização;
- melhor integração com WhatsApp;
- página pública optimizada para clientes que chegam por anúncio ou redes sociais.
