# REVISÃO v78 — Teste de rótulo IBGE potencial coerente com v77 (04/11/2026)
- A rotina ibge_area_summary_lines foi corrigida no v77 para rotular a região fitoecológica IBGE como POTENCIAL e não como cobertura atual; o teste legado tests/test_ibge_area_summary.py ainda exigia a cadeia antiga. Agora valida o texto novo, sem reduzir a conferência de ha, porcentagens e erro de fonte.
- Permanecem inalterados: nome por IBGE, área nativa estratificada pela interseção da máscara de cobertura, percentual com base na AOI total, exibição do bioma e apresentação N/D para cobertura ausente.
- Exigir suíte completa, teste Windows de interface, processamento de uma AOI real e build de mesmo SHA; a homologação científica permanece separada e reprovada.
- Não declarar o erro UnicodeDecodeError/GDAL resolvido antes de um teste de aquisição de dados VV/VH real em Windows. Os candidatos SAR S1 são experimentais e não substituem classificadores treinados para lavouras/nativa.
