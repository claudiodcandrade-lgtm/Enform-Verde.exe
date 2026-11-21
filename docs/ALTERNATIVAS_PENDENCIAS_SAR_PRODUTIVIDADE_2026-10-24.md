# Alternativas para resolver as pendências SAR × produtividade

Atualizado em 24/10/2026. Este documento trata da série PAM real já disponível e da lacuna entre encontrar cenas Sentinel‑1 e conseguir extrair retroespalhamento em máscaras de cultura independentes.

## Decisão recomendada

Executar uma rota em duas fases, começando por soja e milho no Brasil:

1. Usar os polígonos e dados de colheita de YieldSAT como referência independente para identificar os campos e testar um classificador de cultura com Sentinel‑1 retrospectivo. O conjunto publicado informa 293 campos brasileiros de soja e 118 de milho, entre 2017 e 2024; os insumos orbitais listados são Sentinel‑2, clima, solo e topografia, portanto a série Sentinel‑1 terá de ser extraída separadamente. Holdouts devem separar fazendas/regiões e safras.
2. Usar Sentinel‑1 de uma fonte autenticada ou processada em nuvem (opções abaixo), gerar features calibradas por campo para treino/validação e, após atingir métrica independente e cobertura territorial demonstrada, inferir máscara de cultura por microrregião. Só então agregar SAR sobre pixels da cultura e parear com PAM N9 na mesma cultura, safra e unidade territorial.

YieldSAT permite validação de milho e soja e comparação de produtividade em escala de campo. Por si só não valida arroz, café, cana, feijão, laranja/citros ou sorgo, nem prova que um modelo de Sentinel‑1 transfere para qualquer microrregião. Métricas publicadas com Sentinel‑2 não podem ser atribuídas ao SAR.

## Rotas para obter valores Sentinel‑1

| Alternativa | Como contorna a falha de COG | Autenticação/custo | Uso recomendado | Limite |
|---|---|---|---|---|
| Microsoft Planetary Computer Sentinel‑1 RTC | Consultar STAC público e assinar asset COG com endpoint SAS público e temporário; ler por HTTP Range/GDAL | Sem login individual no teste; sujeito a limites públicos e validade do SAS | Rota primária para extração COG; descoberta e byte range foram testados nesta sessão | Ainda falta ler valores VV/VH geoespaciais; RTC tem processamento próprio que deve ser auditado |
| Copernicus Data Space (CDSE) OData/download OAuth2 | Usar STAC/OData para descobrir cena; baixar SAFE/GRD com token OAuth2 e processar localmente com SNAP/GDAL | Conta CDSE; token curto renovado com refresh token | Alternativa para dados nativos e reprocessamento controlado | Download de cena completa é grande; COG sem bearer token respondeu erro de acesso |
| ASF DAAC + HyP3 | Pesquisar Sentinel‑1 no ASF e solicitar RTC/ortorretificação on‑demand; consumir produto de saída | Conta gratuita Earthdata Login; credencial/token mantido pelo usuário | Segunda alternativa para RTC e processamento repetível | Dependência externa/limites de cota e autenticação; registrar parâmetros do HyP3 |
| Google Earth Engine `COPERNICUS/S1_GRD_FLOAT` / `S1_GRD` | Consumir coleção hospedada já calibrada/geocodificada e exportar estatísticas zonais | Conta e autenticação Earth Engine; verificar termos e quotas atuais | Terceira alternativa para protótipo ou checagem cruzada | Não é execução totalmente autônoma offline; quotas e pré-processamento devem ser registrados |

**Seleção após teste:** Planetary Computer RTC é a primeira rota para extração por janela: STAC público, endpoint SAS anônimo e resposta HTTP 206 foram confirmados. CDSE OAuth2 fica como alternativa para dados nativos/reprocessamento. ASF/HyP3 e Earth Engine permanecem rotas adicionais com credenciais. Não persistir o SAS; renovar em runtime. Antes de promover o MPC, completar leitura Rasterio/GDAL de VV/VH, conferir CRS/unidades/processamento e cobrir AOIs reais.

## Rotas para validar a máscara de cultura

