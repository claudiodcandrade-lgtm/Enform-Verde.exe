# V87.79 - Enform Verde 3.26.11-PRECAMPO-EXPERIMENTAL - 10/11/2026
## SINOP_FAZENDA_MARIA_EDUARDA - regressao operacional observada
- AOI 1459,91 ha, EPSG:6933; no Windows 3.26.10 o mapa optico nao abriu, 12 cenas SAR candidatas produziram 0 cenas legiveis, 24 tentativas VV/VH falharam, cobertura nativa e cultivada N/D e carbono N/D. Nao interpretar N/D como 0.
- Diagnostico: UnicodeDecodeError, token SAS de colecao expirado/indisponivel e GDAL RasterioIOError; token de colecao nao prova acesso aos pixels.
## Correcoes incorporadas em 3.26.11
- Novo acesso Sentinel-1 MPC por assinatura individual do ativo usando endpoint oficial; token global indisponivel nao bloqueia automaticamente a triagem atual nem o classificador SAR anual.
- O mosaico Esri World Imagery oferece opcao optica visual final apos CBERS-4A, Sentinel-2 Earth Search, Sentinel-2 MPC e NASA VIIRS, antes do mapa cartografico IBGE. Data e sensor do mosaico Esri sao N/D. Fundo optico NAO interfere na classificacao SAR.
- Os testes de GUI e regressao foram alinhados ao titulo plural Fitofisionomias presentes na propriedade e as contingencias opticas; o programa nao deve reportar outros usos 0,00 ha quando o conhecimento da cobertura e N/D.
- Empacotar RF SAR brasileiro experimental com modelo, manifesto e integridade; nao confundir o diretorio de modelos opcionais do usuario com o modelo embutido. Nao confundir classificacao SAR retrospectiva do ano agricola 2025/26 com a cobertura atual de novembro de 2026.
## Gates tecnicos independentes
- Prova de cena SAR real em janela de Sinop e processamento ESA BIOMASS FH nao substituem o teste de KML completo, leitura dos pixels no Windows, carregamento da imagem optica no canvas, areas exclusivamente classificadas e quantificacao cientificamente apropriada do carbono nativo.
- Testes de previsao rapidos e de assinatura SAR podem passar enquanto a homologacao cientifica nacional permanece reprovada. Nao criar observacoes, incertezas nem estimativas de carbono para ocultar falhas tecnicas.
- Atualizar o prompt historico, a especificacao de solos/PronaSolos, o Word completo e as notas de release; publicar ZIP 3.26.11 somente se os controles de compilacao, verificacao de modulos, acesso a pixels e self-test do EXE no SHA exato forem aprovados.
