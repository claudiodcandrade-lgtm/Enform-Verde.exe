# Enform Verde v3.26.79-PRECAMPO-EXPERIMENTAL

- Corrige ciclo de referência na auditoria do modelo FH×inventário que podia impedir serialização do resultado, relatório e painel executivo.
- Acrescenta regressão integrada FH L2A → pixels zonais → AGB com estrutura horizontal elegível → carbono por compartimento → quadro executivo, resumo e relatório.
- O gate live de Sinop agora exige que pixels FH reais lidos no processamento de carbono cheguem ao payload do dashboard com produto, fonte, contagem de pixels e rota de AGB preservados.
- Mantém as métricas agregadas de inventários como balizas; só calcula AGB quando existe modelo aplicável. Resultados continuam experimentais e não calibrados para Sinop sem validação independente de campo.

**Estado:** candidata pré-campo. Não declarar executável distribuível antes de build Windows, regressão, teste de imagem óptica e autoteste em pasta limpa no mesmo SHA.

## Registro operacional e critério de distribuição

A prova FH real de Sinop passou, e o processamento SAR real de Sinop/Tapajós chegou ao dashboard com sucesso. Em uma tentativa Windows anterior, a regressão FH/AGB→quadro e relatório passou; o job parou depois porque o mock do contrato de interface não aceitava o argumento `metrics` e impedia o desenho do polígono. O mock foi corrigido. A distribuição desta versão exige que o build atual passe no SHA final, incluindo o contrato gráfico, os testes ópticos aplicáveis, a compilação do executável e seu autoteste em pasta limpa. O gate científico independente segue pendente de validação de campo; resultados permanecem experimentais.
