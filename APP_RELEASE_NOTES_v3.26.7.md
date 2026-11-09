# Enform Verde v3.26.7-PRECAMPO-EXPERIMENTAL

## Piloto de triagem SAR agrícola

- A classe de variação sazonal da série Sentinel-1 passa a aparecer como “Área cultivada — candidato SAR experimental; cultura N/D”.
- A indicação é heurística e não calibrada. Não identifica soja ou outra cultura, não confirma vegetação nativa e não substitui validação independente.
- A estimativa candidata não entra no cálculo de carbono nativo ou na previsão de produtividade.
- CBERS-4A permanece como fundo óptico preferencial e Sentinel-2 como contingência; o teste live existente em AOIs genéricas não comprova ainda a renderização no KML privado da Fazenda Maria Eduarda.

## Validação

Testes sintéticos de contrato verificam somente os rótulos e a separação entre candidato experimental e classificação de cultura. Não representam acurácia orbital nem homologação científica. A liberação depende de CI no SHA novo, teste da série SAR e prévia óptica na AOI privada e avaliação dos modelos por cultura.
