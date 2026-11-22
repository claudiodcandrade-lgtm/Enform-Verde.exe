# REVISÃO V87.1 — 05/11/2026 — CORREÇÃO SEMÂNTICA NO SOC 0–100 CM

## Diagnóstico do problema

`soil_pronasolos_zonal.py` retornava `predictive_uncertainty_quantified=True` quando estavam disponíveis limites marginais oficiais (lower/upper) por horizonte, apesar de reconhecer corretamente que a soma não formava IC95% conjunto. Um consumidor de metadados poderia tratar o valor booleano como sinal de acurácia de previsão calibrada da AOI.

## Correção implementada

Para os cinco horizontes 0–5, 5–15, 15–30, 30–60 e 60–100 cm, preservar por identidade espacial e média ponderada `sum_bounds_envelope_tc_ha`, `sum_bounds_envelope_stock_tC`, limites marginais por horizonte, rastreabilidade e `status=ENVELOPE_MARGINAL_OFICIAL`. Alterar `predictive_uncertainty_quantified` para **False** no mapa `official_uncertainty` e no compartimento de SOC 0–100 cm e declarar explicitamente `marginal_envelope_available=True`. Falha de serviço e ausência de limites seguem N/D; soma de carbono 0–100 cm recuperada não deve desaparecer por falta dos limites.

O envelope `[Σ L_h, Σ U_h]` é apenas intervalo computado de limites publicados por horizonte. **Não** traduz cobertura conjunta 95% nem inclui transferência, viés, erro de classificação, correlação entre horizontes, dependências espaciais ou incerteza total do imóvel. DP espacial não é erro do estimador.

## Teste de regressão

`tests/test_soil_fertility_official_uncertainty.py::test_marginal_bounds_envelope_not_joint_ci` deve exigir `marginal_envelope_available` verdadeiro e `predictive_uncertainty_quantified` falso nos dois lugares, preservando soma e estoque por área e aviso textual.

## Requisitos de distribuição

Candidato `Enform Verde 3.26.1-PRECAMPO-EXPERIMENTAL`: SHA do código, testes de contrato/geoespaciais e EXE Windows compilado validado são necessários para liberação técnica, com artefato ZIP e SHA256. Gate científico independente permanece fail-closed e a versão não constitui certificação de estoques.
