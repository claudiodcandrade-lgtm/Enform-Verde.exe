# REVISÃO v76 — TRIAGEM ORBITAL REAL SENTINEL-1 NA AOI — 04/11/2026
## Ocorrência informada: Fazenda Maria Eduarda, Sinop/MT
- Área da AOI no relatório fornecido: 1.459,91 ha. MapBiomas C11 2025: vegetação cartográfica 917,81 ha, soja 535,73 ha, outras lavouras 4,98 ha e outros usos 1,39 ha. Distribuição anual não comprova a ocupação de 2026/27.
- Erro visual: região fitoecológica IBGE exibida com percentual territorial foi interpretada como 100% de floresta estacional sempre viva. A interface agora distingue região FITOGEOGRÁFICA POTENCIAL de cobertura atual.
- Falha relatada: GDAL/UnicodeDecodeError na leitura de Sentinel-1, sem pixels VV/VH suficientes; a previsão histórica PAM/FAO é cenário regional, não monitoramento radar da safra atual.
## Hierarquia de implementação
- Classificação operacional potencialmente mais robusta: ESA WorldCereal no openEO/CDSE (Sentinel-1 + Sentinel-2), com autenticação, emprego de modelo por região e validação. Os mapas globais WorldCereal disponibilizados atualmente não provam culturas da safra atual nesta propriedade.
- Implementação automática nesta revisão: módulo recent_sar_landcover.py consulta cenas Sentinel-1 RTC da Microsoft Planetary Computer, obtém SAS temporário e lê recortes COG VV/VH no polígono. Exige pelo menos três cenas de mesma órbita relativa e direção ao longo de >=35 dias, última <=30 dias. Leitura fail-closed.
- Algoritmo experimental: VH_t,dB=10 log10(VH_t linear); L=mediana temporal VH; A=P90_t(VH)-P10_t(VH). Candidato lenhoso persistente se L>=P65 espacial(L) e A<=P35 espacial(A); candidato mudança sazonal se A>=P70 espacial(A) e L<P75 espacial(L). Demais pixels = indeterminados. Filtro de manchas <12 pixels.
- Exportações: raster GeoTIFF classes 1/2/3 e vetor GeoJSON quando volume manejável, áreas por interseção espacial projetada EPSG:6933, IDs/datas das cenas, órbita, cobertura de pixels, falhas sem expor SAS. Integração no relatório do painel de agricultura e na auditoria; não modifica a classificação cartográfica anual.
- Limite científico obrigatório: classe 1 NÃO comprova vegetação nativa; classe 2 NÃO comprova lavoura. Áreas candidatas NÃO são hectares validados, não alimentam diretamente o carbono ou produção de soja, não possuem IC95% nem matriz de confusão. Ausência de pixels retorna N/D.
- Radar C-band para detecção de padrões de cobertura não altera prioridade BIOMASS P e X, posteriormente L, nos fluxos apropriados de AGB/altura.
## Validação e distribuição
- Testes de contrato usando pixels sintéticos verificam classificação matemática e falha N/D; não são evidência orbital nem homologação científica.
- Validar execução AOI real Fazenda Maria Eduarda com cenas VV/VH auditáveis, melhorar caso de erro Unicode Windows e substituir índices heurísticos por modelo treinado e avaliação independente. WorldCereal sob demanda exige condições de serviço apropriadas.
- Nenhum executável anterior contém esta alteração. Somente distribuir EXE novo após teste completo, autoteste Windows, checksum e mesmo SHA.
