# Catálogo ampliado de fontes externas — 23/10/2026

Este catálogo distingue **A: referência de campo georreferenciada potencial**, **B: referência interpretada/administrativa auditável**, **C: mapa secundário, apenas concordância/pseudo-rótulo**, **D: suporte fenológico/estrutural ou estatístico**. Não são resultados de validação dos modelos Enform Verde. Necessário confirmar licença, download, cobertura de classes, datas, formato e se houve uso prévio no treinamento. **Proibido confundir silvicultura com floresta nativa**.

| Fonte | Classe(s)/geografia | Tipo | Link | Condição |
|---|---|---|---|---|
| Goiatuba GO campo 2025/26 INPE/UnB/Embrapa | Culturas anuais, irrigadas, pastagem, nativa; Cerrado | A | https://doi.org/10.5281/zenodo.17612590 | 117 campos + 463 parcelas; verificar classes presentes e independência treino/teste |
| ESA WorldCereal RDM (plataforma) | Culturas multirregionais, incluindo bases brasileiras identificáveis | A/B | https://esa-worldcereal.org/en/reference-data | Filtrar país, amostras de campo, safra, cultura e licença; não usar safras incompatíveis |
| WorldCereal dados harmonizados Zenodo | Culturas; inclui INPE-LEM, JECAM-CIRAD, CropHarvest | A/B | https://zenodo.org/records/7593734 | Selecionar arquivos brasileiros, datas, CT/sampleID, qualidade e separação espacial |
| PLOS WorldCereal estudo harmonização | INPE-LEM 2020, JECAM-CIRAD 2016–19, CropHarvest Brasil 2018–20 | A/B | https://doi.org/10.1371/journal.pone.0287731 | Identificar nível de referência FO/CV/FD/AC antes de validar |
| Arroz irrigado SC, Mendeley Data/INPE | Arroz, SC; Sentinel-1 e Sentinel-2 | A/B | https://doi.org/10.17632/3n8ms32thw.2 | Disponibiliza blocos treino/validação; excluir vazamento com modelo treinado nas mesmas áreas |
| Estudo culturas Sudeste brasileiro (Landsat) | Amendoim, soja, mandioca, cana, outros | B | https://www.mdpi.com/2072-4292/7/11/14482 | 177 observações campo + 500 interpretadas no treino, 2502 campos interpretados para teste do autor: não reaproveitar a acurácia |
| Conab mapeamento agrícola | Arroz irrigado, café, cana, soja, lavouras 1ª/2ª safra | C/B condicionado | https://www.gov.br/pt-br/servicos/obter-informacoes-sobre-mapeamento-das-areas-agricolas | Polígonos oficiais não significam observações primárias de campo; auditar método |
| MapBiomas Agricultura + LAPIG/UFG | Temporária, perene, silvicultura agrupadas | B/C | https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/agricultura/uso-agricola/ | Validação agregada; não comprova espécie/cultura individual |
| MapBiomas pontos de validação | Uso e cobertura do Brasil | B | https://brasil.mapbiomas.org/downloads/pontos-de-validacao/ | Interpretados por Landsat; checar independência e classes disponíveis |
| IFN/SFB Uso da terra por subparcela | Nativa, plantada, antropizada | A | https://dados.florestal.gov.br/pt_BR/dataset | Dado de campo; verificar precisão local, data e geometrias publicadas |
| IFN/SFB vegetação exótica | Exóticas; possível suporte pinus/eucalipto | A | https://dados.florestal.gov.br/ | Determinar rótulo botânico e se exótica = efetiva silvicultura; não inferir só da espécie |
| Expedição Silvicultura Embrapa (2025) | Eucalipto/pinus, 13 estados, 446 parcelas | A condicionado | https://www.embrapa.br/en/busca-de-noticias/-/noticia/149106379/expedicao-silvicultura-revela-produtividade-florestal-e-concentracao-da-expansao-em-mato-grosso-do-sul | Solicitar parcelas/espécie/coordenadas/licenças; notícia não traz dataset de validação diretamente |
| Inventário florestal MG | Eucalipto e pinus | B condicionado | https://sindifer.com.br/links/SINDIFER%20-Forest%20Iventory%20MG_COP28.pdf | Matriz do OUTRO classificador; exigir amostras/predições independentes do Enform |
| Trazo/WRI limites agrícolas 2023–24 | Contornos de talhões, soja predominante | C | https://source.coop/wri-data-lab/trazofields | >10,9 M contornos derivados de Sentinel-2; coluna mbmode deriva do MapBiomas, não verdade de campo |
| Trazo anotações de contorno | 46.908 limites anotados, 7.453 de teste | B para limite, não cultura | https://wri.github.io/trazo/landing/ | Valida segmentação de talhão, não espécie/cultura |
| GloCAB limites agrícolas | 190.832 polígonos manuais multinacionais inclusive Brasil | B para limite, não cultura | https://zenodo.org/records/10479122 | Classes específicas não presumidas |
| SAFmaps Unicamp | Cana e áreas de cadeia produtiva | C/D | https://doi.org/10.17632/dp4y36fjw5.2 | Base georreferenciada; verificar origem e granulação |
| AGROSTAC | Observações agronômicas harmonizadas | A condicionado | https://zenodo.org/records/15040405 | Conferir arquivos brasileiros, acesso e metadados |
| LAI4EO | Altura/estrutura indireta por LAI, fenologia BBCH, culturas | D | https://lai4eo.github.io/ | Não fornece necessariamente rótulos no Brasil; dado auxiliar e não prova de cultura |
| CROPGRIDS / CropAtlas | Áreas agrícolas globais por cultura | D | https://doi.org/10.1038/s41597-024-03247-7 | Escala grosseira; nunca referência pixel a pixel |
| Open Forest Observatory | Parcelas florestais e drones | A condicionado | https://zenodo.org/records/22731179 | Filtrar país e plantada/nativa, checar licença por item |
| PEVS/IBGE, SFB área de plantios | Área estadual e tipo eucalipto/pinus | D | https://snif.florestal.gov.br/images/pdf/publicacoes/FloBR_2024.pdf | Consistência agregada, não validação de pixel |

**Prioridades imediatas:** 1. baixar e auditar Goiatuba; 2. filtrar INPE-LEM/JECAM/CropHarvest no WorldCereal; 3. inspecionar arroz SC; 4. verificar IFN uso da terra e espécies exóticas por subparcela; 5. solicitar dados primários da Expedição Silvicultura. Para milho, soja, sorgo, café, cana, arroz, feijão, citros, eucalipto, pinus, registrar n por classe, bioma, região, ano, origem do dado, geometria e status de independência.

**Critério científico:** sem pesos SAR realmente executados em datas compatíveis e sem referências independentes não há métrica de validação atribuível ao Enform. Manter classificações incertas como não determinadas, sem carbono nativo.
