# Enform Verde 3.26.20-PRECAMPO-EXPERIMENTAL

## Correções incluídas

- Corrigida a composição do bundle de certificados TLS: o caminho de certificados do sistema não é mais descartado por conter a sequência `certifi` no nome do diretório. A verificação TLS continua ativa para Requests e GDAL.
- Corrigida a sobreposição dos contornos da AOI quando o KML contém coordenadas 3D (longitude, latitude e altitude), removendo a altitude apenas para desenho cartográfico em CBERS-4A/WFI e NASA GIBS.
- Acrescentado fallback de download HTTPS com cache e validação GeoTIFF para o recorte MapBiomas quando o build Windows não consegue abrir `/vsicurl/`. O resultado permanece referência histórica e só pode ser usado após o esgotamento auditado das rotas SAR.
- Fixada a dependência do classificador em `scikit-learn==1.8.0`, a mesma versão de serialização do modelo. O manifesto declara essa versão e o carregador bloqueia runtime divergente antes de desserializar.

## Evidências locais

- Suíte completa: 1.083 testes aprovados, 1 ignorado, no runtime alinhado scikit-learn 1.8.0.
- Coleta/importação: 157 módulos inspecionados.
- Testes direcionados de TLS, coordenadas 3D, MapBiomas e paridade do modelo: 12 aprovados.
- No KML completo da Fazenda Maria Eduarda, uma chamada direta do LEM+ leu 2.278 pixels válidos em 30 aquisições e produziu uma classificação sazonal experimental para 1.457,92 ha; 1,99 ha permaneceram sem classe. Isso prova leitura/processamento nessa chamada e não valida a renderização no dashboard, a acurácia em campo nem o carbono.

## Limites

- A imagem óptica para a geometria completa da fazenda ainda não foi revalidada após a correção do contorno 3D.
- A classificação SAR sazonal na versão compatível do modelo foi repetida diretamente no KML completo, mas ainda não foi confirmada na integração do dashboard.
- O painel integral do aplicativo para essa AOI, a altura de dossel e a estimativa de carbono continuam sem comprovação de ponta a ponta. Pixels de classificação sazonal não equivalem a pixels de altura/biomassa.
- A verificação visual local não rodou por falta de display. Build Windows/EXE ainda não executado. O produto permanece experimental e não homologado.

- O primeiro CI live detectou um segundo instalador de dependências que ainda usava scikit-learn 1.9.1. A classificação foi corretamente bloqueada antes da predição. Os workflows live e dashboard agora fixam 1.8.0; um teste de contrato impede divergência futura. A prova desses workflows deve ser refeita no novo commit.


## V88.07 — resultado SAR real e regressão integral (12/11/2026)

- No SHA `41d6b14bac637800e4dcdc21ea4ff5b0653919e4`, o workflow SAR #144 passou com 1.692 pixels Sentinel-1 RTC válidos em 3 cenas e runtime scikit-learn 1.8.0. A geometria foi uma caixa fixa perto do centroide, não o KML da fazenda: 1.084,73 ha da caixa; área vetorial classificada de 1.079,26 ha e 5,47 ha sem classe dentro da caixa. Nenhum desses números se refere à cobertura da propriedade. Safra 2025/2026, experimental, não validada em campo, sem transferência à propriedade. Artefato ID `13949044333`, SHA-256 ZIP `9293e9c9af5a87a08192d89a80a9b7d186f5112eeb2532b950fd4a3294492bae`.
- O workflow dashboard #3390 passou 1.084 testes (147,606 s), compilação integral e sincronização documental. O contrato rápido passou. O gate científico continua reprovado; não houve comprovação GUI/end-to-end, leitura óptica na geometria real, altura ou carbono.


## V88.08 — escopo de amostras explicitado nos relatórios (12/11/2026)

- Corrigida a interpretação do registro V88.07: o teste Sentinel-1 foi feito numa caixa fixa próxima ao centroide, não no KML da fazenda. A checagem de altura ESA MAAP foi feita em caixa BBOX, não no limite exato do imóvel. O texto e os nomes de campos distinguem caixa experimental de área da propriedade; novo teste bloqueia os campos ambíguos.
- Os testes em caixa comprovam acesso de pixels reais nas rotas avaliadas, mas não constituem resultados agrícolas, de altura ou carbono da fazenda. Permanecem sem comprovação GUI/end-to-end no KML real, imagem óptica no limite do imóvel, altura/estoques, monitoramento agrícola e validação de campo.


## V88.09 — correção do KeyError no relatório SAR de teste (12/11/2026)

O workflow SAR #147 processou a caixa de teste, mas o relatório falhou ao calcular o saldo não classificado porque uma referência ainda usava a chave antiga `polygon_area_ha`. O cálculo foi centralizado em `summarize_sample_box()` e um teste verifica total, saldo e chaves do escopo. O run #147 é evidência do defeito, não resultado concluído. A correção não processa o KML da fazenda e não prova integração com GUI.

## V88.10 — build experimental e testes Windows ponta a ponta (12/11/2026)

