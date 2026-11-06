# V87.7 — Resolução e desempenho do preview óptico Sentinel-2 — 05/11/2026

## Resolução espacial

A composição RGB usa as bandas visíveis B02 azul, B03 verde e B04 vermelho, cada uma com resolução espacial nominal de 10 m. A resolução real de detalhe também depende de qualidade atmosférica/nuvens, nitidez, georreferenciamento, escala exibida e reamostragem do preview. A miniatura é uma visualização; os dados originais não são alterados.

## Arquitetura de desempenho escolhida

Para visualizar uma AOI comum, recortar por janela geográfica do COG com leitura por HTTP range e reamostrar diretamente ao tamanho do canvas (atualmente limitado ao viewport). Isso evita baixar e manter a cena Sentinel-2 completa e é preferível a subdividir toda AOI em quadrantes em toda execução. O código Earth Search abre ativos COG RGB remotamente, calcula a janela ampliada ao redor da AOI, lê apenas essa janela e pede a saída já reamostrada para o canvas.

Quadrantes arbitrários acrescentariam várias chamadas e montagens para propriedades pequenas. Se a AOI atravessar múltiplas cenas/telhas MGRS ou ultrapassar limites de memória/transferência, a arquitetura futura/adaptativa deve processar somente as telhas que interceptam o recorte visível, em blocos limitados e concorrência controlada, depois compor uma imagem do viewport. Não baixar cobertura nacional nem reprocessar pixels invisíveis. Se a rota de múltiplas telhas não estiver disponível, manter fallback óptico alternativo.

## Integridade funcional

- Preview de entorno permanece exclusivamente óptico: Google opcional com chave, Earth Search Sentinel-2 prioritário sem credencial de usuário, Planetary Computer, NASA GIBS VIIRS, Esri e IBGE offline.
- SAR/radar continua reservado aos motores analíticos; nenhum preview entra em classificação, identificação, biomassa ou carbono.
- Consultas e leitura remota ocorrem em worker; falha de um provedor avança à próxima rota.
- Não reivindicar porcentagem de ganho sem benchmark reproduzível. Medir tempo, bytes transferidos, memória de pico e completude espacial em AOIs pequenas, médias, extensas e multi-telha.

## Testes

`tests/test_nasa_gibs_keyless.py` garante prioridade Earth Search, uso de COG, janela e reamostragem limitadas ao viewport, sem chave de usuário. Acrescentar validação de AOI atravessando telhas, integridade do mosaico, fallback por nuvens/dado ausente, ausência de bloqueio da UI e comparação de footprint exibido. Build e regressões devem pertencer ao mesmo SHA do pacote distribuído.

## Fontes

- ESA Sentinel-2 Product Specification (B2/B3/B4 a 10 m): https://sentinels.copernicus.eu/documents/d/sentinel/sentinel-2-products-specification-document-15_1
- Sentinel-2 COGs públicos AWS: https://registry.opendata.aws/sentinel-2-l2a-cogs/
- Earth Search STAC: https://github.com/Element84/earth-search


## Complemento V87.8 — leitura RGB concorrente limitada

As bandas RGB dos COGs ópticos Sentinel-2 têm leituras remotas independentes. O cliente lê vermelho, verde e azul simultaneamente com no máximo três workers, usando janela COG por HTTP range e reamostragem direta para a dimensão do canvas. O limite fixo evita concorrência irrestrita; a saída e a semântica de cor continuam com a mesma ordem de bandas. O restante do app não espera a rede, pois o mapa roda em worker separado.

Teste de contrato exige limite de três workers, leitura pelo window=win e out_shape igual ao canvas. Não alegar aceleração numérica sem benchmark. A otimização afeta somente carregamento da visualização óptica e não altera SAR, resultados analíticos ou interpretação.
