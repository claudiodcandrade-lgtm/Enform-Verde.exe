# Enform Verde 3.26.3-PRECAMPO-EXPERIMENTAL

Versão experimental para validação operacional. Não representa homologação científica independente.

## Correções desta versão

- Corrige a reconciliação de área de cobertura nativa: classes explicitamente não nativas (por exemplo, pastagem) são excluídas da área nativa, lacunas geométricas permanecem desconhecidas e MapBiomas não confirma vegetação nativa atual.
- Mantém aquisição Sentinel-1 com tentativas por cena, renovação de token e contingência entre Planetary Computer e INPE RTC; a análise exige leitura e decodificação de pixels VV/VH.
- Mantém PAM como referência regional na matriz de previsão de safra. Produtividade da propriedade exige cultura atual, vigor datado e fatores climáticos aplicáveis.

## Condição de distribuição

O pacote Windows só deve ser considerado pronto após testes completos, leitura real dos pixels na AOI, execução limpa do EXE e verificação de que o artefato foi produzido a partir do SHA final. A homologação científica independente é uma porta distinta e pode permanecer reprovada.