# REVISÃO V86 — 05/11/2026 — RESULTADOS MODELADOS PARA AFERIÇÃO POSTERIOR EM CAMPO E VERIFICAÇÃO DA VERSÃO

**Produto:** Enform Verde 3.26.0-SOLO-SAFRA; PR #50, branch `feature/agricultural-identification-native-carbon`. Este texto integra a especificação técnica completa, preservando o histórico V85 e anterior.

## 1. Decisão científica e operacional

É autorizada a **geração de resultados numéricos modelados**, inclusive experimentais, para posterior aferição em campo. Cada resultado deve indicar origem, domínio de aplicabilidade, fitofisionomia, compartimento, fórmula, dados efetivamente utilizados, incerteza ou limitação e estado de validação. A ausência de medição independente **não impede a saída experimental tecnicamente justificada**; também **não autoriza** tratar cenário como evidência de campo, certificado, estimativa homologada ou IC95% da propriedade.

As rotinas de carbono, SAR, agricultura, fertilidade e carbono do solo permanecem funcionalmente independentes. Valores N/D não viram zero e não são substituídos por números sintéticos. Mapa histórico MapBiomas não é prova de mensuração SAR presente; a legenda fitofisionômica do IBGE não é prova autônoma de vegetação nativa atual.

## 2. Implementação V86

- `modeled_field_validation.py` constrói `build_pre_field_manifest(native,analysis_id,land,source_sha)` usando **apenas valores calculados pelo motor para aquela AOI**, separados por fitofisionomia e compartimento, e previsão agrícola quando o modelo existente for elegível. Cada item recebe ID de previsão, área de aplicação, densidade/estoque ou produtividade/produção, fonte e método, classificação experimental, intervalos existentes e `trace_sha256`. Se não houver número ou modelo compatível, produz N/D acompanhado de motivo, sem fabular dados.
- O estoque total conhecido `native.known_total_tc` permanece separado de cenários experimentais e não é preenchido com componentes ausentes. O relatório publica claramente `scientifically_homologated=false`, `target_aoi_ci95_validated=false`, `field_validation_pending=true`.
- Para faixa de fonte `[L,U]` compatível em tC/ha, calcular `[L×A,U×A]` como **faixa condicional de sensibilidade** sobre hectares efetivamente modelados, e não IC95% da AOI. AGB por fonte Mg/ha pode ser convertida a tC/ha apenas pela mesma fração carbono 0,47 usada no motor, mantendo a origem da faixa. Para limites marginais oficiais de SOC 0–100 cm, mostrar o envelope somado com a declaração de que **não é intervalo conjunto calibrado**. Sem faixa fundamentada: `INCERTEZA_PREDITIVA_AOI_NAO_QUANTIFICADA`, não usar DP entre pixels como substituto.
- `write_pre_field_evidence(out_dir,manifest)` gera `previsoes_experimentais_pre_campo.json` e `planilha_entrada_medicoes_campo.csv`. A planilha traz valores modelados e **colunas de valores observados obrigatoriamente vazias**. Preenchimento posterior demanda medição real, data, coordenadas, parcela/talhão, grupo espacial independente, método e arquivo de origem.
- `desktop_app.py` foi conectado para exibir resumo da modelagem no Painel de Carbono e escrever ambos os artefatos após analisar uma AOI. A exportação Excel contém aba `Modelo Para Campo` com valores modelados e coluna observada vazia, além das abas anteriores de carbono, pedologia, fertilidade e limites oficiais SOC.
- `desktop_app.module_check` verifica a presença da biblioteca de projeções no EXE e exige SHA de origem no pacote congelado. `.github/workflows/build-windows.yml` gera `enform_build_source.py` com `SOURCE_SHA` do checkout e inclui os imports `modeled_field_validation` e `enform_build_source` no PyInstaller.
- `tests/test_modeled_field_validation.py` e workflow `.github/workflows/model-prediction-contract.yml` verificam projeções numéricas, limites, descarte de valores sem fundamento, planilha de observações vazia, elegibilidade de safra, sintaxe e regressões geoespaciais de solos. **O primeiro conjunto de testes rápidos do módulo experimental passou**; as suítes ampliadas e o build Windows ainda exigem resultado no SHA final.

## 3. Protocolo de validação de campo planejada (sem observações fictícias)

- Estratificar amostras por bioma, fitofisionomia e modelo; parcelas e talhões independentes do treinamento/seleção dos algoritmos. Objetivo de planejamento: 95% de confiança e erro relativo de até 5% **quando demonstrável**. Calcular tamanho amostral após piloto com CV efetivamente observado e correção por população finita. Não declarar amostragem concluída.
- Inventariar em parcelas georreferenciadas biomassa viva (DAP, altura, espécie, alometria), biomassa subterrânea quando apropriado, necromassa em pé e caída por observação direta, serrapilheira gravimétrica, solos 0–100 cm em horizontes compatíveis com densidade e teor de C; safra por talhão/cultura e colheita independente.
- Confrontar previsões **congeladas previamente** com valores observados, em grupos espaciais independentes: viés, MAE, RMSE, R² quando aplicável, erro relativo e cobertura empírica dos intervalos. Identificar incertezas de modelo, transferência, área/classificação, compatibilidade ecológica e covariância; não chamar faixas condicionais de IC95% calibrado sem demonstração.
- A homologação científica independente (`validation/release_evidence.json` e gate modular) permanece **não atendida** na ausência das observações. Uma versão técnica **experimental** pode ser liberada caso os testes e o EXE validem, com o estado científico claramente declarado; nunca forjar o manifesto da homologação.

## 4. Solos: correções adicionais posteriores à V85

- `soil_fertility_zonal.py`: cache de raster WCS agora requer manifesto de `coverage_id`, origem institucional e SHA256 idênticos aos dados reais; download novamente quando ausentes/inconsistentes. Uma camada só é contabilizada como processada quando há pixels numéricos válidos na AOI.
- `soil_soc_official_uncertainty.py`: limites marginais 90 m também requerem manifesto verificado de cobertura e SHA256 antes de reutilizar cache. Ausência/incompatibilidade => N/D de incerteza oficial preservando estoque SOC existente.
- Testes adicionais `tests/test_soil_fertility_official_uncertainty.py` verificam a recusa de cache adulterado/IDs divergentes. Não confundir metadados de WCS com verificação de licenças comerciais ou homologação de laboratório.

## 5. Critérios de liberação

1. Passar regressões unitárias e geoespaciais, testes GUI e aceitação no Windows no **mesmo SHA** efetivamente compilado; anotar SHA256 EXE e ZIP.
2. Conferir disponibilidade real dos rasters Embrapa/PronaSolos, limites marginais, fontes SAR e licenças, deixando N/D nos produtos inacessíveis.
3. Gerar de uma AOI real um manifesto com previsões quando existirem modelos aplicáveis e uma planilha de campo sem dados medidos.
4. Distinguir **release técnico experimental** de **homologação científica independente**. O status `action_required` de execuções GitHub acionadas por bot e a fila de runners não constituem aprovação; não divulgar EXE antes da prova.
5. Manter o prompt canônico, o prompt histórico, especificação de solos e a especificação Word sincronizados a cada alteração material.

**Estado deste checkpoint:** software com mecanismo pré-campo integrado e testes rápidos de modelagem aprovados em commits anteriores; CI geral, datasets oficiais, build final e validação de campo ainda não demonstrados.
