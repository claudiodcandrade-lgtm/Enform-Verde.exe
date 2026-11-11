# Enform Verde 3.26.18-PRECAMPO-EXPERIMENTAL

## Integração do classificador sazonal SAR ao diagnóstico do aplicativo

- O classificador Sentinel-1 LEM+ executado pelo aplicativo registra se foi chamado para a AOI integral, se as classes foram incorporadas, além de safra, cenas/pixels, área/hash da geometria e diagnóstico de aquisição.
- O relatório de uso do solo e o painel executivo mostram o estado do LEM+ separadamente da triagem SAR recente. Falhas de aquisição deixam motivo e erros por cena visíveis.
- Quando um classificador anterior já fornece classes, o LEM+ fica explicitamente como `NOT_EXECUTED` e com escopo não executado. Esse estado não conta como esgotamento SAR.
- A contingência MapBiomas + PAM fica bloqueada se qualquer rota estiver ausente, não executada ou sem um estado terminal conhecido.
- O artefato de CI em caixa de teste permanece separado do aplicativo; não é importado como resultado da fazenda. O runtime realiza sua própria execução na AOI carregada.

## Evidência e limites

- Compilação sintática passou. A suíte completa executou 1.071 testes: todos passaram e 1 foi ignorado. Inclui a regressão que prova `NOT_EXECUTED` quando o classificador prévio já fornece classes SAR.
- `python tools/check_test_collection.py` aprovou 156 módulos; o contrato documental passou após sincronizar a versão Word. `ui_visual_standard.py` não pôde iniciar por ausência de `DISPLAY`.
- Não houve execução do KML integral da Fazenda Maria Eduarda no Windows nesta revisão. A integração do diagnóstico não comprova acesso a provedores, leitura COG, classificação da fazenda nem geração de carbono. Não declarar versão operacional antes da prova de pixels reais na AOI integral e do build Windows.
