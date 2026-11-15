# Enform Verde v3.26.42-PRECAMPO-EXPERIMENTAL

## Correções desta revisão

- Separa o mapa sazonal LEM+ do último ano agrícola completo do monitoramento semântico atual. O mapa anual continua como referência experimental e não suprime a contingência atual.
- Não combina áreas anuais com candidatos Sentinel-1 dos últimos 150 dias no mesmo particionamento de cobertura.
- Exibe densidades de carbono sobre a área efetivamente quantificada, com hectares e percentual de cobertura por compartimento. Não extrapola para estratos sem suporte; o estoque total permanece incompleto/N/D quando faltar cobertura ou compartimento.
- Reduz leitura redundante por cena Sentinel-1: uma leitura COG padrão e uma leitura binária recortada para a AOI, com limites menores de tempo/retry.
- Reprova imagem óptica preta mesmo quando a interface possui objeto de imagem; o teste live avalia os pixels capturados do canvas Windows.
- Quando não há imagem óptica aprovada, mantém mapa de contingência com o perímetro; sobrepõe a camada oficial IBGE de fitofisionomia se ela já estiver carregada, identificando-a como potencial e cartográfica.

## Estado de validação

Esta alteração é uma candidata. Build Windows, suíte de regressão e teste live do canvas precisam passar sobre o commit exato para publicar o pacote como executável validado. A execução do KML privado original da Fazenda Maria Eduarda não é reproduzida pela fixture pública Sinop. Não há homologação de campo; safras, candidatos e compartimentos experimentais continuam rotulados com período, fonte e incerteza.


## V88.74 handoff-gate adjustment

The Windows and SAR integration smokes now distinguish an annual experimental map from a current semantic classification. The next complete validation run is on the synchronized code and Word-specification head; no functional pass is inferred from earlier pending or canceled workflows.