1. **YieldSAT — primeira escolha para soja e milho.** Campos brasileiros têm rótulo/campo e produtividade de colhedora, com Sentinel‑2, não Sentinel‑1. Usar geometrias e anos acessíveis conforme condições de compartilhamento/licença, coletar as cenas S1 coincidentes, treinar classificador temporal SAR e validar em fazendas/regiões e anos totalmente retidos. Primeiro confirmar que polígonos e licença permitem uso comercial no Enform Verde.
2. **Mapa agrícola público independente como referência de avaliação, não como verdade de píxel.** Usar mapas oficiais ou estudos com amostras rotuladas independentes para estabelecer estratos e estimar matriz de erro. MapBiomas pode fornecer proporções/áreas candidatas, mas não servir simultaneamente de rótulo do classificador e validação independente.
3. **Rótulos PAM/SIDRA como supervisão fraca agregada.** PAM fornece produção, área e rendimento em N9, não pixels de lavoura. Métodos de aprendizado por proporções/weak supervision podem ajustar composição de uma região, mas requerem amostras de validação por talhão independentes; sem elas, não publicar acurácia de máscara nem chamar o resultado de cultura confirmada.
4. **Abstenção para culturas sem amostras independentes.** No produto, manter “áreas cultivadas” ou “não identificada” para culturas sem modelo e teste adequados. Não transferir o classificador de soja/milho para as seis culturas restantes.

## Desenho analítico depois de obter a máscara

- Resolver o pareamento N9 com malha e códigos geográficos compatíveis durante 2015–2024; registrar a malha e qualquer tabela de correspondência. Excluir ou harmonizar explicitamente territórios cujo código/limite mudou.
- Mapear a janela fenológica por cultura e região; excluir observações incompatíveis com plantio/colheita e culturas de segunda safra que se sobreponham sem separação.
- Corrigir/calibrar VV/VH, razão VH/VV, ângulo de incidência, órbita relativa, ruído e água/inundação. Registrar datas UTC, cenas, assets, versão do processador e percentual de área válida.
- Calcular estatísticas apenas sobre pixels classificados como cultura. Fazer análise de associação robusta com blocos espaciais e safra, controlando clima, tendência tecnológica, área colhida e dependência temporal/espacial.
- Comparar três referências: rendimento PAM histórico defasado; PAM histórico + clima; PAM histórico + clima + SAR. Reservar holdout espacial e temporal antes de modelar; produzir bootstrap por microrregião/bloco e safra.
- Chamar o resultado inicialmente de associação administrativa/ecológica, não causal. A inferência é produtividade média da microrregião, não produtividade de talhão. Só habilitar previsão após demonstrar melhoria fora da amostra e intervalo preditivo calibrado.

## Estado observado nesta atualização

- A série PAM 5457 N9 (2015–2024), 8 produtos, variáveis 112/214/216 foi baixada e materializada no repositório com 133.920 linhas e checksum. Isso é produtividade/produção/área observadas, não correlação SAR.
- Os COGs do CDSE falharam sem autenticação. Como alternativa pública, o STAC Microsoft Planetary Computer retornou uma cena VV/VH RTC sobre Brasília em 29/01/2023 às 08:45:43.608955 UTC. Um SAS temporário obtido anonimamente permitiu HTTP Range 206 e leitura de 1.024 bytes do asset VV (objeto de 1.856.447.477 bytes). Isso confirma acesso ao objeto, mas ainda não decodifica valores raster de pixels; não há valores SAR mascarados por cultura nem correlação validada.
- A previsão permanece bloqueada. O próximo marco é abrir/ler uma janela raster real via GDAL/Rasterio, confirmar unidades e CRS, validar acesso/licença YieldSAT, testar máscara em holdout independente e criar o primeiro conjunto pareado soja/milho. ASF/HyP3 fica como fallback; nunca usar SAR médio de toda a microrregião como se fossem pixels da cultura.

## Fontes primárias consultadas

- IBGE SIDRA PAM tabela 5457 e API: https://sidra.ibge.gov.br/tabela/5457 ; https://apisidra.ibge.gov.br/
- YieldSAT dataset e documentação: https://yieldsat.github.io/ ; https://arxiv.org/abs/2604.00940
- Copernicus Data Space OData e autenticação: https://documentation.dataspace.copernicus.eu/APIs/OData.html
- Microsoft Planetary Computer STAC e assinatura de assets: https://planetarycomputer.microsoft.com/docs/ ; https://planetarycomputer.microsoft.com/docs/concepts/sas/
- ASF HyP3 autenticação Earthdata: https://hyp3-docs.asf.alaska.edu/using/authentication/
- Google Earth Engine Sentinel‑1 GRD e processamento: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD ; https://developers.google.com/earth-engine/guides/sentinel1
