# ATUALIZAÇÃO V87.55 — 9 DE NOVEMBRO DE 2026 — VERSÃO 3.26.8 — CLASSIFICADOR SAR SEMÂNTICO INTEGRADO SOBRE A 3.26.7
Base: 1ef8429 (3.26.7, PR #51). A 3.26.7 incorporou as V87.39–V87.42, mas não o classificador SAR semântico (V87.43–V87.44); o fallback temporal exibia apenas “Área cultivada — candidato SAR experimental; cultura N/D”.
## Ordem de identificação do uso da terra
1. Classificador SAR instalado/configurado e validado (se houver).
2. Classificador SAR semântico embutido sar_brasil_rf_v2 (RF; 36 atributos mensais VV/VH/VH−VV Sentinel-1 RTC, 80 m; rótulos LEM+ INPE CC BY 4.0, INPE e-sensing Rondônia 2022 e Mato Grosso 2014–16; nunca MapBiomas). Validação em 708 blocos espaciais: OA 0,921 (0,911–0,931); floresta nativa precisão 0,93 (0,90–0,95); Cerrado nativo 0,88; cultivo 0,96; Amazônia-RO 0,888. Aplicado somente no domínio validado (savana/Cerrado, ou floresta no envelope 66,7–45,4°W × 17,5–7,7°S).
3. Culturas dentro do cultivo: soja, milho, algodão, café (OA 0,958 no LEM+). Pixel sem cultura com maioria (probabilidade máxima < 0,5) → “Área cultivada — cultura não identificada”.
4. Fora do domínio: candidato temporal da 3.26.7 (“Área cultivada — candidato SAR experimental; cultura N/D”) e N/D.
## Teste real
- Sinop (2025/26, 30 cenas, órbita 141): FESV Submontana 414,7 ha (nativa SAR nomeada pelo IBGE), soja 512,6 ha, área antrópica recente 745,8 ha, demais < 10 ha.
## Pendências mantidas
- Altura de culturas para vigor combinado (sem coeficientes publicados verificáveis), altura de formações nativas por SAR com inventários microrregionais, gate científico independente.
