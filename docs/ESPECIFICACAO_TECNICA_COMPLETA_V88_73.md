# Especificação técnica Enform Verde V88.73

Data: 15/11/2026. Aplicação: candidata 3.26.42-PRECAMPO-EXPERIMENTAL.

## Correção de fluxo comprovada pelos relatórios

O classificador LEM+ processa o último ano agrícola completo. Seu mapa é rotulado anual e não pode ser tratado como monitoramento de data atual. A trilha temporal fica separada: classes anuais, máscara semântica atual quando disponível, candidatos orbitais recentes, e N/D/erro técnico. A ausência de classificador atual deve acionar a contingência mesmo que o mapa anual exista. Resultados desses produtos não são mesclados em um mesmo particionamento.

O painel de carbono mostra tC/ha e tCO2e/ha por compartimento com denominador explícito: área quantificada. Exibe cobertura em ha e percentual da área nativa, sem extrapolar. O total só é apresentado como completo quando as regras de cobertura e compartimentos forem satisfeitas; caso contrário informa subtotal conhecido, área sem suporte e N/D/parcial.

## Fluxo visual

CBERS-4A/WFI e Sentinel-2 permanecem fundos opcionais. O teste Windows captura pixels do canvas e verifica brilho, contraste e fração visível. Em erro, rejeição de imagem ou timeout, a UI mantém o limite da AOI e desenha a camada oficial IBGE de fitofisionomia já carregada, identificada como potencial. Se a camada IBGE não estiver disponível, mostra o mapa local da AOI e explica a indisponibilidade. Nenhuma camada cartográfica entra no cálculo de cobertura ou carbono.

## Leitura SAR e desempenho

Para cada cena COG, uma leitura normal e uma alternativa binária recortada à AOI substituem a rotação repetida de até cinco estratégias equivalentes. Os limites passam a 12 s/1 retry no GDAL e 30 s na rota HTTP de crop. O estado do fluxo registra tentativa, leitura válida, erro de transporte, autorização e proveniência. As reduções limitam esperas repetidas; não certificam o tempo final sem medição por AOI.

## Evidência e gates

Os testes precisam passar no commit de código e no commit documental final: suíte integral, regressões de escopo anual/atual e densidade parcial, smoke de pixels de canvas Windows, SAR live e build Windows. O KML integral da Fazenda Maria Eduarda requer teste em ambiente Windows local; a fixture pública no centroide de Sinop não o substitui. Sem validação de campo, todos os modelos pertinentes permanecem pré-campo/experimentais, com incerteza explícita ou “incerteza não mensurável”.


## V88.74 — ajuste de gate

O teste de integração deve registrar annual_map_applied, safra, escopo temporal, current_semantic_result_applied e status/gatilho da rota de contingência. Mapa anual pode ser transferido aos módulos de carbono e dashboard apenas como produto experimental daquele período; o estado semântico atual permanece em campo separado.


## V88.75 — contratos de teste

A trilha de auditoria do LEM+ registra o AOI integral e a safra completa, com flags separadas de aplicação anual e classificação atual. A suíte de regressão protege explicitamente esse contrato, a rejeição de pixels pretos no canvas e duas tentativas bounded por cena Sentinel-1.