Commit de código testado `cba8b13792a6ae805c8ce4366d64f7ed69a77766`; build Windows #2628/run `43235313158` concluiu `success`. EXE `3.26.20-PRECAMPO-EXPERIMENTAL`, SHA-256 `fc007bc416fdf647e2822f407b8d05e6d3917fecd351cde79e1d51920419fb86`; artefato ZIP ID `13953123396`, 531.891.569 bytes, digest SHA-256 `523ca5aed0cbaf28e5cb732c3722c2eb2c2ee496a9bfe4123e287f1ed71ab1b6`. Autocheck em pasta limpa, `--ui-smoke`, `--module-check`, paridade dos módulos verificados e aceite SAR do KMZ de teste Tapajós passaram. O release público automático foi ignorado; artefato experimental de Actions.

Rotas reais verificadas no build: CBERS-4A/WFI encontrou pixels em 11/11 amostras geográficas do Brasil, cada uma com cobertura de pixels reportada de 100% (limiar do teste 95%, amostras representativas, não prova exaustiva de todo pixel/data); imagem CBERS-4A foi desenhada na tela Tk via fila worker em caixa de teste perto do centroide de Sinop (673×562; status PASS_CBERS), não no KML privado completo. Prévia Sentinel-2 real do KMZ de teste Tapajós passou. O teste SAR Sentinel-1 do KMZ Tapajós e ALOS-PALSAR no Cerrado passaram como testes separados.

O workflow SAR experimental #150 (`43235313209`) terminou com `SAR_EXPERIMENTAL_POLYGONS_OBSERVED`: 1.692 pixels em 30 cenas, mas somente na caixa fixa de teste perto do centroide de Sinop; não representa a Fazenda Maria Eduarda. Safra 2025/2026; campo não validado; transferência à propriedade bloqueada. A rota ESA MAAP FH leu pixels numa caixa BBOX regional, sem perímetro da fazenda; não constitui altura da propriedade. A estimativa de altura/AGB SAR de alta biomassa para Tapajós segue não validada por falta de FH L2B na AOI inventariada.

Dashboard CI #3394: 1.086 testes aprovados, sem falhas; compilação integral e verificação documental passaram. Contrato rápido passou. O gate científico independente continua reprovado. Ainda não há processamento/output confirmado para o KML da Fazenda Maria Eduarda no dashboard: classificação SAR de propriedade, monitoramento de culturas/safra, imagem óptica no polígono exato, altura/estoques de carbono e validação de campo permanecem pendentes. Não interpretar o build/testes como homologação científica.

# V88.11 — runtime geoespacial disponível e regressão integral (12/11/2026)

## Solução para GeoPandas

- GeoPandas não foi substituído por mock: os testes dependem de operações reais de geometrias, CRS, interseção vetorial e leitura de raster. A solução correta é instalar as dependências declaradas pelo próprio projeto.
- O runtime-base do ambiente não traz o stack geoespacial. Foi criado um diretório temporário isolado e nele foi instalado `requirements_desktop.txt`, sem alterar o Python global nem o ambiente de aplicação.
- Pacotes efetivamente usados: GeoPandas 1.2.0, Shapely 2.2.0, PyProj 3.8.0, Pyogrio 0.13.0, Rasterio 1.5.2, scikit-learn 1.8.0, NumPy 2.5.4 e Pandas 2.3.3. O teste live Sentinel-1 de MPC também concluiu leitura real de VV e VH.
- Os testes offline que ainda permitiam chamadas à contingência radar ou MapBiomas/PAM foram corrigidos para injetar respostas controladas nas rotas externas. Isso remove espera de rede acidental dos fixtures, sem substituir o teste live dedicado.

## Evidência executada

- `PYTHONPATH=/tmp/enform-geo-runtime python -m unittest discover -s tests -v`: 1.085 testes executados, todos aprovados, um skip.
- O skip único foi `test_application_shell_unchanged`, pois não havia servidor gráfico/display (`$DISPLAY`). Os outros três contratos visuais estáticos passaram.
- O teste `test_current_mpc_scene_decodes_real_vv_and_vh_pixels` passou, confirmando nesta execução consulta de cena MPC e leitura de pixels VV/VH reais na área de teste de Sinop. Isso não substitui o smoke visual do EXE no KML integral.
- `python -m compileall -q -x '(\\.git|build|dist)' .` e `git diff --check` passaram.

## Instalação reproduzível

Linux/macOS: criar um `venv`, ativá-lo e executar `python -m pip install -r requirements_desktop.txt`; depois executar `python -m unittest discover -s tests -v`. No Windows, usar `py -3.12 -m venv .venv`, ativar `.venv\\Scripts\\Activate.ps1` e executar os mesmos comandos `pip` e `unittest`. Em instalações Conda, preferir instalar GeoPandas e dependências geoespaciais do canal conda-forge de forma consistente, sem misturar canais.

## Estado das pendências

A falta de GeoPandas no runtime foi resolvida para esta validação e a suíte completa passou. Continuam pendentes gates diferentes: build/GUI Windows no SHA atual, smoke ponta a ponta no KML integral da Fazenda Maria Eduarda, leitura óptica nessa geometria e homologação científica. O único skip local é a captura visual Tk por ausência de display; a evidência visual deve vir de Windows CI ou de sessão gráfica com baseline.
