# Continuidade — Enform Verde SAR — 23/10/2026 — v15 — uso do solo / confiança

## Nova instrução autorizada e prioritária

Pesquisar e incorporar classificação SAR de fitofisionomias e usos agropecuários. Instituições brasileiras reconhecidas têm prioridade para vegetação nativa. Para milho, soja, sorgo e outras culturas anuais; pastagens plantadas; perenes, especialmente café e citros; e florestas plantadas, podem ser usados métodos publicados por instituições reconhecidas de qualquer país.

**Confiança mensurável é requisito básico e inegociável.** Ordem confirmada pelas mensagens mais recentes: **SAR com confiança demonstrada → IBGE → MapBiomas**. Sem evidência suficiente, não substituir mapas de referência. Medir interseção espacial com a AOI e apresentar hectares e percentual para cada classe, sem dupla contagem. Não confundir legenda do classificador, IBGE e MapBiomas.

## Estado desta implementação

Base confirmada ao vivo: PR #48 aberto/não mesclado; HEAD d373c52b34a89e43a9386e5f27a96cb6713e71dc; Run #505 success, artifact 12527471150, 515.707.507 bytes, SHA-256 5bc957b4e255a398775ec07921004b6a49aa29228474f6c38628156a14f0180d.

Nova candidata de código: 3.24.39. Consultar HEAD/Actions ao vivo antes de dizer que há EXE pronto. Este prompt é escrito junto do código, antes da nova compilação Windows. Nenhum artifact 3.24.39 está comprovado neste texto. Não excluir ou substituir artifacts existentes; não mesclar nem fechar PR #48.

- `land_use_sar.py`: RF adaptado de família metodológica publicada; calibração logística multiclasse separada; validação espacial independente; matriz de confusão, precisão/recall/F1, Brier e ECE; IC95% Wilson da precisão por classe aceita. Três splits train/calibration/validation e referência única por unidade; separação espacial mínima de 1 km é triagem, não prova de independência/representatividade.
- Política operacional fixa: probabilidade calibrada ≥0,90; ≥50 referências independentes aceitas por classe; limite inferior IC95% precisão ≥0,90. Esses números são critérios conservadores de implementação, não resultados dos artigos. Intervalos são condicionados a desenho de validação defensável; não provam confiança de cada pixel nem IC de área.
- Quando o cultivo não é elegível, permite grupo pai agropecuário apenas se tiver validação própria elegível. Caso contrário, IBGE/MapBiomas. Rejeita AOI fora do domínio, sensor/processamento/período incompatíveis, extrapolação dos atributos e pseudorrótulos cartográficos declarados como validação.
- Referências reais e atributos SAR compatíveis devem ser fornecidos no contrato JSON. Não há pesos nacionais validados embutidos. A presença de um artigo no catálogo não o torna executável. Métodos DL, SVM e full-pol catalogados não foram implementados nesta alteração.
- Interface: configuração de classificação e botão independente de AGB; classificação também integrada ao fluxo geral; camada IBGE oficial obtida da rota/cache existente quando não selecionada manualmente. Relatório, Excel, GeoJSON de interseções, GeoTIFF de classes/confiança e JSON de auditoria.
- A distribuição original de cada fonte fica preservada na auditoria, mesmo quando sobreposta por fonte prioritária. AOI inteira como denominador, nodata como lacuna explícita, recorte de células na borda, EPSG:6933 para área equivalente. EPSG:5880 é policônica, não deve ser descrita como equivalente.
- `mapbiomas_zonal.py`: corrigida área por pixel, dividindo área geodésica da linha pela quantidade de colunas. Teste novo com GeoTIFF real local detecta a multiplicação anterior pela largura.
- Testes locais: 85 passaram antes do commit; incluem 10 testes novos de classificação com dados **sintéticos**, apenas verificação computacional. Não são validação científica em Santo Ambrósio/Tapajós.
- Pesquisa/contrato/limitações: `docs/CLASSIFICACAO_SAR_USO_SOLO.md`; fontes Embrapa, INPE, UnB, UFSM, ITA, Twente e métodos globais para café, citros, cereais, forrageiras e plantações.
- Não foi validada aquisição automática de séries de classificação, nem pesos/modelos reais nas AOIs. O módulo usa GeoTIFF de atributos e referências institucionais reais fornecidos; as rotas existentes de AGB não criam esse contrato automaticamente.
- A nova partição não altera modelos de carbono existentes. Estratificar carbono por ela exige integração explícita posterior com modelos compatíveis para cada classe. Preservar os avanços de AGB/altura, solo, necromassa, serapilheira, UI e exportações.

