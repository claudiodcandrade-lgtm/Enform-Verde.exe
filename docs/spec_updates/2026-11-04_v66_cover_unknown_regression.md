# REVISÃO V66 — COBERTURA NATIVA DESCONHECIDA E REGRESSÃO DE RELATÓRIO (04/11/2026)

## Alteração incorporada
- Commit fe5214fea99e7a034d4e0c96e7680e0efea1c914: no `executive_carbon_report.py`, quando `unknown_cover_area_ha > 0`, o painel informa explicitamente `Cobertura nativa: N/D — cobertura não integralmente verificada`. Mantém a vegetação nativa já cartografada (área mínima conhecida) e a área sem classe, mas não transforma desconhecido em zero confirmado.
- Correção de regressão `tests/test_carbon_presentation_regression.py`, verificada no último workflow falho 41905276990; falha anterior não era no cálculo de biomassa, mas na frase obrigatória de incerteza do percentual de cobertura.
- A lógica de classificação deve respeitar as interseções disjuntas entre MapBiomas anual, fitofisionomia IBGE e AOI; no recorte Sinop 1.500,33 ha, 72,92 ha nativos e 1.241,75 ha de soja anual MapBiomas não tornam a AOI inteira floresta ou lavoura.
- Serrapilheira experimental: referências diretas de estoque seco por fitofisionomia com filtros espaciais; IFN/SFB de espessura em cm não é estoque seco e exige calibração independente massa/espessura. Cenários sem IC de transferência permanecem fora do estoque conhecido.
- CI deve incluir regressão integral, compilação EXE Windows, autoteste em pasta limpa, SHA e ZIP no mesmo commit. Homologação científica independente não é dispensada; dados reais por compartimento, identificação SAR e calibração temporal/espacial ainda são exigidos.

## Estado e publicação
- Prompt de continuidade v66 e especificação técnica completa v66 substituem os documentos v65 no pacote de download; preservam histórico anterior integralmente.
- Nenhum ZIP Windows de commit anterior deverá ser rotulado v66. Verificar o resultado do build do SHA documental final, o artefato e seu checksum antes de divulgar.
