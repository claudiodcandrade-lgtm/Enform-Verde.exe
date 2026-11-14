# Enform Verde 3.26.34 — pré-campo experimental

- Corrige o handoff do resultado SAR por estrato até `project['sar_result']`, preservando proveniência e auditoria para os painéis.
- Corrige erro sintático na trilha pública ALOS/PALSAR do pipeline SAR.
- Exige certificado completo de ausência de cenas para contingência por inventário; erro técnico, cena ou pixel SAR processado bloqueia essa contingência.
- Regra de apresentação: estimar todos os compartimentos aplicáveis com fonte e incerteza rastreáveis. Necromassa acima e abaixo do solo são exceções explícitas quando não houver equação alométrica aplicável.
- `py_compile` passou localmente. Testes direcionados, CI e build Windows não foram confirmados neste ambiente por ausência de dependências geoespaciais/HTTP.
- Não homologado; teste de AOI real ponta a ponta continua necessário.
