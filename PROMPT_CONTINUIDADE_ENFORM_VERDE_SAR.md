# PROMPT DE CONTINUIDADE — ENFORM VERDE SAR
## Atualização consolidada — 2026-10-04

Retomar o desenvolvimento no repositório `claudiodcandrade-lgtm/Enform-Verde.exe`, branch `sar-agb-height-integration-v3.24.22`, PR #48.

## Prioridade absoluta
Liberar a versão Windows `3.24.22-PROFESSIONAL` somente depois que a mesma cabeça de código passar todos os gates científicos, geoespaciais e de empacotamento Windows.

## Estado atual do PR
- PR #48 aberto.
- Cabeça atual: `81f122728929c7c77da732830a00fff5fdb5e5c1`.
- Workflow atual: run #355 / `37216005034`.
- Não mesclar antes do término bem-sucedido desse run ou de uma cabeça posterior.

## Evoluções já incorporadas

### 1. ESA BIOMASS / altura SAR
- `FP_AGB_L2B` e `FP_FH__L2B` são descobertos separadamente.
- FH/H100 nunca é tratado como AGB.
- Se existir FH/H100 e houver estrutura horizontal local cadastrada, a rota height-first pode produzir AGB antes de L/C/fallback.
- Se houver FP_AGB_L2B oficial, ele permanece produto direto prioritário e pode carregar comparação com o modelo height-first.

### 2. Modelo Tapajós H100 × estrutura horizontal
Base primária: ORNL DAAC 1552, 30 parcelas de 50 × 50 m, com DAP, altura total, densidade da madeira e georreferenciamento.

Modelos:
- PF+SLF: `AGB = 0.4092378415 × G × H100`
  - n=16 parcelas
  - 4 blocos espaciais
  - RMSE leave-spatial-block-out = 26.650 Mg/ha
  - MAE = 21.662
  - viés = -0.833
  - R² = 0.879
- SF: `AGB = 0.2945481254 × G × H100`
  - n=14 parcelas
  - 3 blocos espaciais
  - RMSE = 17.551 Mg/ha
  - MAE = 11.515
  - viés = +5.496
  - R² = 0.839

A resposta de campo é AGB alométrica Chave-2014 calculada árvore a árvore; não é biomassa destrutiva.

Suportes de aceitação:
- `acceptance/Teste_SAR_Altura_Estrutura_Tapajos_PF_Alta.kml` — PF parcelas 8–11.
- `acceptance/Teste_SAR_Altura_Estrutura_Tapajos_SF_Baixa.kml` — SF parcelas 21–23.

Esses KMLs permanecem CANDIDATOS até a execução real comprovar FH/H100 processável e AGB height-first numérica no próprio polígono.

### 3. ESA CCI Biomass v7
- Rota CEDA/ESA CCI v7 implementada.
- `AGB_SD` classificado corretamente como incerteza.
- Proveniência `SAR_DERIVED_CCI`.
- Modelo `ESA_CCI_BIOMASS_V7`.
- Grade 100 m.
- Gate corrigido depois da falha operacional do #351.
- No run #352, o gate live dos quatro assets 2024 Tapajós/Cerrado passou.

### 4. Cerrado DF
- ALOS/PALSAR L-band HV continua produzindo AGB quantitativa real no polígono de aceitação.
- Valor verificado anteriormente: 16.7534523925 Mg/ha.
- Incerteza de sensibilidade espacial: 11.2437158143 Mg/ha.
- Não é validação local nem IC95%.

## NOVA EVOLUÇÃO — biblioteca estrutural nacional

### Regra de dois níveis
1. **Dados primários abertos de árvore/parcela**
   - permanecem no nível real de observação;
   - gerar DAP médio, classes diamétricas, área basal, densidade de fustes, altura e demais métricas;
   - podem entrar em pareamento SAR somente quando houver suporte espacial/temporal compatível.

2. **Resultados finais publicados sem dados primários abertos**
   - permanecer no nível de estudo;
   - nunca expandir médias em parcelas sintéticas;
   - armazenar média, DP, EP, IC95, IQR, faixa, n de parcelas, n de sítios e desenho amostral quando publicados;
   - usar como prior, envelope de transferência, efeito de domínio e/ou síntese meta-analítica.

