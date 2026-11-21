# V87.43 — decisão e experimento TerraClass/PRODES (08/11/2026)

## Decisão registrada

O proprietário autorizou usar PRODES/TerraClass como rótulos cartográficos de treinamento para uma rota experimental amazônica. Esse consentimento não converte mapas em observações de campo, não autoriza chamar concordância cartográfica de acurácia de campo e não substitui validação independente.

Hierarquia operacional confirmada pelo proprietário em 08/11/2026: modelos/dados testados e homologados têm prioridade. O experimental é contingência claramente rotulada, somente quando não houver modelo testado aplicável; se também não houver uma rota experimental elegível, retornar N/D com motivo.

## Implementação

- Novo módulo `terraclass_sar_experiment.py` e CLI `tools/train_terraclass_sar_experiment.py` treinam um Random Forest experimental com atributos SAR co-registrados e polígonos TerraClass 2024.
- Classes são agregadas para vegetação nativa, agricultura, pastagem, silvicultura e outros usos. TerraClass não é tratado como fonte de identificação de soja versus milho.
- Avaliação GroupKFold separa blocos espaciais de 5 km (ajustáveis entre 1 e 50 km); a matriz e as métricas recebem o nome `map_agreement`, não `field_accuracy`.
- O relatório grava hash SHA-256 do modelo, ano, domínio, tamanho amostral e número de blocos; marca `field_validation=false` e `release_eligible=false`.
- O treino exige raster SAR e referência do mesmo ano (2024), CRS projetado, atributos em grade comum e pelo menos cinco blocos. PRODES não é usado para rotular classes de cultura; sua série de supressão é apenas contexto/controle temporal.
- A nova rota é opt-in e não altera a classificação padrão, o total de carbono nem o registro de modelos validados. Não há modelo pré-treinado instalado nem execução em dados reais incluída neste patch.

## Cobertura e limitações territoriais

- A referência TerraClass 2024 está disponível para Amazônia e Cerrado, em conjunto cobrindo aproximadamente 73% do território nacional. Isso não equivale a treinamento validado para todos os biomas.
- PRODES mapeia supressão anual de vegetação nativa em todos os biomas, mas não classifica o uso posterior de cada área; seus rótulos não permitem inferir cultura atual.
- Os demais biomas seguem com classificação SAR semântica N/D até existir referência compatível e amostras SAR correspondentes. A interface deve declarar a área e o motivo, sem deixar campo vazio.
- Vigor: não foi instalado coeficiente verificável de altura por cultura/região/fase. Referências de literatura permanecem candidatas experimentais; sem modelo, observação e RMSE compatíveis, altura e vigor permanecem N/D.
- Não declarar operação nacional completa nem liberação EXE até treino com dados reais, matriz nacional de disponibilidade, regressão e build Windows no mesmo SHA.

## Métricas e proveniência

- Precisão/recall por classe recebem IC95% via bootstrap de blocos espaciais, preservando a unidade de reamostragem geográfica; esses intervalos quantificam a concordância cartográfica.
- O JSON grava hash SHA-256 do raster de atributos SAR, do vetor TerraClass (incluindo componentes do shapefile) e do modelo, além de CRS, dimensão e transformação da grade.
- PRODES é registrado como contexto, mas `prodes_used_as_label=false`; assim não se confunde supressão da vegetação com classe agrícola atual.

## Fontes oficiais

- TerraClass: https://www.terraclass.gov.br/
- INPE/Embrapa — TerraClass 2024: https://www.gov.br/inpe/pt-br/assuntos/ultimas-noticias/terraclass-divulga-dados-atualizados-sobre-cobertura-e-uso-da-terra-no-bioma-amazonia
- INPE BiomasBR — PRODES: https://data.inpe.br/biomasbr/prodes-monitoramento-anual-da-supressao-de-vegetacao-nativa/
