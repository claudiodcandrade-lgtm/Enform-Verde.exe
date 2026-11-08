# REVISÃO V80 — Aplicabilidade nacional, incerteza e auditoria científica (04/11/2026)
## Abrangência para qualquer AOI brasileira
- Todos os seis biomas brasileiros devem receber tentativas de processamento: Amazônia, Cerrado, Caatinga, Mata Atlântica, Pantanal e Pampa. Restrições de cobertura, período, sensor, autenticação, domínio de modelos e qualidade de evidência são registradas por AOI, sem alegar homogeneidade de disponibilidade nacional.
- Sempre retornar resultados fundamentados quando houver fonte aplicável; se uma classe, biomassa, solo ou cultura não puder ser inferida de maneira defensável, retornar N/D com razão, em vez de inventar números ou IC95%.
- Separar ESTOQUE/TAXA ESTIMADA, DISTRIBUIÇÃO CARTOGRÁFICA HISTÓRICA, OBSERVAÇÃO ORBITAL ATUAL e IDENTIFICAÇÃO SAR VALIDADA como estados não intercambiáveis.
## Auditoria geoespacial e incerteza
- Módulo national_analysis_audit.py: geometria auditável por SHA256 do WKB WGS84; área da AOI em EPSG:6933, area_ha=area_m2/10000, participação percentual 100 x area_classe_ha/area_AOI_ha; fechamento espacial e tolerância registrados.
- Salvar por classe fontes, estado cartográfico ou SAR atual, estatísticas de área, data UTC de execução, IDs de cenas efetivamente lidas, caminho de GeoTIFF/GeoJSON quando existente, limitações e incerteza de classificação local = N/D sem referência independente.
- Nunca somar áreas de triagem SAR aos polígonos MapBiomas; nunca declarar que SAR experimental comprova vegetação nativa, agricultura, vigor, acurácia ou previsão de produtividade. Evitar conversão da variação do radar em intervalos estatísticos calibrados.
- A incerteza de carbono (tC/ha, tC, tCO2e), dos componentes e da área de cobertura deve ser exibida e auditada separadamente. IC95% somente com matriz ou parâmetros estatísticos defensáveis. Solo 0–100 cm apenas em interseções com camadas reais, sem conversão de 0–30 cm por multiplicador arbitrário.
## Falhas de engenharia descobertas e reparos de v80
- A compilação Windows de v79 falhou no teste GUI, pois o contrato exigia a cadeia obsoleta «Fitofisionomia IBGE». Agora a verificação exige «Fitofisionomia presente na propriedade» e uso de native_carbon.strata.
- O gate documental falhou ao exigir atualização binária Word no MESMO commit, embora o sincronizador Word gere o DOCX em commit posterior. Agora exige prompt + checkpoint técnico revisado no commit de código + workflow de sincronização Word verificável; também aceita Word no mesmo commit.
- Registro explícito dos módulos dinâmicos national_analysis_audit, recent_sar_landcover e property_physiognomy_display no PyInstaller.
- Radar SAR: escolher série de órbita compatível com cobertura temporal suficiente, não apenas a órbita da cena mais recente; manter pixels sem observação como nodata=0 após filtragem, não convertê-los em classe 3; remover URLs com SAS da mensagem de erro.
## Integração e validação
- Revisões implementadas no código, sujeitas a novo CI e build no SHA definitivo; não atribuir essas correções ao ZIP do SHA 8839435427a3f3a4e0370de5082d666b406df50a.
- Casos de controle: seis biomas com dados sintéticos apenas de teste de contrato, AOI sem CRS, fechamento cartográfico, cenas em órbitas alternativas, dados SAR faltantes, sigilo dos tokens e identificação coerente de áreas/fitofisionomias.
- Na ausência de comprovação independente de modelo, campo e medição orbital na AOI, o gate científico permanece reprovado. A avaliação experimental nacional é uma funcionalidade operacional distinta de homologação científica.
