# Enform Verde v3.26.79-PRECAMPO-EXPERIMENTAL

- Corrige ciclo de referência na auditoria do modelo FH×inventário que podia impedir serialização do resultado, relatório e painel executivo.
- Acrescenta regressão integrada FH L2A → pixels zonais → AGB com estrutura horizontal elegível → carbono por compartimento → quadro executivo, resumo e relatório.
- O gate live de Sinop agora exige que pixels FH reais lidos no processamento de carbono cheguem ao payload do dashboard com produto, fonte, contagem de pixels e rota de AGB preservados.
- Mantém as métricas agregadas de inventários como balizas; só calcula AGB quando existe modelo aplicável. Resultados continuam experimentais e não calibrados para Sinop sem validação independente de campo.

**Estado:** candidata pré-campo. Não declarar executável distribuível antes de build Windows, regressão, teste de imagem óptica e autoteste em pasta limpa no mesmo SHA.
