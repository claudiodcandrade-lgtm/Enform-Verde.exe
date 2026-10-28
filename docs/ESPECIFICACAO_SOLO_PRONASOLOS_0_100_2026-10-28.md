# Enform Verde — Especificação técnica do carbono orgânico do solo até 100 cm
Data: 28/10/2026 (UTC−3)

## Escopo obrigatório — faixa 0–100 cm

**Concentrar todas as consultas ao serviço PronaSolos de estoque de carbono nas cinco camadas 0–5, 5–15, 15–30, 30–60 e 60–100 cm (IDs ArcGIS 2, 3, 4, 5 e 6).** Não consultar a camada de 100–200 cm (ID 7), não compor 0–200 cm e não somar novamente subtotais cumulativos ao estoque de 0–100 cm.

Serviço oficial auditável da Embrapa Solos/PronaSolos disponibilizado via SGB: https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer

Conforme metadados do MapServer, a resolução espacial do raster é **90 m** e os rasters indicam estoque de carbono em Mg C/ha (numericamente tC/ha). O mapeamento é preditivo e depende de covariáveis, dados de solos legados e da metodologia indicada no relatório técnico oficial. Não realizar falso aumento de resolução espacial.

## Consulta e composição

- Geometria da AOI transformada para EPSG:3857 exclusivamente para consulta ao MapServer; a área do estoque final permanece determinada por projeção equivalente no módulo de carbono.
- Amostragem sistemática dentro da geometria, incluindo um ponto representativo, com desduplicação e limite de **até 36 pontos totais por AOI** (padrão atual; menor se a área não contiver pontos suficientes).
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


## Controle adicional de valor bruto e prova do serviço — 28/10/2026

Os valores `Stretched Pixel Value`, `Renderer Value` e `Display Value` de respostas ArcGIS não são medições de estoque de carbono: podem representar intensidades de renderização. **Nunca** converter diretamente esses atributos em Mg C/ha. Aceitar somente `value`, `Pixel Value`, `raw_value` ou sinônimos de valor bruto, finitos e não negativos. O teste `test_visualization_stretch_is_not_soil_stock` estabelece esta invariável. Commits: `4ba3299e697951f249af7ea7d59e70ca7b67b318` e `8a1d3b3b012cfaaf01f3c97142a6ed5424adb510`.

Para provar acesso real à API, `tools/probe_pronasolos_100cm.py` implementa consultas ao servidor SGB nas coordenadas geográficas de cinco pontos de referência (Amazônia/Tapajós, Cerrado/Brasília, Caatinga/Petrolina, Mata Atlântica/Itapetininga e Pantanal/Nhecolândia). O workflow Windows grava `pronasolos_probe_100cm.json` e publica artefato `pronasolos-100cm-audit` com os códigos de estado, valores brutos retornados de todas as cinco camadas, hash SHA-256 da resposta e motivo dos erros. Commits `6b014040d0ad145d0e6cc34260751b2e51cfdbed`, `fa2b6ff2030be4e020e6066f78c8e5facd4a35c8`, `76a82f9678db13bea5cd8fc18067548e08beb0b1` e `ac03501446a9be9aedc1cea239c410684c9e75f2`.

Esse teste de acesso é **não bloqueante por indisponibilidade de rede**, mas uma falha não pode ser interpretada como comprovação de cinco biomas. Mesmo êxito em cinco pontos **não constitui** validação de estoques da AOI, de incerteza preditiva, de fitofisionomia específica ou de precisão de 95%. O release científico exige evidência adicional.