## Próxima verificação

Conferir novo HEAD, CI Windows, teste de EXE em cópia limpa e nome/ID/tamanho/hash do artifact 3.24.39. Se houver falha, corrigir somente causa demonstrada. Antes de habilitar prioridade SAR em dados reais, recuperar referências geográficas independentes e atributos pareados com domínio/época/sensor corretos; aplicar o contrato e auditar representatividade. Não transformar testes sintéticos ou acurácia global publicada em erro local conhecido.

---
## Registro anterior preservado integralmente (v14)

# Prompt de continuidade — Enform Verde SAR — 23/10/2026 (v14)

Retome o trabalho no repositório `claudiodcandrade-lgtm/Enform-Verde.exe`, PR **#48**, branch `sar-agb-height-integration-v3.24.22`. O PR deve permanecer aberto: **não faça merge**. Confirme ao vivo HEAD, Actions e artifacts antes de declarar uma versão concluída.

## Estado atual confirmado em 23/10/2026

- PR #48 está aberto, não mesclado. Título: “Enform Verde 3.24.38 — fallback Pantanal/Nhecolândia”.
- HEAD da branch: `d373c52b34a89e43a9386e5f27a96cb6713e71dc`.
- Commits da versão: `747a9de` (fallback Pantanal/Nhecolândia), `5ebe722` (integração na interface e versão 3.24.38), `21ed29a` (testes da função), `a19df40` (upload do diagnóstico H100 passa a não bloquear o restante da CI), `d373c52` (corrige apenas os rótulos do pacote e artifact para 3.24.38; nenhuma lógica do aplicativo foi alterada).
- Run #503 (`40004376430`) falhou ao enviar o diagnóstico H100 porque o armazenamento de artifacts do GitHub Actions atingiu a cota. Os testes posteriores foram pulados; esse run não valida o código.
- Run #504 (`40005082306`) no HEAD `a19df40`: tentativa 1 passou em gates/testes, compilação e teste do EXE em cópia limpa, mas o upload falhou por cota; tentativa 2 falhou no gate público ALOS/PALSAR do Cerrado por falta de polarização HV; tentativa 3 passou e armazenou um pacote de código 3.24.38, porém com rótulo antigo `Enform-Verde-Windows-v3.24.37-CANDIDATE`, ID `12525774450`, 515.708.260 bytes, SHA-256 `91930586672b756f708c3fcb012856b7bfb16b43ce27ee49eafc160ed1b1b0c1`. O erro de rótulo foi corrigido em `d373c52` sem alterar o aplicativo.
- Run #505 (`40011699767`), commit `d373c52b34a89e43a9386e5f27a96cb6713e71dc`, concluiu com `success` na tentativa 1 em 23/10/2026. Gates, testes científicos, build Windows, teste do EXE em cópia limpa e upload passaram. Artifact correto: `Enform-Verde-Windows-v3.24.38-CANDIDATE`, ID `12527471150`, 515.707.507 bytes, SHA-256 `5bc957b4e255a398775ec07921004b6a49aa29228474f6c38628156a14f0180d`. Download pela página do run: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40011699767
- Artifact anterior mantido para histórico: Run #500, `Enform-Verde-Windows-v3.24.37-CANDIDATE`, ID `11446067068`, SHA-256 `bb72eac17ca5b291863ff4a5fa6ded254d2c75e04a0816a26f1336c28f0c6e3c`, 515.473.687 bytes: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/37534230278
- Com autorização explícita do usuário, foram excluídos somente os dois artifacts duplicados 3.24.36: Run #499, ID `11446336529`, 515.472.245 bytes; Run #498, ID `11446341169`, 515.474.577 bytes. Preservados: artifact correto 3.24.38 do Run #505; pacote 3.24.38 com rótulo antigo no Run #504; versão 3.24.37 do Run #500; diagnósticos Tapajós IDs `12525113813` (tentativa 2 do Run #504), `12525942532` (tentativa 3 do Run #504) e `12526353069` (Run #505), 357 bytes cada. Não excluir mais artifacts sem nova autorização.
- O Run #500 passou gates, build/runtime/cópia limpa e upload; isso não comprova validade científica para todas as AOIs. Diagnóstico H100 Tapajós #500 foi `BLOCKED_DATA_COVERAGE`, pois não encontrou GeoTIFFs no prefixo consultado. Tapajós H100/AGB SAR continuam sem validação comprovada.
- Este v14 substitui o v13 e registra o estado final do Run #505. PR #48 segue aberto e não mesclado; confirmar online novamente antes de qualquer nova publicação.

