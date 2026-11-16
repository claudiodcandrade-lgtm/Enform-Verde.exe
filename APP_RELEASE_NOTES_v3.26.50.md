# Enform Verde v3.26.50 — pré-campo experimental

## V88.92 — fluxo condicional de vigor SAR para previsão

- Corrigida a amostragem do vigor em máscaras SAR anuais experimentais: agora separa blocos-alvo e referências internas não sobrepostas, em vez de usar o polígono dissolvido que se sobrepunha aos alvos e podia deixar o cálculo sem referências.
- Vigor relativo SAR de cenas atuais VV/VH, quando obtido com data, idade e pixels válidos, chega às probabilidades do modelo PAM + clima/balanço hídrico para soja e milho. A auditoria registra máscara da safra anterior, escopo condicional e incerteza de transferência não quantificada; o quadro executivo distingue vigor incorporado de previsão sem vigor.
- Uma consulta de catálogo Sentinel-1 e uma obtenção de token são reutilizadas por cultura/AOI. O alvo continua submetido à leitura e aos gates de pixel individual.
- Com referências/pixels insuficientes, vigor é N/D e a previsão pode seguir sem vigor quando há máscara de cultura elegível. Não se confirma cultura atual nem permanência da lavoura. O painel de produtividade disponível cobre soja e milho; outras culturas prioritárias não recebem projeção específica sem modelo correspondente.

## Verificação

38 testes focados de SAR-vigor-safra, painel PAM/clima e balanço hídrico passaram localmente; `compileall` e `git diff --check` passaram. A validação não inclui cena Sentinel-1 live, build/EXE Windows, CI remota, KML privado integral da Fazenda Maria Eduarda nem dados de campo. Estado: pré-campo experimental, não homologado.
