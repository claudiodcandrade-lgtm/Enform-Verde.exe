# Revisão V87.10 — liberação técnica verificada 3.26.2

Data: 05/11/2026. Aplicativo: `3.26.2-PRECAMPO-EXPERIMENTAL`. SHA do código e da distribuição: `b4055ebbbfc9394616658c2c215603087dd5a60e`.

## Preview de entorno Sentinel-2
A janela de entorno usa exclusivamente imagem óptica. Earth Search/AWS Sentinel-2 L2A público é a rota automática prioritária sem chave do usuário; depois Planetary Computer, NASA GIBS VIIRS, Esri World Imagery, Esri Street Map e mapa IBGE offline. Google Maps é opcional somente com chave válida fornecida pelo usuário; nenhuma chave é gerada automaticamente. SAR/radar permanece separado e reservado às análises.

As bandas RGB Sentinel-2 B04/B03/B02 têm resolução nominal de 10 m. Leitura COG usa HTTP range limitada à janela AOI/viewport, reamostragem direta ao canvas e até três leitores paralelos independentes. Evita download da cena completa e quadrantes arbitrários. AOIs que cruzam telhas devem processar apenas telhas intersectantes. Não divulgar ganho percentual sem benchmark medido.

## Resultado de integração, regressão e executável
No mesmo SHA `b4055ebbbfc9394616658c2c215603087dd5a60e`:

- dashboard: suíte integral aprovada, 925 testes;
- Windows: build aprovado, incluindo prévia Sentinel-2 real para Tapajós e testes de integração;
- EXE testado em cópia limpa; checksum do executável registrado;
- artefato Windows: `Enform-Verde-Windows-v3.26.2-PRECAMPO-EXPERIMENTAL`;
- SHA-256 do executável: `8af9e7445b77cad603f94877befb510359f7b5564df60a451b57a4f86aa8c1a4`;
- digest SHA-256 do ZIP do artefato: `6aa511d6b5e864d23bec6bcf088f922ca07850a6bc0e3066a97f529492640ab5`.

## Limites científicos
Este marco libera uma compilação técnica experimental para testes. Não representa homologação científica independente. O gate científico permanece não aprovado por ausência de evidências observacionais suficientes; estimativas experimentais devem permanecer identificadas e com incerteza/limitações explícitas.


## REVISÃO V87.11 — CORREÇÃO OPERACIONAL CAR/KML — 05/11/2026
Identificador da aplicação: `3.26.2-PRECAMPO-EXPERIMENTAL`. O erro reportado em propriedade real foi `name 'redraw' is not defined`: ao importar KML testado ou consultar CAR, o perímetro abria, mas `_show_geom` não completava seu fluxo. A rotina `desktop_app.py::_schedule_offline_map_fit` chamava uma variável global inexistente em `self.after(420,redraw)`. Essa linha foi removida no commit `d99634cf29cb6f6b7d4fb951b5654890dcd1e456`; desenho imediato da AOI, busca online e fallback offline já ocorriam sem ela. Com isso, a preparação passa a alcançar inicialização do diagnóstico IBGE e o caminho posterior de análise, sujeito a disponibilidade das fontes. Regressão automática `tests/test_car_kml_map_setup_regression.py` verifica a inexistência do callback solto e o fluxo comum de CAR/vetor. Manter o histórico, as funções de Sentinel-2 e SAR, os seis biomas, carbono 0–100 cm, fertilidade, agricultura e modelos pré-campo. Nova distribuição só pode ser declarada corrigida após testes de integração reais e build Windows verificado no mesmo SHA; não confundir correção de NameError com homologação científica.


## ADENDO V87.12 — FALHA DA REGRESSÃO CORRIGIDA E CRITÉRIO DE ACEITE
O Dashboard dual run 42042610110 apontou SyntaxError no novo teste de CAR/KML por sequências literais de escape na linha de definição de _poll_ibge. Correção publicada no commit 7367eb1db282485e42b8af900df691e223aeccd8. A proteção de _show_geom contra falhas no mapa está no commit 41429e6193356f455cd2707f41a6b4916fcb80fd. Confirmar byte-compile, regressão geral, teste no Windows com CAR e KML, diagnóstico IBGE, execução de análise, saída de relatórios e hashes de ZIP/EXE no SHA final. Até isso ocorrer, a versão corrigida é candidata e não liberada. Sem alteração do gate de homologação científica.


