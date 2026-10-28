# Enform Verde — Especificação técnica do carbono orgânico do solo até 100 cm
Data: 28/10/2026 (UTC−3)

## Escopo obrigatório — faixa 0–100 cm

**Concentrar todas as consultas ao serviço PronaSolos de estoque de carbono nas cinco camadas 0–5, 5–15, 15–30, 30–60 e 60–100 cm (IDs ArcGIS 2, 3, 4, 5 e 6).** Não consultar a camada de 100–200 cm (ID 7), não compor 0–200 cm e não somar novamente subtotais cumulativos ao estoque de 0–100 cm.

Serviço oficial auditável da Embrapa Solos/PronaSolos disponibilizado via SGB: https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer

Conforme metadados do MapServer, a resolução espacial do raster é **90 m** e os rasters indicam estoque de carbono em Mg C/ha (numericamente tC/ha). O mapeamento é preditivo e depende de covariáveis, dados de solos legados e da metodologia indicada no relatório técnico oficial. Não realizar falso aumento de resolução espacial.

## Consulta e composição

- Geometria da AOI transformada para EPSG:3857 exclusivamente para consulta ao MapServer; a área do estoque final permanece determinada por projeção equivalente no módulo de carbono.
- Amostragem sistemática de até 36 pontos dentro da geometria mais um ponto representativo, com desduplicação e limite no número efetivamente consultado.
- **Uma requisição `identify` por ponto, para `layers=all:2,3,4,5,6`.** Resposta deve conter ID de camada para associar os valores por profundidade; NoData, falhas de serviço e valores inválidos não viram zero.
- 0–30 cm = 0–5 + 5–15 + 15–30; 0–60 cm acrescenta 30–60; 0–100 cm acrescenta 60–100. Cada total é composto **exclusivamente de camadas recebidas no mesmo ponto espacial**, não de médias de horizontes provenientes de amostras diferentes.
- Amostragem do raster e desvio-padrão espacial do estoque total no subconjunto de pontos válidos são **estatísticas descritivas**. Nunca atribuir IC95% preditivo apenas com variabilidade entre pixels: faltam erro do mapa, covariâncias, viés espacial e erro de transferência. Guardar proveniência, N e ausência da estimativa de incerteza.
- Se 0–30 cm não puder ser composto, registrar falha explícita; se 0–100 cm estiver indisponível, marcar `INCOMPLETO_NAO_EXTRAPOLAR` e não derivar 0–100 cm de 0–30 ou usar zero. Resumos das profundidades disponíveis são apenas informativos.
- Carbono do solo de 0–100 cm só integra o estoque da fitofisionomia quando efetivamente estimado para a geometria nativa compatível. Não atribuir estoque do solo das áreas cultivadas ao carbono de vegetação nativa.

## Melhoria operacional esperada

Até 36 consultas HTTP totais por AOI para até cinco horizontes, contra até 180 consultas com o algoritmo anterior (5 consultas separadas por ponto) ou 216 consultas com seis horizontes. Esse fator teórico de redução de chamadas **não é benchmark real de tempo de resposta**; a latência da API, o tamanho das AOIs e a taxa de falhas ainda exigem medição.

## Evidência de código e teste

- `pronasolos_identify.py`: `LAYER_IDS=(2,3,4,5,6)`; construção dos parâmetros batched e extração dos resultados por ID e por ponto.
- `soil_profile_stats.py`: totalização independente e pareada exclusivamente 0–30, 0–60 e 0–100 cm.
- `desktop_app.py`: `pronasolos_soc_profiles` integra a requisição em lote e expõe diagnóstico do atendimento de 0–100 cm.
- `tests/test_pronasolos_identify.py` e `tests/test_soil_profile_stats.py`: casos sintéticos de horizontes coincidentes, ausência, NoData, erro de serviço, proibição de consulta à camada 7 e não contabilização de perfil mais profundo.
- `.github/workflows/build-windows.yml`: contrato GUI exige 0–100 cm e as cinco camadas na origem do código.

**Pendência de homologação:** verificar os testes Windows e a execução com retorno **real da API oficial**, demonstrar a completude 0–100 cm e incerteza defensável com fontes institucionais, e produzir o executável Windows testado no mesmo SHA homologado. **Sem liberação definitiva apenas por compilação.**
