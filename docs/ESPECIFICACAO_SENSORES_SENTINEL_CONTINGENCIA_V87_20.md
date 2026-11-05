# Especificação técnica V87.21 de acesso a Sentinel-1 e contingência multissensor

Data: 05/11/2026. Escopo: tornar a aquisição de dados atuais auditável e repetível, priorizar Sentinel-1 e usar fontes alternativas sem confundir sensores ou transformar falhas técnicas em ausência de dados. Esta revisão também corrige a contabilização de cobertura não mapeada e de classes explicitamente não nativas.

## Fluxo Sentinel-1 prioritário

1. Consultar a coleção RTC pública `sentinel-1-rtc` por STAC, interseção exata da geometria AOI em EPSG:4326, intervalo UTC limitado e paginação completa.
2. Selecionar VV e VH, mesma órbita relativa e direção, cenas espaçadas e cobertura temporal necessária. A catalogação sozinha não comprova disponibilidade.
3. Solicitar SAS fresco pelo endpoint MPC baseado no ID `sentinel-1-rtc`. Usar endpoint storage-account/container somente como compatibilidade se a rota oficial falhar. Nunca armazenar token nem escrever URL assinada em logs.
4. Ler COG HTTPS com TLS verificado, retries/retry delay e janelas limitadas à AOI. Se a cena falhar, solicitar SAS novo e repetir uma vez. Tentar cenas suplentes da mesma órbita até 12 candidatas, mantendo data recente e separação temporal.
5. Validar pixels não NoData VV/VH, CRS, interseção e fração da AOI observada; registrar scene ID, órbita, data UTC, polarization, pixels válidos, cobertura e qualidade.
6. Não executar classificador ou vigor quando não houver pixel válido suficiente ou modelo validado para a variável pedida.

## Rotas de contingência Sentinel-1

| Ordem | Fonte/rota | Produto e autenticação | Uso e limites |
|---|---|---|---|
| 1 | Microsoft Planetary Computer STAC | Sentinel-1 RTC, VV/VH; token SAS anônimo renovável | Rota de produção atual do app; pixels COG em janelas da AOI. |
| 2 | Copernicus Data Space Ecosystem STAC/OData | GRD/SLC; catálogo aberto, download/API autenticado conforme produto | Descoberta suplementar; produto GRD/SLC requer processamento compatível para comparação RTC. Não misturar valores sem normalização e QA. |
| 3 | ASF DAAC/Vertex + HyP3 | Sentinel-1 GRD e produto RTC on-demand; exige Earthdata Login para busca/submissão e consulta de jobs | Alternativa para RTC quando MPC COG falha. Baixar resultado processado, validar parâmetros RTC e geocodificação antes de combinar. |
| 4 | Arquivos oficiais ESA/CDSE | SAFE/GRD/SLC; usuário OAuth/credencial oficial | Último fallback para aquisição bruta; requer pipeline SNAP/RTC definido, DEM, órbita, calibração, terrain correction e auditoria antes de análise. |

Cada provedor deve registrar estado próprio. Falhar uma rota não encerra a busca: avançar para a próxima rota configurada e apta. Se as credenciais necessárias não estiverem configuradas, registrar `FALLBACK_NAO_CONFIGURADO`, sem simular aquisição e sem expor segredo. Produtos RTC de provedores diferentes só podem ser combinados após verificação de unidade, radiometria, resolução, máscara, órbita e processamento.

## Contingências de outros sensores

- Sentinel-2 L2A: refletância de superfície, índices ópticos e visualização. Exigir nuvem/sombra/água mascaradas, cenas com pixels efetivamente lidos, data, resolução e fração válida. EarthSearch e MPC são rotas de aquisição; GIBS/Esri são apenas visualização.
- Landsat 8/9 Collection 2 Level-2: continuidade temporal óptica em lacunas Sentinel-2; aplicar escala/offset e QA_PIXEL. Treinar e validar modelos de uso/cultura/vigor próprios para Landsat.
- GEDI e ESA Biomass: alturas/biomassa e referência de campo no suporte do footprint/resolução do produto. Não extrapolar automaticamente para raster contínuo da AOI.
- MODIS/VIIRS/GPM e clima: contexto fenológico, chuva e séries regionais; escala insuficiente para rotular talhão.
- Nenhuma alternativa óptica ou coarse pode aparecer no relatório como Sentinel-1. Nenhum fallback produz classes de fazenda sem validação independente apropriada.

## Estados do relatório