## ADENDO V87.13 — CONTROLE DOCUMENTAL CORRIGIDO, EVIDÊNCIAS E CRITÉRIO FINAL
Data 05/11/2026. Versão 3.26.2-PRECAMPO-EXPERIMENTAL. O build Windows run 42047129950 relativo ao SHA de código 34134031f511f989e5fd1caec9b7d0a24737eda7 concluiu com sucesso: PyInstaller, prévia Sentinel-2, autoteste EXE em diretório limpo, padrão visual e verificação de módulos. Artefato ZIP ID 13427240397, digest SHA-256 dcfbd9b2807777fba70d1bfd27744607e396ede5d82eecb923845eafb914af67. EXE SHA-256 90dd8597952272be6853882d55f8e156e78cfb47dd85b637946c91d8aaf5c29a. O Dashboard dual run 42047130008 realizou os testes mas reprovou no gate documental porque a última correção de teste era posterior aos documentos.

O verificador docs foi corrigido para examinar a sequência de commits entre merge-base e HEAD, encontrando a última alteração efetiva, e exigindo documentação *no mesmo commit ou em commits posteriores*: prompt atual, prompt histórico, especificação de solos e Word diretamente ou via checkpoint versionado com workflow ativo. Não permitir documentos antigos para validar código novo. Os testes incluem atualização posterior válida, documentação anterior inválida, commit exclusivo do bot Word e nova alteração de código que invalida documentação anterior. O workflow Dashboard agora examina o histórico integral do PR, não apenas uma janela eventual. Não reduzir a exigência de documentação nem mascarar regressões. Após esta revisão e antes de distribuir novo SHA, exigir CI técnico concluído e build do EXE com identidade e checksum idênticos.

Preservar sem regressão as correções da análise CAR/KML, a segregação de imagem Sentinel-2 para visualização, o fallback offline IBGE, as estimativas e incertezas por compartimento e o caráter experimental pré-campo. A homologação científica observacional independente permanece separada.


## ADENDO V87.14 — HIERARQUIA IBGE, PLANILHA E FALHAS OPERACIONAIS
Data: 05/11/2026. Área do imóvel KML AM: 27.057,81 ha em projeção equivalente EPSG:6933 (base única de percentuais e estoques); 27.063,48 ha em UTM EPSG:32721, exibidos separadamente apenas para diagnóstico. Região fitoecológica POTENCIAL IBGE: Floresta Ombrófila Densa, código D, 27.057,81 ha. Tipos da legenda_2 subordinados: Terras Baixas 26.749,44 ha e Aluvial 308,37 ha. A interseção anual MapBiomas+IBGE de 27.050,00 ha representa cobertura cartográfica, não campo; 7,81 ha de diferença exigem identificação por classe, não presunção de floresta nem arredondamento para zero.

Correções de interface: processamento de respostas obsoletas da fila do mapa não interrompe a espera pelo resultado da geração corrente; prioridade Sentinel-2 aberta, alternativas Planetary Computer/NASA/Esri/IBGE offline, sem impedir a análise. As quebras de linha literais exibidas como barra invertida+n foram corrigidas no relatório IBGE.

Pedologia: recuperação no FeatureServer oficial ou MapServer da mesma cartografia Embrapa 1:5 milhões, interseção exclusiva EPSG:6933 e indicação de classes/unidades de mapeamento; áreas de associações não são áreas dos componentes individuais. Fertilidade: estatísticas 90 m apenas quando dados WCS numéricos reais da Embrapa estiverem acessíveis, com fonte, cobertura e incerteza. Quando sem WCS, N/D com justificativa, nunca inventar CTC ou V% e nutrientes.

Serapilheira: não atribuir estoque da referência Tapajós, Nhecolândia ou Santo Ambrósio ao imóvel AM (-58,795°, -2,684°) que não atende aos geofences de extrapolação. Valor não quantificado = N/D, nunca zero; o total permanece parcial. Estimativas experimentais requerem fonte de massa seca da mesma fitofisionomia e propagação defensável do erro de transferência.

Excel: primeira aba PAINEL EXECUTIVO incluindo geométrica, bioma, fitofisionomia, cobertura, carbono por compartimento e tCO2e por hectare e área quantificada, pedologia, fertilidade e uso do solo. Aba Totais tCO2e com total conhecido em tC, tCO2e, densidade na área nativa e situação de completude. Não multiplicar densidade da área nativa pelo total da AOI. A formatação numérica de TODAS as abas usa padrão Excel #,##0.00 interpretado pela localidade brasileira com duas casas decimais e agrupamento de milhares, células com largura automática, quebra de texto e altura aumentada para legibilidade. O novo teste de contrato valida os elementos principais. Preservar modelos científicos e estados experimentais. Gate independente de campo continua pendente e não é substituído por testes de contrato.
