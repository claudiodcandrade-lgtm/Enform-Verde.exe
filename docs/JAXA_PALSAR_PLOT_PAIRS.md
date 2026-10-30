# Rota verificável: mosaico global JAXA ALOS/PALSAR 2010 × parcelas Tapajós

## O que foi corrigido

O bucket `deafrica-input-datasets` distribui cenas para **Digital Earth Africa**, não constitui espelho global da JAXA. A ausência de objetos no prefixo `alos_palsar_mosaic/2010/S05W055/` **não prova** ausência de observações PALSAR brasileiras. O diagnóstico `tools/diagnose_tapajos_2010_height.py` agora recusa a consulta geograficamente incompatível.

Fontes: [JAXA EORC, mosaicos globais](https://www.eorc.jaxa.jp/ALOS/en/dataset/fnf_e.htm), [registro JAXA](https://www.eorc.jaxa.jp/ALOS/en/palsar_fnf/registration.htm), [especificação de redistribuição DE Africa](https://docs.digitalearthafrica.org/en/latest/data_specs/ALOS_PALSAR_annual_mosaic_specs.html), [conversão DN e datas](https://docs.digitalearthafrica.org/en/latest/sandbox/notebooks/Datasets/ALOS_PALSAR_Annual_Mosaic.html).

## Entrada real exigida

Obter da distribuição global JAXA autorizada os **quatro rasters do mesmo ano e da mesma grade**, para a localização das parcelas: HH, HV, máscara de qualidade e data de observação (dias após 24/01/2006). Formato rasterio compatível (GeoTIFF ou ENVI acompanhado de cabeçalho); não basta PNG/thumbnail ou catálogo. Registrar arquivos originais, ano, origem, versão, autorização/termos de uso e SHA256 de cada arquivo. O software não faz login JAXA, não contorna registro e não comprova automaticamente a autenticidade dos arquivos fornecidos. O uso comercial exige revisão de licença.

As parcelas devem estar em CSV UTF-8 com `plot,lon,lat,h100_field_m`, longitude/latitude WGS84, IDs únicos e altura **de campo**. O arquivo `data/tapajos_ornl1552_structure_v1.csv` contém 30 parcelas de referência e pode ser usado como entrada **somente após verificar sua proveniência, domínio e permissões**.

## Execução auditável

Obter SHA256 de cada arquivo (Windows PowerShell: `(Get-FileHash arquivo.tif -Algorithm SHA256).Hash`; Linux: `sha256sum arquivo.tif`). Substituir todos os marcadores abaixo por caminhos e hashes reais:

```bash
python tools/extract_jaxa_palsar_plot_pairs.py \
  --hh <HH_RASTER> --hh-sha256 <HH_SHA256> \
  --hv <HV_RASTER> --hv-sha256 <HV_SHA256> \
  --mask <MASK_RASTER> --mask-sha256 <MASK_SHA256> \
  --date <DATE_RASTER> --date-sha256 <DATE_SHA256> \
  --plots data/tapajos_ornl1552_structure_v1.csv \
  --plots-sha256 <PLOTS_SHA256> --year 2010 \
  --report validation/tapajos_jaxa_pairs_unvalidated.json
```

O extrator verifica SHA256, integridade da grade/CRS, DN HH/HV 16 bits, máscara **255 = terra válida**, pixel central estritamente dentro da parcela 50×50 m, datas de aquisição coerentes com o ano e unicidade da parcela. Conversão radiométrica: `gamma0_dB = 10*log10(DN²) - 83`. Datas do mosaico são **dias inteiros desde 24/01/2006** (somar diretamente; não subtrair um dia). Não há hora UTC exata no raster anual. Pixels de água, layover, sombra e fora da parcela são excluídos; não há substituição pelo pixel mais próximo.

## Interpretação e bloqueios

O JSON produzido é `OBSERVED_SAR_PLOT_PAIRS_UNVALIDATED`, com `scientifically_validated=false`, `height_sar_m=null`, `aoi_ci95_validated=false`, origem e uso comercial **não autenticados**. Mesmo pares reais não são validação independente: exigir validação espacial em blocos, comparação contra baseline sem SAR, RMSE/MAE/viés/R², erro temporal e transferência entre fitofisionomias. A altura H100 do CSV é de inventário, **não** altura SAR. HH/HV em banda L são retroespalhamento, não um produto de altura. Altura SAR operacional permanece dependente de produto FH real ESA BIOMASS P ou TanDEM-X InSAR compatível, GEDI auxiliar e validação; na ausência, N/D. Não habilitar release por este extrator ou por testes sintéticos.
