# Checkpoint V88.45 — contingência HTTP 429 Sentinel-1

Data: 13/11/2026  
Versão candidata: `3.26.31-PRECAMPO-EXPERIMENTAL`  
Base remota verificada: V88.43, SHA `431833f1cec7693d8892d5a615cdaac02eb8a879`  
Branch: `patches-3.26.6`, PR #51 em rascunho; não mesclar.

## Diagnóstico confirmado

O Windows CI da V88.43 encontrou HTTP 429 ao assinar ativos VV/VH via MPC em Petrolina; o catálogo INPE RTC não encontrou cenas recentes naquele recorte. Essa observação é uma limitação de acesso por AOI/provedor/data, não prova de indisponibilidade nacional. O ESA MAAP é rota para produtos ESA Biomass e não autentica Sentinel-1.

## Correção V88.45

- Para a coleção MPC `sentinel-1-grd`, o leitor solicita o token SAS de coleção e usa-o em memória nos dois COGs. O signer por ativo só é tentado se o token de coleção não estiver disponível.
- Os erros 429 continuam limitados e interrompem a busca por cenas adicionais no mesmo provedor/AOI.
- O relatório registra a rota de acesso, mantém URLs/tokens fora da saída e exige par VV/VH da mesma cena.
- INPE RTC e CDSE permanecem alternativas já existentes. ASF OPERA RTC-S1 exige Earthdata e não está integrado à leitura de pixels; AWS GRD COG é público, mas requer processamento RTC e também não está integrado.

## Evidência disponível

A suíte local completa passou após as alterações V88.45: **1.150 testes aprovados, 1 ignorado** por ausência de display gráfico. A coleta identificou 169 módulos de teste. `git diff --check` passou. Isso não substitui CI Windows, consulta live nem pixels SAR no AOI da propriedade.

## Evidência disponível antes do novo SHA

No SHA V88.43 passaram os contratos do dashboard, pré-campo e máscara SAR Sinop; a leitura ESA BIOMASS FH em Sinop passou. O gate nacional falhou por HTTP 429 no MPC/zero cenas INPE em Petrolina e a homologação científica reprovou por falta de validação independente. No checkout local, V88.44 passou 1.146 testes (1 ignorado por ausência de display) e coletou 168 módulos; esse resultado antecede a nova rota V88.45.

## Gates que continuam abertos

Confirmar no Windows que o token de coleção abre pixels VV/VH recentes no mesmo produto/aquisição; examinar o diagnóstico distribuído; obter build/dashboard no SHA final; executar o KML integral de Maria Eduarda até o dashboard. A validação observacional independente por compartimento/bioma continua pendente. Até esses gates passarem, o pacote é pré-campo experimental e não homologado.
