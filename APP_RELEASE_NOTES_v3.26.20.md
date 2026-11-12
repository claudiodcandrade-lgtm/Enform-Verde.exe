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
