# V88.00 — Diagnóstico e retentativas de leitura de pixels

## Falha de referência

O relatório da Fazenda Maria Eduarda, versão 3.26.18, registrou falha técnica na leitura SAR, ausência de pares VV/VH na janela sazonal, `UnicodeDecodeError` na contingência MapBiomas + PAM e ausência da imagem óptica. Esses resultados não provam ausência de cenas nem de pixels na AOI.

## Requisitos implementados

- MapBiomas repete a leitura do GeoTIFF em três transportes GDAL: configuração padrão multirange, ranges serializados sem HEAD/HTTP 1.1, e multirange sem multiplexação/HTTP 1.1. Registra a etapa `open_cog`, `read_pixel_window` ou `summarize_pixels`, estratégia usada e erro sanitizado.
- Sentinel-1 recente e LEM+ tentam quatro combinações de transporte/credencial. A auditoria informa fase da falha, estratégia, número da tentativa e detalhe da exceção sem URLs assinadas.
- Falha técnica de leitura LEM+ retorna `ERRO_TECNICO_LEITURA_SAR`; falta efetiva de cenas ou pixels válidos retorna `N/D_SEM_PIXELS_SAR`.
- Os leitores CBERS-4A/WFI e Sentinel-2 repetem a mesma cena com três transportes de COG antes de descartá-la. A imagem só é aceita após verificar pixels RGB e cobertura mínima da AOI.
- O relatório do fallback MapBiomas + PAM inclui etapa e detalhe. A contingência continua exclusivamente histórica e só pode ser avaliada depois da execução terminal de todas as rotas SAR configuradas.

## Verificação e liberação

Cinco testes unitários do fallback passaram; compilação sintática e `git diff --check` passaram. A suíte que importa a GUI não foi executada neste ambiente por ausência da dependência `requests`. Build e testes Windows ainda pendentes. A leitura de pixels no KML integral da Fazenda Maria Eduarda não foi demonstrada; esta revisão não pode ser declarada funcional para a fazenda até a evidência do executável Windows na geometria original.

## Referência técnica

GDAL, documentação oficial de `GDAL_HTTP_MULTIRANGE`, `GDAL_HTTP_MULTIPLEX`, `GDAL_HTTP_VERSION` e `/vsicurl/`: https://gdal.org/en/stable/user/configoptions.html e https://gdal.org/en/stable/user/virtual_file_systems.html

O arquivo Word completo é atualizado a partir deste checkpoint pelo workflow de sincronização do repositório, mantendo o histórico editorial e o registro de versão.

## V88.01 — Evidências do build e sincronização documental (12/11/2026)

- No workflow Windows #43127520197, a imagem CBERS-4A ou Sentinel-2 chegou ao canvas Tk em Sinop; o smoke óptico distribuído por biomas/extremos, o pixel SAR Sentinel-1 no KMZ real do Tapajós, a validação de fontes SAR, os pixels ALOS-PALSAR do Cerrado e a cobertura ESA BIOMASS FH nos AOIs apoiados por inventários do Tapajós passaram.
- O empacotamento não ocorreu. A suíte completa falhou em `test_versioned_spec_is_valid_docx_with_current_update`: o job fixou o SHA `14df5ab4dfe5aba156a7f1218dab2f1fdfeebc74`, iniciado antes do commit `6b1673e49565defc45acbd311e1880147c9c3b59` que sincronizou o DOCX com V88.00/3.26.19. É uma corrida de ordem entre workflows, portanto o build deve ser repetido sobre um commit que já contenha a especificação Word atual.
- Essas amostras não validam o KML integral da Fazenda Maria Eduarda, não comprovam classificação agrícola/carbono nessa fazenda e não equivalem a cobertura exaustiva de pixels de todo o Brasil. O gate científico independente permanece reprovado; não declarar calibração nem homologação.

## V88.02 — Build Windows 3.26.19 concluído (12/11/2026)

- A suíte completa concluiu sem falhas (1.080 testes). O executável passou compilação, runtime empacotado, autocheck em diretório limpo, paridade dos módulos Python/EXE, verificação visual, leitura de pixels reais e aceitação SAR do KMZ de teste do Tapajós.
- Workflow Windows #43130208992, código-fonte `8d9d56d442e967474dbb66f5452cfb9d728f8e7a`, conclusão `success`. Artefato `Enform-Verde-Windows-v3.26.19-PRECAMPO-EXPERIMENTAL`, ID `13905414794`, 533.419.321 bytes; SHA-256 do EXE `9907b91a615ad45011efa7c832dea4bd86506d661cef222e89958c28281fc7fb`; digest SHA-256 do ZIP `2586497f0d0b0b09aa59181b7662736dd0bc570981432de06c502e53550784b9`.
- As provas ópticas distribuídas em 11 AOIs representativas (limiar de cobertura de pixels de 95%) passaram; CBERS-4A ou Sentinel-2 foi efetivamente renderizado no canvas Tk de teste em Sinop. O KMZ real usado na aceitação SAR do Tapajós passou. Isso é evidência operacional nos AOIs/testes indicados, não prova exaustiva de todos os pixels do Brasil.
- O pipeline Sentinel-1/MPC e a classificação semântica sazonal na geometria integral da Fazenda Maria Eduarda não foram comprovados neste build. Tampouco foram calculados carbono ou classes agrícolas para esse KML. Gate de homologação científica independente permanece reprovado. Distribuir como versão **experimental de pré-campo**, sem alegar calibração, homologação ou validade decisória.
