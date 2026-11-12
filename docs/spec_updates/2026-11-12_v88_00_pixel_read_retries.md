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
