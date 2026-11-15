# V88.83 — compartimentos de carbono, incerteza e mosaicos fragmentados

## Candidata

Enform Verde `3.26.44-PRECAMPO-EXPERIMENTAL`. Suíte integral local aprovada: 1.182 testes, 1 ignorado; compilação Python e coleta de 174 módulos aprovadas. Build Windows, workflows do commit final e execução do KML privado da Fazenda Maria Eduarda continuam pendentes.

## Correções no relatório Tapajós

- A rota gravimétrica local de serapilheira aceitava somente o nome detalhado de floresta ombrófila densa. Relatórios do classificador podem chegar com o rótulo amplo `Formação florestal`; a candidata permite esse rótulo apenas dentro da geocerca estrita do estudo de Tapajós e o registra como correspondência ampla de floresta SAR. Isso não confirma subtipo IBGE nem autoriza extrapolação para savanas ou outras regiões.
- A rota de raízes de Cairns estima raízes totais vivas + mortas para estratos florestais compatíveis. A incerteza publicada da relação e a transferência ao local não são completas para esta AOI. A sensibilidade de primeira ordem à incerteza de AGB pode ser apresentada separadamente, nunca como incerteza total ou IC95. Não somar raízes mortas novamente à necromassa abaixo do solo.
- A serapilheira reporta a faixa gravimétrica da fonte quando disponível; a incerteza de transferência por subtipo amplo continua não mensurável. O estrato savânico sem equação/fonte compatível permanece N/D.
- O carbono do solo preserva as faixas marginais publicadas por profundidade e não as promove a IC95 conjunto de 0–100 cm. Sem erro preditivo completo/covariância, a incerteza total continua N/D/“incerteza não mensurável”.

## Desempenho, cache e mosaicos

- O pré-carregamento de fontes PronaSolos e limites oficiais para carbono do solo ocorre uma vez por AOI; os estratos usam a mesma coleção validada e fazem interseção zonal exata. Isso evita downloads e consultas repetidas por formação.
- Aquisições WCS que excedem 1024 pixels por lado são fragmentadas em janelas de 1024 pixels (quadrantes para uma janela 2048×2048). Cada tile numérico permanece no cache; um VRT indexa as janelas para leitura por bloco, sem materializar um array do mosaico nem gravar uma segunda cópia integral. Manifestos registram estratégia e hashes de cada tile; corrupção invalida o cache.
- A malha de tile não altera resolução, CRS, nodata ou cálculo zonal. Tiles incompatíveis são rejeitados. Cache validado permanece reutilizável; cobertura única continua como GeoTIFF.
- Fertilidade, limites marginais de incerteza e perfis PronaSolos usam a mesma abordagem fragmentada/indexada. O limite operacional de fertilidade foi elevado a 64 tiles, após o que a rota retorna motivo de indisponibilidade em vez de exceder recursos sem controle.

## Evidência e limites

- Regressões adicionadas para o rótulo amplo de floresta no Tapajós com restrição geográfica, sensibilidade parcial de raízes, visibilidade sem falsa promoção da incerteza total, cache de fontes de solo por AOI e mosaico VRT sobre tiles. Testes direcionados: 54 aprovados; suíte integral: 1.182 aprovados, 1 ignorado; 174 módulos coletados.
- Não alegar que o relatório privado foi recalculado nem que o executável Windows está pronto até execução de ponta a ponta e build do mesmo SHA. Manter pacote experimental e portões científicos/validação de campo separados.
