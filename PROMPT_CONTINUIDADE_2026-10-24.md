# PROMPT DE CONTINUIDADE — ENFORM VERDE
Atualizado em 24/10/2026

## Contexto e objetivo
Retomar o desenvolvimento real do Enform Verde no repositório claudiodcandrade-lgtm/Enform-Verde.exe, branch `feature/agricultural-identification-native-carbon`, PR #50. Preservar funcionalidades já operacionais e concluir rotas efetivas, com testes e incerteza cientificamente defensável. Não confundir catálogos de artigos, regras isoladas ou testes unitários com modelos orbitais treinados e integrados. Não anunciar EXE sem artefato Windows verificado.

## Requisitos permanentes
- Aplicativo Windows autônomo; importar SHP, GPKG, GeoJSON, KML e KMZ; mapa raster IBGE offline com municípios, estados, hidrografia e infraestrutura; zoom, scroll, polígono semitransparente, área em hectares; separadores brasileiros.
- Cobrir Amazônia, Cerrado, Mata Atlântica, Caatinga e Pantanal; classificar fitofisionomias por evidências confiáveis, usando IBGE `legenda_1` e MapBiomas quando apropriado, sempre com fonte.
- Prioridade absoluta para AGB derivada de SAR: ESA BIOMASS P, ALOS/PALSAR L, SAR X, Sentinel-1 C, e ESA CCI Biomass v7 como fallback documentado. Não apresentar estatística regional como estimativa SAR pixel a pixel. Altura RH98 de GTDX não entra diretamente em modelo H100 sem conversão validada.
- Estimar, quando houver suporte científico, AGB, raízes, necromassa, serrapilheira e carbono do solo; priorizar inventários microrregionais, IFN/SFB, SINAFLOR e Embrapa Solos. Informar limites quando faltar estimativa defensável. Preservar tC e tCO2e e não confundir OPEX, CAPEX ou outros parâmetros financeiros com carbono.
- Identificar lavoura (milho, soja, sorgo, café, cana, arroz, feijão e citros) somente com classificadores validados; caso contrário 'áreas cultivadas'. Preservar 'pastagem' quando segura. MapBiomas silvicultura classe 9 indica floresta plantada, não prova eucalipto ou pinus. Só distinguir gêneros com modelo e validação específicos.
- Mostrar cena e horários como 'horário de aquisição (UTC)' e 'horário de aquisição (UTC -3)', quando de fato disponíveis; verificar metadados antes de informar indisponibilidade.

## Identificação de sistemas integrados
Implementar ILP (lavoura-pecuária), ILF (lavoura-floresta), IPF (pecuária-floresta), ILPF (lavoura-pecuária-floresta). Coocorrência de componentes em uma fazenda não comprova integração de manejo. Distinguir usos adjacentes, rotação sem integração e sistemas verdadeiros. Quando a evidência for parcial, rotular como candidato ou não comprovado, sem falsa certeza.

## Referências científicas a verificar e reproduzir
1. Embrapa Solos/UERJ, U-Net com Sentinel-2 para iLPF: https://www.alice.cnptia.embrapa.br/handle/doc/1178498
2. Embrapa Territorial/UNICAMP, Random Forest para ILP no Maranhão: https://www.alice.cnptia.embrapa.br/handle/doc/1175472
3. Embrapa Agricultura Digital/UNICAMP, IA e imagens para ILP: https://jornal.unicamp.br/noticias/2024/03/20/metodo-alia-inteligencia-artificial-a-imagens-de-satelite-para-mapear-areas-com-integracao-lavoura-pecuaria/
4. Séries PlanetScope e deep learning, Remote Sensing of Environment: https://www.sciencedirect.com/science/article/pii/S0034425723004376
5. Embrapa Pecuária Sudeste, forragem com HLS e clima: https://www.sciencedirect.com/science/article/pii/S0168169925006027
Investigar ainda Embrapa Gado de Corte, Instrumentação, ESALQ, UFV e outras. Para cada método verificar código, pesos, dados, licença, definição das classes, validação espacial/temporal e domínio de transferência. Referência publicada não equivale a pesos operacionais.

## Cadeia de processamento requerida
Aquisição de Sentinel-1, Sentinel-2, Landsat/HLS e outras fontes adequadas -> máscaras e correções -> alinhamento espacial e séries temporais -> inferência com modelos treinados efetivamente disponíveis -> fusão de evidências espacial, espectral e temporal por unidade de manejo -> decisão ILP/ILF/IPF/ILPF ou abstenção -> relatório e mapas com rastreabilidade. Integrar ao desktop_app e pipeline principal. Testar AOIs reais nos cinco biomas; não gerar probabilidades sintéticas.

## Rigor de incerteza
Publicar matriz de confusão, precisão, revocação, F1, amostras independentes, região/ano, modelo e domínio. IC95% Wilson pode expressar precisão binomial quando suas premissas forem atendidas; não é intervalo de confiança de área nem probabilidade por pixel. Para área usar desenho amostral e estimadores adequados com correção de erro de classificação. Evitar pseudorreplicação e explicitar erro de transferência. Se não houver validação, indicar 'incerteza não quantificada', sem inventar RMSE, F1 ou IC.

## Estado real conhecido no GitHub
Repositório: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe
Branch: feature/agricultural-identification-native-carbon
PR: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/pull/50
- 92ea80d: `integrated_system_classifier.py` com decisão conservadora ILF/IPF/ILPF a partir de evidências.
- eee07cc: testes iniciais.
- 173b0d6: inclusão de testes no workflow Windows.
- c446054: intervalo de Wilson para precisão condicional.
- 4be3627: catálogo de referências, marcado não operacional sem pesos/validação.
- 96b6f40: testes de incerteza e bloqueio de modelos não validados.
- 8695cfa: `classify_integrated_batch`, decisão em lote com exportação JSON.
- cd64c6c: testes de lote e abstenção.
O dashboard havia passado em execução anterior, mas a situação dos workflows deve ser consultada novamente. Ainda não está demonstrada inferência orbital U-Net/Random Forest operacional nem integração completa com a interface. Não afirmar o contrário.

## Ordem de execução obrigatória
1. Inspecionar branch, PR, arquivos, workflows e artefatos; identificar regressões.
2. Obter código/pesos/dados e licenças dos modelos científicos; se não disponíveis, reproduzir treinamento com amostras reais, separação espacial e temporal e métricas independentes.
3. Implementar aquisição e pré-processamento de imagens e adaptadores de inferência.
4. Integrar resultados à decisão ILP/ILF/IPF/ILPF e ao mapa/relatório com abstenção.
5. Publicar incertezas compatíveis com o desenho de validação e área.
6. Testar Tapajós, Santo Ambrósio, Brasília e AOIs adicionais em Pantanal/Mata Atlântica/Caatinga, sem misturar fitofisionomias.
7. Rodar CI Windows, corrigir falhas, gerar EXE e disponibilizar link real de artefato verificado.
8. Atualizar este prompt a cada marco e preservar todo avanço anterior.

## Critério de conclusão
Somente concluir quando as rotas estiverem realmente ligadas à aplicação, com evidências rastreáveis, testes passando e artefato Windows verificável. Documentar claramente funcionalidades operacionais, experimentais e indisponíveis.
