# V88.155 — correção do diagnóstico FH com modelo AGB ausente

Data: 18/11/2026  
Aplicativo de referência: 3.26.71-PRECAMPO-EXPERIMENTAL  
Base revisada: SHA `f945d9fd915b9f938e0a54a917eb8e33f5b9448b`

## Resultado que o build anterior realmente demonstrou

No aceite Windows do AOI Tapajós (1.290,688 ha), o leitor zonal encontrou 1.512 pixels válidos de FH e não registrou erros de leitura. Portanto, o rótulo `ERRO_TECNICO_ROTA_PRIORITARIA` era incorreto para esse caso. O ESA CCI foi corretamente bloqueado porque havia FH, mas a aplicação não dispunha de um modelo AGB compatível com a extensão/domínio do AOI. O aceite do EXE falhou e nenhum artefato foi publicado.

## Correção de código

A distinção foi implementada: FH lido sem modelo recebe `FH_DISPONIVEL_AGB_MODELO_NAO_DISPONIVEL`; CCI continua bloqueado; falhas reais de rota sem pixels válidos continuam sinalizadas separadamente. A saída mantém AGB como N/D e não converte o diagnóstico em estimativa.

## Pendências que bloqueiam uma versão operacional

A calibração FH×campo e sua integração ao fluxo de AGB não estão implementadas. O modelo Tapajós existente está restrito às zonas dos sítios ORNL e não cobre o AOI extenso do aceite. A base local inclui dados IFN e outras fontes, mas ainda não foi demonstrado pareamento FH–inventário multiprovedor, validação espacial independente nem incerteza propagada em domínio microrregional. Não substituir essa lacuna por CCI, médias de inventário ou uma regra de aceite permissiva.

A rotina corrigida precisa ser incorporada ao executável, e a versão candidata só poderá ser liberada após demonstrar, no mesmo SHA: consulta da base expandida, pares FH–inventário elegíveis, modelo único de AGB com validação e incerteza, integração até dashboard/relatório e autoteste Windows aprovado. A homologação científica independente permanece separada.
