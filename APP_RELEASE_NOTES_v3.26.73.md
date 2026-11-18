# Enform Verde v3.26.73-PRECAMPO-EXPERIMENTAL

## Gate de elegibilidade ESA CCI antes da aquisição

- O pipeline agora verifica a elegibilidade da contingência antes de consultar ou baixar o histórico CCI, eliminando aquisição grande quando FH está disponível, a rota prioritária não foi resolvida ou falta calibração CCI–inventário validada.
- A auditoria diferencia `NAO_ADQUIRIDO_GATE_BLOQUEADO`/`download_skipped=true` de falha técnica em download efetivamente tentado.
- O teste impede regressão que inicie a aquisição CCI com a rota FH não resolvida.
- Não alterados os limiares científicos. Não foram criados coeficientes nem resultados de calibração.

## Situação

Candidata pré-campo/experimental, ainda sem executável liberado. A correção não supre a ausência de modelo AGB FH aplicável nem de calibração ESA CCI–inventário. FH com pixels válidos sem modelo continua N/D explícito; erro técnico não vira ausência real de cenas. A distribuição exige regressão integral e gates Windows/SAR→dashboard no SHA final. Homologação científica exige validação de campo independente.