## Alteração em implementação na 3.24.38

- `carbon_compartments.py`: nova função `pantanal_nhecolandia_litter_carbon_component`; combina massa seca pontual da tese UFMS Nunes (2015) com frações de C medidas por Nascimento et al. (2024), convertendo kg/m² em Mg matéria seca/ha (×10) e depois em Mg C/ha.
- A integração ocorre depois das referências locais geocercadas de Santo Ambrósio e Tapajós. A nova referência só é acionada se ainda não houver serapilheira regional compatível, se o bioma indicar Pantanal e toda a borda da AOI ficar no raio de 35 km de Nhumirim/Nhecolândia.
- Estimativa seca codificada: 2,870784 Mg C/ha; IC95% amostral aproximado por delta method/t (gl=12): 2,484530–3,257038 Mg C/ha. Estoque seco Nunes: cordilheiras n=26, 0,6675769 kg/m² (SE 0,03732); capões n=13, 0,3436923 kg/m² (SE 0,07520). Frações C: CORD.N 52,2% (DP 1,6 p.p., n=36), CAP 47,8% (DP 3,1 p.p., n=20). Pesos da mistura seguem a alocação amostral Nunes, não proporções de habitat medidas dentro da AOI.
- O intervalo computa erro amostral entre pontos e frações C; **não** quantifica erro de transferência espacial/ecológica, composição de habitats, nem erro de equivalência cordilheira↔CORD.N/capão↔CAP. O próprio método/status mostram essa limitação. Não chamar isso de erro total conhecido ou estimativa medida na AOI.
- Teste novo em `tests/test_carbon_compartments.py` verifica valor, intervalo, sinalização do erro de transferência e rejeição fora do geofence. Passou no Run #505 junto com todos os gates, build Windows, teste do EXE em cópia limpa e upload; o pacote correto 3.24.38 está disponível no artifact informado acima.

## Achado confirmado no estudo de serapilheira do Pantanal (Nascimento et al., 2024)

