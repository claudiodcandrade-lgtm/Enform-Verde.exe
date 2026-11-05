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


## ADENDO V87.15 — ESTOQUE MÍNIMO, MAIS PROVÁVEL E MÁXIMO NO EXCEL
O valor mais provável permanece a estimativa pontual por compartimento e interseção IBGE × cobertura. As fontes de incerteza são específicas: limites de massa/carbono inventarial, AGB quando reportada e o envelope oficial de carbono do solo pareado em 0–100 cm. A rotina de cenários `carbon_scenario_envelopes.scenario_envelope` calcula intervalos por fitofisionomia × compartimento e faz somas aritméticas apenas de limites rastreáveis. Para posicionar o centro no ponto médio, aplica `delta=min(central,max(central-low,high-central))` e divulga `central±delta`, não negativo. A faixa assim transformada é representativa de sensibilidade e NÃO um IC95% nem prova de cobertura. A fonte original deve continuar acessível no log. É vedada a criação de percentuais de erro arbitrários por falta de observações. Quando faltar limite de qualquer estoque conhecido, cenários total mínimo e máximo N/D; quando faltar algum compartimento, estoque integral permanece PARCIAL mesmo que haja cenários para os conhecidos. Informações quantitativas do Excel aparecem em tC/ha, tCO₂e/ha, tC e tCO₂e, com áreas compatíveis EPSG:6933, formato pt-BR 2 casas e células adaptativas. CI e compilação do SHA final continuam mandatórios; gate de validação científica independente distinto.


## ADENDO V87.16 — ENVELOPE OFICIAL DE SOLO, SERAPILHEIRA E GATE DE NECROMASSA
Esta nota reafirma os limites científicos da versão 3.26.2-PRECAMPO-EXPERIMENTAL. Carbono do solo 0–100 cm: usar os **limites oficiais de produto** da Embrapa quando obtidos e validados nas cinco profundidades 0–5, 5–15, 15–30, 30–60 e 60–100 cm. Propagar por pixels pareados e pesos de área EPSG:6933. A soma de envelopes marginais é uma faixa oficial de sensibilidade, não IC95% conjunto; um intervalo estatístico exigiria natureza do erro publicado, dependência/covariância horizontal e vertical verificadas e metodologia de propagação explícita. A propagação deve separar a estimativa mais provável central, intervalo marginal e cenário simétrico visual. Não substituir ausência de produto por DP espacial dos pixels.

Serapilheira: distinguir estoque seco observado de deposição anual e espessura IFN. Se houver n quadrantes independentes, SD e fração de C auditáveis, calcular erro-padrão, IC t e carbono estimado por fitofisionomia estritamente compatível. A incerteza da média da área de estudo não representa automaticamente erro de extrapolação ao imóvel; quando faltar erro validado de transferência manter resultado apenas como experimental separado. Para imóvel em AM -58,795°, -2,684°, não importar valores de parcelas geocercadas do Tapajós, Chaves-PA, Nhecolândia. Necromassa IFN agregada sem identidade de classe, sem massa compatível/erro de transferência ou com risco de sobreposição entre material em pé e caído permanece N/D fora do estoque conhecido.

Excel: painel inicial com cenários mínimo/central/máximo em tCO₂e/ha e tCO₂e nas áreas realmente quantificadas, por componente e área nativa; estimativas não quantificadas não são zero, e o total completo permanece parcial. Cenários simétricos têm como centro a estimativa mais provável, mas não substituem intervalos assimétricos originais nem constituem IC95% conjunto. Não afirmar que os erros/intervalos estão completos quando a origem não oferece dados suficientes. Documentação V87.16 registra requisito científico e status de implementação; sua incorporação ao código deve ser verificada em testes e build Windows específicos antes da liberação do piloto.


