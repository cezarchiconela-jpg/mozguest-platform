# +258 Guest v2.4.2 — Localização Simplificada e Rebranding Final

## Objectivo

Esta versão fecha duas correcções finais identificadas no teste local:

1. Remover os últimos pontos visíveis onde ainda aparecia a marca antiga no cabeçalho, rodapé, página offline e ícones da PWA.
2. Simplificar profundamente o preenchimento da localização da propriedade pelo proprietário.

## Melhorias aplicadas

### 1. Marca final +258 Guest

Foram corrigidos os pontos visíveis que ainda apresentavam a antiga identidade no topo, rodapé e página offline.

Também foram regenerados os ícones principais da PWA para evitar o uso visual de iniciais antigas.

### 2. Localização simplificada para proprietários

Na página de criação/edição de propriedade, a localização agora pode ser definida por quatro formas:

- botão **Usar minha localização actual**;
- campo de pesquisa no mapa por cidade, bairro, rua ou ponto de referência;
- botão para abrir pesquisa no Google Maps;
- campo para colar link/coordenadas do Google Maps;
- clique directo no mapa para marcar o ponto exacto.

O proprietário já não precisa saber escrever manualmente latitude e longitude. Os campos continuam disponíveis para transparência, mas são preenchidos automaticamente pelo mapa, pelo navegador ou pelo link/coordenadas coladas.

### 3. Validação técnica

Foi feita validação de sintaxe Python com:

```bash
python3 -m compileall -q .
```

Também foi feita pesquisa textual para confirmar ausência de referências antigas como:

- MozGuest
- mozguest
- MOZGUEST
- MozAdmin
- moz-admin
- Amukela
- KayaMoz

Resultado: nenhuma ocorrência textual antiga relevante encontrada.

## Observação

O mapa visual usa Leaflet/OpenStreetMap para permitir pesquisa e clique no mapa sem depender de uma chave API paga do Google. O botão de Google Maps abre a pesquisa numa nova aba e o campo de colagem aceita coordenadas ou links do Google Maps que contenham latitude e longitude.
