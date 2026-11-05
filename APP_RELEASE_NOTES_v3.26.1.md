# Enform Verde 3.26.1-PRECAMPO-EXPERIMENTAL

**Estado:** candidato a versão técnica experimental; **NÃO É LIBERAÇÃO HOMOLOGADA**. A presença deste arquivo não demonstra que houve build, testes Windows ou download. Apenas distribuir após aprovação de testes compilados do mesmo SHA e publicação de pacote/manifesto com SHA256.

## Objetivo e escopo

Operacionalizar resultados modelados oriundos de dados reais para futura comparação com medições de campo, sem preencher evidências independentes com dados artificiais e sem perder os módulos anteriores de carbono, SAR, Embrapa/PronaSolos 0–100 cm, classificação de solos, fertilidade, agricultura, vigor, clima e safra.

## Alterações desde 3.26.0

- Motor `modeled_field_validation.py`: previsão por fitofisionomia e compartimento, com área espacial, densidade (tC/ha), estoque (tC, tCO2e), método, fonte, `trace_sha256`, intervalo condicionado e lacunas marcadas N/D. A origem e o método não podem ser “N/D”, “desconhecido”, “None” ou vazio; não há previsão válida em área nula.
- `previsoes_experimentais_pre_campo.json` e `planilha_entrada_medicoes_campo.csv` (sem observações inventadas) ficam junto aos demais relatórios espaciais da análise.
- Excel: aba `Modelo Para Campo`, com onze colunas e a coluna de medição de campo em branco, além das abas existentes. Contexto e validade das estimativas preservados.
- Biomassa subterrânea: preserva intervalos condicionais de alometria (quando fornecidos), sem apresentar IC95% da propriedade. Modelos de biomassa e inventários carregam identificadores de fonte; solo 0–100 cm transporta metadados institucionais e envelope de limites marginais, quando recuperáveis.
- Fertilidade química e estoque SOC: cache bruto WCS autenticado pelo ID do produto, fonte e checksum SHA256 antes de reutilização; pixels N/D/fora da AOI não contam como estimativa. Média espacial não equivale a análise laboratorial no imóvel; DP espacial não é IC95% da previsão.
- `enform_build_source.py` é gerado no build PyInstaller com SHA exato dos fontes compilados; testes do EXE exigem SHA, módulos e dados locais. Gate científico independente permanece fail-closed.
- CI GitHub: workflows de build e dashboard substituídos cancelam jobs obsoletos de commits anteriores; a execução do SHA atual deve ser verificada antes da liberação.
- Código e documentação atualizados: revisão V87, dois prompts, especificação de solos, checkpoint científico e especificação Word.
 
## Testes e limitações

Testes unitários de contratos experimentais e geoespaciais passaram em SHA anterior da V86. Os novos testes da V87, GUI Windows, aceitação real, disponibilização dos dados SAR, licenças oficiais, acurácia em cinco biomas e compilação final aguardam execução e evidência do **SHA final**. Os intervalos declarados são de fonte/cenário ou condicionais; não constituem cobertura calibrada da AOI. Não permitir certificação científica por este candidato experimental.


### CORREÇÃO CIENTÍFICA V87.1 — 05/11/2026 — ENVELOPE MARGINAL DE SOC NÃO É INCERTEZA PREDITIVA VALIDADA

Em `soil_pronasolos_zonal.py`, quando houver os dez rasters oficiais de limites (`lower`/`upper` por cinco horizontes), o resultado deve manter `status=ENVELOPE_MARGINAL_OFICIAL` e `sum_bounds_envelope_tc_ha=[soma(L), soma(U)]`, mas **`predictive_uncertainty_quantified=False`** tanto em `official_uncertainty` quanto no compartimento `0–100 cm`. A nova chave `marginal_envelope_available=True` identifica a existência dos limites informativos sem inferir erro de previsão calibrado da AOI. Os testes `test_marginal_bounds_envelope_not_joint_ci` passam a verificar as duas semânticas. Não retirar limites, transformar DP espacial em intervalo ou atribuir IC95% da propriedade. Esta correção é parte do candidato experimental **3.26.1-PRECAMPO-EXPERIMENTAL**, não constitui nova homologação científica. O build Windows, contratos no HEAD e artefato assinado SHA256 continuam obrigatórios para liberação.
