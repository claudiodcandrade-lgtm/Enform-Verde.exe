# Enform Verde v3.26.42-PRECAMPO-EXPERIMENTAL

## Correções desta revisão

- Separa o mapa sazonal LEM+ do último ano agrícola completo do monitoramento semântico atual. O mapa anual continua como referência experimental e não suprime a contingência atual.
- Não combina áreas anuais com candidatos Sentinel-1 dos últimos 150 dias no mesmo particionamento de cobertura.
- Exibe densidades de carbono sobre a área efetivamente quantificada, com hectares e percentual de cobertura por compartimento. Não extrapola para estratos sem suporte; o estoque total permanece incompleto/N/D quando faltar cobertura ou compartimento.
- Reduz leitura redundante por cena Sentinel-1: uma leitura COG padrão e uma leitura binária recortada para a AOI, com limites menores de tempo/retry.
- Reprova imagem óptica preta mesmo quando a interface possui objeto de imagem; o teste live avalia os pixels capturados do canvas Windows.
- Quando não há imagem óptica aprovada, mantém mapa de contingência com o perímetro; sobrepõe a camada oficial IBGE de fitofisionomia se ela já estiver carregada, identificando-a como potencial e cartográfica.

## Estado de validação

Build operacional aprovado no SHA `8551bcaf84586af71ae574abda8a6e37e467f4d3`: 1.173 testes, build Windows e handoff SAR live para amostra pública Sinop/Tapajós passaram. O artefato Windows foi testado em pasta limpa com smoke de UI, módulos, paridade Python/EXE, rede e aceitação Tapajós. 11/11 locais amostrais carregaram pixels CBERS. O teste de canvas passou com fallback AOI local visível. A versão continua pré-campo/experimental: KML privado Maria Eduarda não testado, classificação atual semântica N/D, resultados SAR de uso da terra são anuais e experimentais, carbono parcial e sem IC total; não há homologação de campo.


## V88.74 handoff-gate adjustment

The Windows and SAR integration smokes now distinguish an annual experimental map from a current semantic classification. The next complete validation run is on the synchronized code and Word-specification head; no functional pass is inferred from earlier pending or canceled workflows.


## Checkpoint V88.76 — fallback visual IBGE não bloqueante

CBERS/Sentinel-2 são opcionais e não bloqueiam a análise. A UI mantém um fundo de contingência visível e, após falhas ópticas, carrega a camada IBGE de fitofisionomia em worker assíncrono. A camada é rotulada como formação potencial e não entra em mapas de cobertura atual, carbono ou cultura. Se o dado IBGE também falhar, a AOI permanece visível com aviso. O smoke nacional registra locais sem óptica sem reprovar o build; o smoke de canvas mede pixels reais e aceita apenas imagem visível ou cartografia de contingência, nunca uma tela preta.


## V88.76 fundo visual de contingência

A imagem óptica é opcional. A UI desenha a AOI imediatamente, tenta CBERS/Sentinel-2 e demais fundos em worker, e ao esgotá-los tenta carregar a camada potencial IBGE. O IBGE fica rotulado como referência; não confirma cobertura atual. Se o IBGE falhar, o mapa local da AOI e o aviso permanecem. Indisponibilidade óptica não bloqueia o build; o canvas smoke exige pixels visíveis do mapa ou fallback.


## Evidência do artefato Windows

- Run: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/43731184717
- ZIP do build: `Enform-Verde-Windows-v3.26.42-PRECAMPO-EXPERIMENTAL`
- SHA-256 do executável: `796561975818f2e6a6db8d7858875f6d080b926d523885583bf9907c5c7fff35`
- SHA-256 do ZIP: `31653bc1c2edb1b066b5ccb3e1056858c8114bbcca91b82872bdd6aa70849312`
- Código exato: `8551bcaf84586af71ae574abda8a6e37e467f4d3`
