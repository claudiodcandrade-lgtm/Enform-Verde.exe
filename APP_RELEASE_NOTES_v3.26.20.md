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

- No SHA `41d6b14bac637800e4dcdc21ea4ff5b0653919e4`, o workflow SAR #144 passou com 1.692 pixels Sentinel-1 RTC válidos em 3 cenas e runtime scikit-learn 1.8.0. A cobertura processada foi parcial: 1.084,73 ha observados de 1.459,91 ha; a área vetorial classificada totalizou 1.079,26 ha e 5,47 ha não foram classificados dentro da cobertura processada. Safra 2025/2026, experimental, não validada em campo, sem transferência à propriedade. Artefato ID `13949044333`, SHA-256 ZIP `9293e9c9af5a87a08192d89a80a9b7d186f5112eeb2532b950fd4a3294492bae`.
- O workflow dashboard #3390 passou 1.084 testes (147,606 s), compilação integral e sincronização documental. O contrato rápido passou. O gate científico continua reprovado; não houve build Windows nem comprovação GUI/end-to-end, leitura óptica da fazenda, altura ou carbono.