| Código | Significado | Ação |
|---|---|---|
| `N/D_DADOS` | Busca completa e rotas configuradas não encontraram cenas/serie/cobertura compatível | Registrar intervalo, provedores consultados, contagens e critérios. |
| `ERRO_TECNICO` | STAC incompleto, falha HTTP/auth/SAS, COG, decoder, CRS, reprojeção ou algoritmo | Registrar tipo e mensagem sanitizada por tentativa; renovar credenciais, repetir ou avançar ao próximo provedor. Nunca apresentar como ausência real. |
| `FALLBACK_NAO_CONFIGURADO` | Rota alternativa exige credencial ou dependência não configurada | Indicar rota e requisito, continuar demais opções e reportar lacuna de acesso. |
| `N/D_VALIDACAO` | Pixels foram obtidos, mas falta classificador/modelo independente compatível | Não produzir classe/estimativa; conservar medidas em auditoria. |
| `PROCESSADO_EXPERIMENTAL` | Medidas calculadas sem validação suficiente | Apresentar como experimental com incerteza e proibição de extrapolar ao imóvel. |
| `VALIDADO` | Produto passou validação independente no domínio e safra anunciados | Relatar amostras, validação externa, métricas e limitações. |

## Portas para usos downstream

- Identificação de cultura/vegetação atual: exigir classificador validado, sensor/fonte aceitos e máscara contemporânea. MapBiomas é referência anual histórica, nunca rótulo atual automático.
- Vigor: exigir pixels atuais datados, máscara de cultura verificada, métricas e incerteza; erro de acesso é ERRO_TECNICO e bloqueia projeção.
- Previsão de safra de propriedade: exigir cultura aceita, vigor válido, clima no período fenológico, modelo validado e área atual da máscara. PAM regional é prior/benchmark, não observação da fazenda.
- Biomassa/carbono: métricas de sensores de referência não substituem observações/parcelas; usar modelos e equações compatíveis com fitofisionomia e propagar incerteza.

## Evidência de aceite

A conclusão requer ao menos três cenas atuais da mesma órbita com pares VV/VH lidos na AOI e espaçamento temporal conforme a análise; registros de cobertura e ausência de falhas não recuperadas na série usada; fallback testado em falha forçada sem confusão com dados ausentes; testes e build Windows aprovados no mesmo SHA final; hash de artefato. Contratos sintéticos provam comportamento de código, não acesso orbital real nem homologação científica independente. Até comprovar pixel real na AOI, manter versão como candidata e não declarar a falha de campo definitivamente resolvida.

## Revisão V87.21 — leitura real e semântica de áreas desconhecidas

O Sentinel-1 prioritário tem regressão Windows de leitura efetiva das bandas VV e VH em COG sobre a AOI: a checagem requer valores de pixels válidos e não considera resposta HTTP parcial ou descoberta STAC como leitura concluída. A falha de uma cena provoca renovação do SAS e tentativa das cenas candidatas restantes; MPC e INPE RTC são consultados separadamente. Somente rotas e séries que completarem as verificações radiométricas, geométricas e de cobertura podem seguir para análise.

Na máscara de carbono nativo, fonte cartográfica histórica pode apoiar a exclusão de classe inequivocamente antrópica, como pastagem, soja ou área urbana, mas não pode confirmar vegetação nativa atual. Uma lacuna espacial sem classe permanece em unknown_cover_area_ha; pastagem explicitamente mapeada deixa de ser contada como lacuna; classes nativas oriundas apenas de MapBiomas continuam sem confirmação orbital. A área total deve reconciliar nativo + excluído + desconhecido, sem declarar cobertura completa quando há lacunas.

O bloqueio de regressão no SHA anterior expôs duas situações distintas: a fixture de uma classe nativa usava a fonte IBGE+MAPBIOMAS, contrariando a regra de exigir confirmação SAR; ela foi alterada para SAR_VALIDADO+IBGE e recebeu um teste explícito de que MapBiomas sozinho deixa a área desconhecida. Havia também um erro real em native_carbon.native_class: o retorno antecipado convertia uma classe cartográfica inequivocamente antrópica, como pastagem, em desconhecida. A decisão foi reordenada para permitir exclusão de rótulos antrópicos, mantendo MapBiomas incapaz de confirmar vegetação nativa. O novo SHA precisa passar a suíte completa do dashboard, a leitura real VV/VH e o build Windows; testes sintéticos não substituem o resultado de pixel real.

O painel agrícola mantém PAM como referência regional para a matriz de modelos, combinada com vigor observado e fatores climáticos. A série PAM não é produtividade medida da propriedade: sem cultura atual, vigor datado e modelo temporal/espacial aplicável, a previsão da propriedade continua bloqueada e a projeção regional permanece identificada como cenário de referência.