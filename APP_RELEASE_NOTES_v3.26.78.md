# Enform Verde v3.26.78-PRECAMPO-EXPERIMENTAL

- Inclui referências agregadas de área basal, densidade e outras métricas horizontais de fontes confiáveis no pacote de evidência da rota FH × inventário.
- Mantém fonte, fitofisionomia, região, estrato, unidade, n e incerteza publicada separados; estatísticas agregadas funcionam como baliza, nunca como parcela sintética.
- Preserva o domínio espacial e estatístico do modelo H100 × G de Tapajós; não extrapola o coeficiente para outras regiões sem modelo aplicável.
- Mantém a ordem AGB: FH + estrutura horizontal/modelo aplicável; ESA CCI + inventários; média de inventários compatíveis como contingência apenas após rotas completas sem erro técnico e sem AGB quantitativa.
- A lista Top 10 de frequência requer inventários fitossociológicos representativos com frequência/ocorrência taxonômica observada ou publicada; agregados estruturais não são usados para inventar frequência.

**Estado:** candidata pré-campo. Este arquivo descreve o código-fonte; não comprova EXE Windows, fluxo ponta a ponta, leitura óptica, vigor ou homologação científica.

## Verificação da candidata

- Regressão local completa: 1.324 testes aprovados, 1 ignorado.
- Coleção: 192 módulos inspecionados sem falha.
- IFN/SFB materializado localmente: 841.387 observações, 8.951 UAs; 8.951 correspondências únicas à legenda_1 do IBGE.
- Pendentes no mesmo SHA: build Windows, `--module-check`, `--visual-check`, `--network-check`, abertura da imagem óptica real e autoteste do EXE em diretório limpo.
- Não homologada cientificamente sem validação independente de campo. Não chamar a candidata de EXE distribuível antes do workflow Windows passar.
