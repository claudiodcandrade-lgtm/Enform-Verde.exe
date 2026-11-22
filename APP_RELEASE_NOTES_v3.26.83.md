# Enform Verde v3.26.83-PRECAMPO-EXPERIMENTAL

## Alterações desta candidata

- O mapa passa a apresentar, dentro da AOI, os polígonos vetoriais de uso e cobertura com legenda de classe, origem, área e percentual. O desenho é local e não aciona a busca de imagem óptica; classes experimentais continuam explicitamente identificadas.
- O painel de carbono destaca a soma conhecida em tC e tCO₂e e a chama de parcial quando faltam compartimentos. A planilha de carbono mantém suas abas e gráficos e ganha gráficos separados de estoques por compartimento em tC e tCO₂e.
- O comando Exportar Excel abre uma escolha inequívoca entre a planilha de carbono nativo e a planilha separada de monitoramento agrícola. A planilha agrícola inclui áreas/classes/origens e o relatório disponível de vigor e safra.
- Incertezas de biomassa entre estratos passam a seguir a correlação conservadora ρ=1 aprovada. O desvio espacial de solo é apresentado como estatística descritiva, não como erro de predição ou IC95%; sensibilidade parcial de raízes não é promovida a incerteza total.

## Respostas com base no relatório da Fazenda Maria Eduarda

- **Base expandida de inventários e CCI:** a base IFN expandida foi consultada (5 unidades amostrais elegíveis; 1.023 árvores). O relatório não registra inventários agregados publicados nem fonte externa compatível associada à AOI. Portanto, não há evidência de calibração do ESA CCI por inventários neste resultado. O CCI v7 foi usado como produto de AGB, com 183,49 Mg/ha e incerteza reportada de 63,62 Mg/ha; sua comparação com inventários não foi incorporada ao estoque.
- **FH:** não chegou altura FH válida ao painel desta execução. A busca e paginação do catálogo terminaram, mas a leitura de pixels ficou incompleta e registrou erro técnico; a ausência de dados FH não foi comprovada. A leitura FH real em Sinop já aprovada em outra execução não comprova a leitura nesta AOI.
- **Incerteza:** a soma conhecida no relatório foi 91.581,58 tC (335.799,14 tCO₂e), parcial. A incerteza total permanece N/D porque há compartimentos ausentes e erros residuais/transferência/covariância sem quantificação suficiente. Valores de desvio espacial do solo não são IC nem erro de predição.

## Estado de validação e distribuição

Esta é uma candidata experimental, sem EXE distribuível neste checkpoint. A suíte coletou 1.104 testes: 74 erros de importação/execução, 32 ignorados e uma falha na leitura live de VV/VH Sentinel-1. O coletor inspecionou 197 módulos e não passou porque o runtime carece de `requests`, `geopandas`, `shapely` e `rasterio`. Dos 40 testes focados em painel, incerteza, exportações, mapas, versionamento e documentação, todos passaram. Build Windows, gates module/visual/network e EXE limpo não foram executados. Não declarar homologação científica nem afirmar que o congelamento geral foi eliminado.
