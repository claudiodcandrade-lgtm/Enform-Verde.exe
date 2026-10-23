# Plano e evidências de validação externa SAR — 23/10/2026

## Fontes identificadas (não constituem validação concluída do Enform Verde)
- **Goiatuba/GO (campo, safra 2025/26)**: https://doi.org/10.5281/zenodo.17612590 ; artigo https://doi.org/10.3390/data10120204 . 117 campos pré-selecionados e 463 parcelas adicionais, levantamento in situ de novembro de 2025. Verificar quais classes estão presentes, datas de observação, licença, geometrias e se a mesma unidade/área entrou no treinamento. Não presumir cobertura de oito culturas.
- **MapBiomas — pontos de validação Coleção 9**: https://brasil.mapbiomas.org/downloads/pontos-de-validacao/ . 85.152 pontos interpretados de Landsat, classe anual, concordância e borda. Úteis para auditoria de cobertura nativa vs plantada e estratos, desde que não haja reutilização como treino. **Não** são automaticamente verdade de campo para eucalipto/pinus nem todas culturas.
- **Apêndice técnico agricultura/silvicultura Coleção 10**: https://brasil.mapbiomas.org/wp-content/uploads/sites/4/2025/08/Agriculture-and-Forest-Plantation-Appendix-ATBD-Collection-10-v2.pdf . LAPIG independente agrupou silvicultura, lavoura temporária e perene; não mede identificação individual das oito culturas.
- **Inventário mineiro publicado de florestas plantadas (matriz externa eucalipto/pinus)**: https://sindifer.com.br/links/SINDIFER%20-Forest%20Iventory%20MG_COP28.pdf . Matriz publicada com 12.025 unidades e gêneros separados. É resultado de outro modelo, portanto **não pode ser copiada como validação do Enform Verde**; solicitar pontos, polígonos, datas, separação treino/teste e permissão de uso para validar o SAR independente.
- **Limites agrícolas Trazo**: https://source.coop/wri-data-lab/trazofields . Limites inferidos por visão computacional, com atributos MapBiomas; **não são labels independentes de cultura**.

## Execução obrigatória
1. Obter dados primários georreferenciados da fonte, documentação e licença. Registrar versão, DOI/URL e SHA256.
2. Criar lista das unidades de treino/calibração e estabelecer exclusão espacial/temporal inequívoca, com prova de ausência de vazamento e avaliação de domínio por bioma, estado, estação e data.
3. Adquirir cenas SAR reais com cobertura temporal compatível, processamento/polarização/metadados equivalentes aos exigidos pelo modelo. Registrar ID e horário original/ Brasília.
4. Carregar pesos e versão do modelo efetivamente implantado, produzir predições **antes de conhecer os rótulos de teste**; salvar CSV imutável com os campos exigidos por `independent_sar_validation.py`.
5. Executar o avaliador por classe; mínimo de 50 *predições aceitas* independentes/classe, confiança calibrada >= 0,90, limite inferior Wilson 95% de precisão >=0,90. Produzir matriz de confusão, erro de omissão/comissão, calibração e estratificação espacial. Corrigir desbalanceamento de amostra com probabilidades/ponderações de desenho quando disponíveis.
6. Auditar identidade dos campos e proveniência; só após auditoria externa registrar classe habilitada. Não confundir acurácia geral do MapBiomas com acurácia do Enform.
7. Teste eliminatório nativo vs silvicultura vs cobertura arbórea incerta; rejeitar qualquer contagem indevida de carbono nativo.

## Status documentado
- Código de avaliação: implementado e versionado; regressões sintéticas criadas.
- Fontes reais: identificadas, **não** pareadas com previsão SAR.
- Modelos SAR treinados/pesos para 11 alvos: não demonstrados no repositório.
- **Resultados independentes e aprovação por classe: PENDENTES.**
