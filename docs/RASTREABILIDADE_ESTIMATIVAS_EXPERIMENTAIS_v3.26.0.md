# Enform Verde 3.26.0 — auditoria de estimativas experimentais

Atualizacao: 2026-11-04. Esta implementacao nao constitui homologacao independente.

O modulo `experimental_audit.py` registra, para cada estimativa, formacao IBGE, area efetiva, densidade, estoque em tC e tCO2e, formula, fonte, metodo, tipo de incerteza e hash deterministico do rastro. A ausencia de bytes verificados fica declarada. Intervalos da fonte, multiplicados pela area, nao representam IC95% da AOI se faltarem erro de transferencia, incerteza de classificacao e covariancias.

A previsao experimental so pode ser exibida quando o modelo retornar dominio espacial/temporal, fonte e hash declarados, metodo de intervalo, limites e identificador de modelo. Ao lado do numero aparece 'ESTIMATIVA EXPERIMENTAL (nao homologada)'. PAM/SIDRA por microrregiao nao e validacao de rendimento de talhao.

Fontes: PronaSolos/Embrapa Solos 0-100 cm https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer; SFB/IFN https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono; MapBiomas Colecao 11 https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-30m/cobertura/; PAM/IBGE https://sidra.ibge.gov.br; FAO56 https://www.fao.org/4/x0490e/x0490e05.htm; FAO33/66 https://www.fao.org/4/i2800e/i2800e00.htm.

O gate `scientific_release_gate.py` segue intacto e continua exigindo dados primarios e avaliacao independente. Os patches de solo, agricultura e build Windows permanecem um item separado a integrar; nunca aceitar regressao ou pular o gate de evidencia.