- Fonte primária: https://doi.org/10.1590/0001-3765202420240709 (texto integral SciELO: https://www.scielo.br/j/aabc/a/7mgjqYQTMMV55n8q6jnJrNd/?lang=en).
- O estudo delineou parcelas de 10 × 10 m e coletou, em 152 parcelas, serapilheira em triplicata com moldura de 50 × 50 cm. As triplicatas foram homogeneizadas por parcela. O material foi peneirado, seco a 60 °C por 48 h até peso constante e pesado; porém o artigo não publica os pesos secos por parcela/classe nem estoques médios de massa seca por área.
- O artigo publica teor de C (dag/kg, numericamente % da massa seca) com média ± DP para CAP 47,8 ± 3,1; CC 44,7 ± 3,5; CORD.AM 46,6 ± 3,0; CORD.N 52,2 ± 1,6; CORX 47,6 ± 1,8; MUR 53,9 ± 1,4. Isso é concentração de carbono, não estoque tC/ha.
- Só converter para estoque por classe se forem obtidos pesos secos representativos por parcela/unidade (ou média, n e erro publicados) e for possível pareá-los ao teor de C e ao domínio correto. Fórmula: massa seca por área × fração de C; 1 dag/kg = 1%. Propagar a incerteza de massa e de teor de C e preservar as 152 parcelas como unidades independentes; as triplicatas dentro da parcela não são n independente.
- Se os pesos por parcela/classe não forem recuperados em suplemento, tese, repositório ou dados abertos dos autores, não estimar tC/ha com essa fonte. Exibir o teor de C como dado de composição e manter “estoque de serapilheira Pantanal não estimável com esta publicação”; procurar inventário gravimétrico local compatível na hierarquia já definida.
- Os estoques por ponto foram transcritos das tabelas 4, 6 e 8 do Apêndice I (pp. 90, 93 e 96) da tese Nunes (2015). Cada ponto é unidade independente; as quatro subamostras são usadas para obter a medida pontual e não contam como n separado. Os valores sazonais publicados são agregados, mas o código usa as médias/SE dos pontos da estação seca: cordilheiras n=26, 0,6675769 kg/m², SE 0,03732; capões n=13, 0,3436923 kg/m², SE 0,07520.
- A 3.24.38 usa fração de C Nascimento et al. (2024) como transferência entre estudos/habitats: CORD.N para cordilheira e CAP para capão. Os erros amostrais das frações são propagados, mas a equivalência ecológica e a transferência espacial permanecem sem quantificação. O intervalo apresentado é amostral parcial, não erro total da AOI.
- O SFB/IFN agora publica `IFN - Serapilheira por UF` retificado (metadados: https://dados.florestal.gov.br/dataset/ifn-serapilheira-por-uf_disp-set2025). A tabela contém bioma/UF/município/coordenadas/UA/data, uso da terra e `Profundidade` em cm; não publica massa seca/estoque gravimétrico. O portal registra retificação em 24/10/2025 por duplicidades. Não converter profundidade em tC/ha sem calibração gravimétrica pareada. Madeira caída/necromassa IFN tem outros dados, tratados separadamente.

## Objetivo imediato

Corrigir e validar no código do PR a distribuição das classes de cobertura e os compartimentos de carbono para:

1. Fazenda Santo Ambrósio — CAR `PA-1502509-F3361AAF86CB40E0AE6E2A8DFA4A8CB5`, Chaves/PA, Ilha Mexiana.
2. Área de aceitação no Tapajós — `acceptance/Teste_SAR_Alta_Biomassa_Tapajos.kml`.

A saída deve mostrar área e percentual por classe, além de estimativas independentes de biomassa viva, serapilheira e necromassa, com fonte, domínio, unidade amostral, n, método, erro e limitação de transferência. Não converter dados anuais de queda de folhas em estoque; não converter profundidade de serapilheira em massa sem calibração gravimétrica pareada; não inferir necromassa por alometria de árvores vivas. Não transferir o valor do Tapajós para Santo Ambrósio.

## MapBiomas e classes espaciais

O usuário determinou usar o mapeamento MapBiomas para completar a cobertura fitofisionômica de Santo Ambrósio e calcular o percentual de ocorrência de cada classe. Implementar para qualquer AOI:

- Calcular hectares e percentual por classe MapBiomas, informando coleção, ano, resolução, fonte, pixels válidos/nodata e método de área. Usar a camada anual mais recente que estiver publicamente disponível e confirmar a versão atual na execução.
- O artefato de trabalho preparatório contém `mapbiomas_zonal.py` e testes; ele **não foi confirmado no HEAD do GitHub**. Inspecione o branch antes de reaproveitar ou substituir arquivos.
- Não chamar classes genéricas do MapBiomas de subclasses IBGE. MapBiomas distingue cobertura/uso em legenda própria (por exemplo, formação florestal, savânica, mangue, floresta alagável e campo alagado); isso não identifica automaticamente FOD Aluvial, FOD Terras Baixas ou outras classes detalhadas.
- Para reportar percentuais de fitofisionomias IBGE, sobrepor os polígonos/classes espaciais IBGE à máscara MapBiomas e calcular área de interseção por classe, documentando o cruzamento e as classes sem correspondência. Reportar também a distribuição MapBiomas original para auditoria. Não preencher lacunas com a classe dominante da propriedade.
- Estratificar os cálculos de carbono por área das classes compatíveis. Usar apenas a máscara florestal para AGB de inventários que amostram árvores florestais com DAP ≥10 cm; excluir formações savânicas/campos alagáveis desses modelos quando não houver suporte validado.

Fonte pública: https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-30m/cobertura/
GeoTIFF C11 usado na preparação: https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection11/lulc/coverage/brazil_coverage/brazil_coverage-col11_2025.tif

## Dados que não podem ser perdidos

### Santo Ambrósio

- Há resumo recuperado de 17 amostras gravimétricas de serapilheira: média 14,3876 t de matéria seca/ha; DP 9,2863; IC95% 9,613–19,162 t/ha. Quadrados de 0,5 × 0,5 m, secagem a 70 °C até peso constante.
- Esse IC quantifica a média amostral sob a hipótese de independência; **não** prova que a amostra representa toda a fazenda ou todas as classes. Localize e confira os dados/fontes primários no branch/arquivos abertos antes de usar. Aplique apenas ao estrato e domínio demonstravelmente compatíveis; registre que o erro de transferência espacial/ecológica não está incluído se não for quantificável.
- O inventário de árvores tem 167 parcelas e 2.144 árvores; média de AGB seca 418,65 Mg/ha, IC preliminar 372,55–464,78, área basal 36,43 m²/ha, altura média 14,96 m, DAP mínimo 10 cm. Parcelas não têm coordenadas individuais. Isso valida somente biomassa viva acima do solo em floresta e não mede solo, raízes, indivíduos com DAP<10 cm, serapilheira ou madeira morta.
- Tratar Santo Ambrósio como várzea estuarina. Classes esperadas a investigar incluem FOD Aluvial e FOD Terras Baixas; não presumir que sejam as únicas antes de calcular a distribuição espacial.

### Necromassa

- A fazenda e o inventário acima não mediram necromassa. Não inventar estoque ou margem de erro.
- Priorizar parcelas abertas georreferenciadas de instituições reconhecidas, na mesma classe e região; depois inventários institucionais totalizados com erro publicado; depois dados oficiais IFN/SFB e Sistema Sinaflor com suporte comprovado; PNLA serve como localizador. Dados privados de licenciamento são último nível e só entram com autorização, margem de erro publicada e compatibilidade ecológica/metodológica.
- Arquivo IFN/SFB agregado por bioma×UF não contém coordenadas nem classe IBGE. Manter fora do total quando a transferência por classe/proximidade não puder ser defendida; não apresentá-lo como estimativa local.
- Necromassa aérea requer medida direta compatível (madeira morta em pé/caída, com protocolo e unidade adequados). Necromassa subterrânea só com raízes mortas medidas diretamente. BGB viva é outro compartimento.

### Tapajós — serapilheira

- Referência publicada de estoque seco de piso florestal: média 4,95 Mg/ha, n=6 parcelas independentes (duas classes de solo interdigitadas, n=3 por classe), a partir dos controles antes do tratamento em abril/1999. IC95% t bilateral reconstruído, gl=5.
- Só selecionar para Amazônia + classe IBGE Floresta Ombrófila Densa e AOI integralmente dentro do limite operacional de 15 km. É benchmark microrregional, não medição da AOI; reportar separadamente erro amostral e incerteza de transferência quando houver dados.
- Não aplicar em Santo Ambrósio ou fora do domínio.

## Suspeita de regressão a validar, ainda não confirmada em CI

Há evidência de que geometrias KML/KMZ podem chegar sem CRS declarado. Chamadas diretas a `.to_crs()` podem falhar e uma exceção tratada pode fazer desaparecer silenciosamente as referências de serapilheira/necromassa. Verificar o leitor real de CAR/KML, normalizar CRS somente quando coordenadas forem reconhecíveis como longitude/latitude, rejeitar coordenadas projetadas sem CRS e adicionar testes de regressão para:

- Polígono de aceitação Tapajós sem CRS e com CRS explícito: referência válida deve aparecer nos dois casos.
- Área Tapajós fora da classe/geofence: nenhuma transferência.
- Santo Ambrósio: saída deve mostrar serapilheira com origem/erro conforme dados locais; necromassa deve mostrar estimativa válida ou “não estimável” com motivo — nunca desaparecer da tabela/relatório.
- MapBiomas deve retornar áreas/percentuais coerentes, excluir nodata do denominador e transformar a geometria para o CRS do raster. Tratar a área de pixel geodesicamente (inclusive quando a projeção do raster não for geográfica).

## Hierarquia de dados e regressões protegidas

Preservar sem enfraquecer:

1. Parcelas abertas georreferenciadas de instituições reconhecidas.
2. Inventários institucionais totalizados com n, unidade e incerteza publicados.
3. Dados oficiais públicos IFN/SFB e Sistema Sinaflor no mesmo nível de origem oficial, desde que sejam inventários medidos e possuam suporte/erro apropriados; registro administrativo sozinho não comprova medição.
4. PNLA como caminho de localização de estudos/licenças.
5. Dados privados de licenciamento por último, somente com autorização, margem de erro publicada e compatibilidade de classe/domínio.

Não parear inventário sem coordenadas de parcela com pixels SAR. O SAR deve processar pixels reais; registrar cena, produto, download/abertura, pixels da AOI, atributos e modelo. AGB numérica só pode ser rotulada como SAR quando sua proveniência for realmente SAR. Preservar resultados de processamento, exportações, UI, geometria/mapa, formato pt-BR, limites de domínio e todos os gates verdes já existentes. Em particular, não reverter a regra que serapilheira exige estoque em massa seca e não produtividade anual.

O Pantanal tem agora referência regional de serapilheira com IC amostral apenas na Nhecolândia (3.24.38, CI #505 aprovado). Não há erro de transferência conhecido por AOI/habitat; fora do geofence, o componente segue não estimado. A AGB Pantanal continua apoiada apenas em parte das classes. A necromassa usa fallback IFN/SFB bioma×UF com intervalo preditivo, mas sem estrato IBGE. Não declarar cobertura científica nacional completa nem que todo erro esteja conhecido.

## Próximas ações obrigatórias ao retomar

1. Conferir ao vivo PR #48, HEAD `d373c52b34a89e43a9386e5f27a96cb6713e71dc`, Run #505 e artifact ID `12527471150` antes de qualquer declaração posterior. No estado confirmado em 23/10/2026, PR aberto/não mesclado e Run #505 `success`.
2. A versão 3.24.38 já foi construída, testada em cópia limpa e armazenada. Não reexecutar nem alterar código sem uma falha ou necessidade nova demonstrada. Preservar tudo que funciona.
3. O commit `d373c52` alterou somente duas strings de release no workflow (`LEIA-ME` e nome do artifact), corrigindo 3.24.37 para 3.24.38; sem alterações funcionais.
4. Persistem limites científicos: o IC da serapilheira Nhecolândia cobre erro amostral, mas não transferência espacial/ecológica; outras classes/AOIs seguem com limitações descritas. Não afirmar que todo erro de transferência é conhecido.
5. Manter os casos originais e sua investigação: MapBiomas para área/percentual por classe em Santo Ambrósio e Tapajós; cruzamento com IBGE sem confundir legendas; linhas explícitas de AGB/serapilheira/necromassa; validação específica das AOIs.
6. Em futuras rotas para outras AOIs, avaliar inventários IFN/SFB e SINAFLOR com estoque/massa, método, unidade amostral, n e erro compatíveis. Profundidade de serapilheira IFN não se converte em massa sem calibração gravimétrica; registro administrativo SINAFLOR não prova medição.
7. Não declarar “erro total conhecido” quando há transferência não quantificada. Preservar limites de domínio e todos os gates científicos existentes.
8. Não excluir artifacts, fechar/mesclar PR #48 ou trocar o artifact final sem instrução do usuário. Se houver nova versão, conferir nome, ID, tamanho e SHA-256 e atualizar este prompt.