## ADENDO V87.17 — CORREÇÃO DE FIXTURE ESPACIAL CAR/KML
O Dashboard run 42066584298 chegou a 941 testes e falhou apenas no test_basemap_failure_does_not_block_ibge_setup porque o objeto simulado do geom_metrics não incluía area_utm_ha após a migração do relatório para EPSG:6933 como área de referência. Corrigida a fixture no commit 6e62355e08f9a5745ec48bf9da52f1fa2cfa0735, preservando o aplicativo. O recurso EPSG:6933 permanece como base para estoque e percentuais; a área UTM é estritamente informativa. Nova distribuição requer novamente workflow completo de regressão e EXE empacotado e testado no SHA correspondente. A aprovação científica independente não decorre do ajuste da fixture.


## ADENDO V87.18 — TESTE AOI SINOP, SAR REAL E EXCEL
Teste reportado: 1.459,91 ha; vegetação nativa MapBiomas 917,81 ha; soja anual MapBiomas 535,73 ha; cultivadas sem cultura 4,98 ha; pasto 1,39 ha; SAR atual falhou com "Not enough actual VV/VH raster pixels were accessible"; vigor falhou com UnicodeDecodeError ao acessar dado binário remoto. Portanto não declarar culturas nem floresta atuais identificadas VIA SAR. Código da nova revisão implementa leitura limitada de janelas de COG reais nas rotas recent_sar_landcover e crop_vigor_auto, rastreio de número de pares e erros por cena, TLS habilitado. Essas alterações NÃO significam que pixels reais serão acessíveis em toda AOI; testar efetivamente na propriedade depois da compilação.

Rota WCS Embrapa para fertilidade permanece preferencial. Nova alternativa ArcGIS MapServer Identify aceita estritamente valores numéricos oficiais por ponto, com status MAPA_PREDITIVO_AMOSTRAL, recusando pixels RGB e sem permitir cobertura/IC95% inventados. Somente CTC/pH/CE/textura/carbono teor quando camada publicada; ausência V%, nutrientes. Carbono SOC 0–100 permanece inalterado.

Aba Carbono por Formação acrescenta tCO₂e/ha e estoque tCO₂e sobre área quantificada. Três cenários de carbono mínimo, mais provável e máximo passam às linhas superiores do Painel Executivo e preservam situação N/D quando qualquer fonte conhecida não tiver erro fundamentado. Outras células devem autoajustar altura e largura, com ponto de milhar e vírgula decimal no Excel pt-BR e duas casas. Estoque de serrapilheira só entra na soma após massa seca gravimétrica e extrapolação compatível; IFN espessura somente não basta; necromassa IFN incompatível permanece fora.

A revisão V87.18 exige regressões completas e ZIP do SHA do código; gate científico independente ainda não homologado.


## ADENDO V87.19 — RECORRÊNCIA DE FALHA SENTINEL-2; ROTA OPERACIONAL REVISADA
Na AOI da propriedade, a imagem Sentinel-2 falhou novamente, apesar dos catálogos alternativos. A busca STAC Earth Search (Sentinel-2 L2A) deve tentar até oito cenas candidatas em vez de tratar uma cena retornada pelo catálogo como válida. Rejeitar ausência de bandas red/green/blue, CRS ausente, janela sem interseção, imagem sem pixels RGB válidos e erro HTTP/COG por cena. Não confundir raster de 10 m com amostragem de visualização redimensionada (não altera resolução original). Para bandas em grades distintas, obter janela de fonte por banda, projetar para grid comum e aplicar controle da mesma geometria poligonal sobre o bitmap final. Aceitar somente imagens com pixels observados; raster vazio obriga fallback explícito. Visualização não substitui identificação SAR das culturas ou nativas. A rota Earth Search continua sem chave de API; Google só com chave fornecida pelo operador. Manter fontes externas verificáveis e status N/D quando inacessíveis. Testes: c5ca3601; código: 50b2841d. Não chamar implementação de homologação/validação operacional antes do teste Windows e acesso real às cenas.