### Tratamento estatístico
Foi criado `structural_evidence.py`:
- `StructuralEvidence`
- `evidence_se()`
- `random_effects_summary()`
- `harmonize_primary_plot_rows()`

Regras:
- média + EP: usar EP publicado;
- média + DP + n: `SE = DP/sqrt(n)`;
- IC95: `SE ≈ largura/3,92`;
- IQR: converter a DP apenas como aproximação explícita `IQR/1,349`, se n conhecido;
- min–máx: somente envelope, sem peso de variância;
- síntese entre estudos comparáveis: efeitos aleatórios DerSimonian–Laird;
- reportar Q, tau² e I²;
- IC95 da média agrupada não deve ser interpretado como intervalo preditivo da AOI;
- nunca pseudo-replicar estudo agregado.

### Fontes estruturais nacionais cadastradas
Criado `data/structural_inventory_sources_v1.csv`.

Inclui como base:
- SFB/IFN DAP>=10 por UF — dados primários abertos;
- SFB/IFN DAP>=5/regeneração — dados primários abertos;
- SFB/IFN Unidades Amostrais — coordenadas/metadados;
- ORNL DAAC 1552 Tapajós — dados primários;
- Embrapa Amapá/IEF-AP/INPA;
- Embrapa Amazônia Ocidental/INPA;
- IFN/RJ Floresta Estacional Semidecidual;
- referência de Viçosa/MG;
- Castanho et al. Caatinga multi-sítio;
- de Jesus et al. Caatinga/Sentinel-1;
- Delitti et al. Cerrado;
- Oliveira et al. Cerrado DF.

O registro inicial NÃO deve ser chamado de exaustivo. Continuar ampliando com Embrapa, IFN/SFB/SNIF, UFRA, Museu Goeldi, INPA, INPE, UFLA, UFV, UFPR, UFT, UnB, USP e outras instituições idôneas.

### Cobertura IFN
O portal SFB confirma arquivos CSV DAP>=10 por UF e DAP>=5, além de unidades amostrais e outros componentes. Priorizar a transformação desses arquivos em tabelas estruturais por UA/subunidade e cruzamento por bioma/fitofisionomia.

### Integração ao pacote
- `sar_pipeline.py` importa o motor `structural_evidence`, garantindo inclusão no executável.
- Workflow copia `data/structural_inventory_sources_v1.csv` para o pacote Windows.
- Workflow verifica a presença do registro nacional no pacote.
- `tests/test_structural_evidence.py` protege:
  - não criação de parcelas sintéticas;
  - conversão IQR explicitamente rotulada;
  - faixa min–máx sem peso estatístico;
  - linhas de parcelas primárias preservadas como reais.

## Não regredir
Preservar:
- identidade visual aprovada;
- banner Enform Verde / Multisource;
- mapa IBGE offline;
- scroll visível e zoom;
- área em hectares;
- upload concluído;
- apagar pesquisa;
- CAR/CCIR automáticos;
- P > L > X > C > CCI;
- fallback separado do SAR;
- trilha cena → produto → pixels → modelo → AGB;
- Windows autônomo sem Python instalado.

## Próximas ações obrigatórias
1. Aguardar/conferir run #355 da cabeça `81f1227...`.
2. Se falhar: corrigir somente a causa comprovada, atualizar esta trilha e disparar novo run.
3. Se passar:
   - baixar/verificar artefato `Enform-Verde-Windows-v3.24.22-PROFESSIONAL`;
   - registrar Artifact ID, tamanho e SHA-256;
   - confirmar logs do probe BIOMASS FH nas AOIs Tapajós;
   - só chamar AOI de “GARANTIDA HEIGHT-FIRST” se FH/H100 real tiver sido processado e o modelo H100×G tiver retornado AGB numérica na própria AOI;
   - caso FH não cubra Tapajós, manter KML como CANDIDATO e buscar outro polígono brasileiro com interseção verificável de altura SAR + inventário horizontal.
4. Se todos os gates de software passarem, mesclar PR #48 em `main`.
5. Atualizar este prompt após merge com merge SHA e artefato final.
6. Continuar expansão da biblioteca estrutural nacional, priorizando dados primários IFN e inventários institucionais; onde não houver parcelas abertas, usar resultados agregados somente com o tratamento estatístico acima.

## Regra de comunicação
Não afirmar cobertura, altura SAR, AGB, validação, artefato ou merge sem evidência verificável da mesma cabeça de código.
