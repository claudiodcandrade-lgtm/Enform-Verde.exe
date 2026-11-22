# Checkpoint V88.51 — estimativas e handoff do SAR

Versão candidata: `3.26.34-PRECAMPO-EXPERIMENTAL`. Em 14/11/2026 foi identificado e corrigido o descarte de SAR no caminho worker → `_execute_main` → dashboard: o worker transmitia um dicionário vazio, enquanto o resultado por estrato ficava apenas dentro de `native_carbon`. Agora se constrói um payload AOI agregado, com trilha SAR por estrato e cobertura agrícola, e ele é preservado no projeto.

A contingência de inventário exige certificado de ausência de cenas completo, sem erros, cenas ou pixels processados. Nenhuma falha técnica é tratada como ausência. Necromassa acima/abaixo do solo é a exceção explicitada para falta de equação alométrica; todos os demais compartimentos requerem estimativa experimental rastreável, com fonte, área-base e incerteza declaradas.

Verificação local: `py_compile` passou nos módulos alterados. Testes de integração/regressão ficaram bloqueados porque este ambiente não possui `requests` e `geopandas`; não foram considerados aprovados. Ainda pendem CI, build Windows, execução real de AOI até os painéis e confirmação de estimativas numéricas por compartimento. Estado experimental, não homologado.
