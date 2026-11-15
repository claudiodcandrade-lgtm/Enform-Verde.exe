# V88.86 — fluxo de vigor SAR e previsão PAM × clima (15/11/2026)

## Causa do vigor N/D
- A rota de vigor contemporâneo recebia fragmentos de pixels como referências de talhões. O classificador automático requer seis referências com ao menos 30 pixels válidos por geometria; os fragmentos falhavam nesse contrato e a série terminava em N/D, mesmo quando a triagem havia lido VV/VH.
- O diagnóstico agora dissolve a máscara de candidatos SAR e a divide deterministicamente em blocos amostrais sem sobreposição. Um bloco é avaliado e pelo menos seis blocos servem de referência interna, mantendo o mínimo configurado e a checagem de 30 pixels. O desenho continua experimental, não representa talhões independentes nem validação de campo.
- A consulta do catálogo e o token temporário são compartilhados pelos blocos de uma AOI; a leitura/validação VV/VH segue por bloco. Isso reduz buscas redundantes sem substituir pixels reais nem relaxar a janela de 30 dias.

## Limite agronômico e safra
- A triagem orbital recente só identifica uma assinatura SAR compatível com cultivo; não identifica soja, café ou outra cultura. O vigor derivado desses candidatos é uma assinatura estrutural relativa e não pode ser tratado como vigor agronômico calibrado nem aplicado à previsão de uma cultura específica.
- Para cenário com máscara SAR anual experimental, o modelo PAM N9 + clima/balanço hídrico continua gerando produtividade condicional a cultura/área e safra dessa máscara histórica. O relatório agora registra a fonte, período, hectares, modelo, PAM, NASA POWER/FAO-56/FAO-33 e se vigor atual específico foi usado. A transferência da área para a safra projetada permanece não quantificada.
- Quando não existe máscara atual validada e vigor específico correspondente, a previsão é explicitamente SEM VIGOR. Vigor estrutural genérico não é injetado no modelo de soja/milho. Linhas provisórias antigas de MapBiomas não podem contradizer a previsão autoritativa SAR/PAM/clima.

## Versão e validação

Candidata: `3.26.45-PRECAMPO-EXPERIMENTAL`.

- Compilação Python passou; `tests.test_crop_report_consistency`: 10 testes aprovados.
- `python -m unittest discover -s tests`: 953 testes descobertos, 30 ignorados, 70 erros e 2 falhas. A maioria dos erros decorre da ausência local de `geopandas`, `shapely`, `rasterio` e `requests`; o teste live Sentinel-1 não leu pixels porque `requests` está ausente. Uma falha é o guard documental antes da sincronização desta entrada. A suíte completa e os testes live precisam ser reexecutados na CI com dependências antes de qualquer build/liberação.
- KML privado integral da Fazenda Maria Eduarda e validação de campo continuam pendentes. A candidata 3.26.45 permanece pré-campo experimental, não homologada.

## Leitura do relatório de carbono Tapajós anexado
- A biomassa aérea informada (123,975 tC/ha na formação florestal) aponta ESA CCI Biomass v7.0, produto L4 multissensor derivado de SAR. Esse rótulo não prova que altura SAR foi medida ou usada como preditor.
- O relatório não apresenta produto de altura, banda/órbita, cenas, pixels válidos, distribuição de alturas nem passagem da altura para a equação de biomassa. Com a evidência disponível, a conclusão é: altura SAR não foi demonstrada como entrada efetiva; AGB veio do CCI derivado de SAR.
- O estoque total está corretamente parcial/incompleto e sua incerteza não mensurável. A incerteza amostral da serapilheira (37,61%) exclui erro de transferência espacial; não deve ser lida como incerteza total da AOI.
