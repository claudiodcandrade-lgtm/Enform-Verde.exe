# Enform Verde 3.26.19-PRECAMPO-EXPERIMENTAL

## Escopo deste build

Esta revisão atua nas falhas de leitura reportadas na Fazenda Maria Eduarda: retentativas de transporte HTTP para COGs CBERS-4A/Sentinel-2, Sentinel-1 recente, LEM+ e MapBiomas; diagnóstico com etapa, estratégia e detalhe de erro; e separação explícita entre falha técnica na leitura SAR e ausência de cenas/pixels válidos.

O fallback MapBiomas + PAM permanece uma referência histórica e só é elegível depois que as rotas SAR configuradas forem executadas e esgotadas. Ele não comprova cobertura, cultura ou safra atuais.

## Estado de validação

Cinco testes unitários do fallback MapBiomas + PAM passaram neste ambiente; compilação sintática e verificação `git diff --check` passaram. A suíte que importa a GUI não foi executada localmente porque o ambiente não tem `requests`. A leitura na geometria integral da Fazenda Maria Eduarda não foi validada. A compilação e as regressões do Windows CI ainda são necessárias; os pixels reais e os painéis da AOI integral permanecem como critério de aceite antes de chamar esta versão de funcional para a fazenda.

Os resultados experimentais não devem ser tratados como homologação científica ou validação de campo. Erro técnico de leitura não deve ser apresentado como ausência de cena, ausência de pixel ou zero hectares.
