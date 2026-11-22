# V88.109 — dependências de teste e gates locais concluídos
## Registro de validação — 16 de novembro de 2026
- Ambiente isolado de testes reconstruído a partir de `requirements_desktop.txt` em `/tmp/enform-geo-runtime`, sem alterar o Python global. GeoPandas 1.2.0, Requests 2.34.2, Shapely 2.2.0 e Rasterio 1.5.2 foram confirmados por importação.
- `tests/test_core_to_dashboard_handoff.py`: 4/4 aprovados. `tests/test_analysis_pipeline_contract.py`: 6/6 aprovados. `tools/check_test_collection.py`: 183 módulos inspecionados, sem falhas de importação.
- Suíte completa: 1.239 testes, `OK (skipped=1)`. O skip ocorreu no shell headless sem display gráfico; o teste visual estático passou.
- `ui_visual_standard.py` foi executado no desktop gráfico com as mesmas dependências e retornou `PADRAO_VISUAL_OK`.
- Aceitação SAR real no AOI público `acceptance/Teste_SAR_Biomassa_Tapajos.kmz` concluiu com `SAR_PROCESSADO`: 259.688 pixels, área calculada de 1.290,69 ha e proveniência `SAR_DERIVED_CCI`. O resumo auditável está em `validation/acceptance_tapajos_live_v88_109.json`. O teste confirma processamento nesta amostra, sem provar cálculo integral de todos os compartimentos ou chegada ao dashboard. A aquisição remota demorou vários minutos; não foi feito benchmark controlado.
- A especificação DOCX foi sincronizada com `3.26.57-PRECAMPO-EXPERIMENTAL`; o teste de atualização documental passou.
## Limites de evidência
- Os contratos de handoff testam propagação consistente por fixtures; não equivalem à execução do KML integral privado da Fazenda Maria Eduarda no aplicativo Windows.
- Build/teste do EXE Windows e execução integral no KML permanecem pendentes; não declarar homologação nacional nem validação de campo.
- Os resultados e parâmetros científicos continuam sujeitos às regras de domínio, proveniência, incerteza e N/D vigentes.
