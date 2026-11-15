# Correção funcional V88.66 — 3.26.39-PRECAMPO-EXPERIMENTAL

Data: 15/11/2026. Base: 4962b1fa90ccb89d075ec56e3f9aae049cec410a. Esta é uma candidata experimental; precisa passar CI e novo teste integral com a AOI real.

## Diagnóstico confirmado pelo relatório do usuário

- 12 cenas Sentinel-1 VV/VH foram lidas e resultaram em candidatos SAR; o painel preservava parte desses dados, mas a rota operacional não produzia classes semânticas validadas.
- A contingência de carbono consultava SAR novamente depois do cálculo nativo. Falha nessa segunda consulta impedia o cenário de inventário; a contingência ainda exigia certificado de ausência de cenas mesmo quando o objetivo era apenas um cenário condicional.
- Uma atualização óptica com falha apagava o mapa previamente aceito e deixava apenas o perímetro.

## Alterações nesta candidata

- Reutiliza os detalhes SAR da análise corrente para o cenário de inventário e não reinicia SAR nesse caminho.
- Separa o modo de cenário condicional do gate de ausência confirmada de pixels. Mantém a área-base IBGE como potencial, não confirma cobertura nativa, e não soma o cenário ao estoque medido. A disponibilidade de fonte compatível continua determinando se o resultado será numérico ou N/D.
- Preserva a última imagem óptica aceita se a tentativa de atualização falhar. Isso não converte mapa cartográfico em imagem óptica.
- Acrescenta regressões para preservar a imagem em falha de atualização e para impedir que o modo condicional afrouxe o gate operacional padrão.

## Limites

As áreas de candidato SAR não são classes de cultura validadas. A classificação semântica, os compartimentos de carbono sem fonte compatível, a transmissão ponta a ponta no dashboard e o teste completo da Fazenda Maria Eduarda ainda precisam de confirmação na nova build. Até essa evidência, manter status pré-campo experimental e não homologado.
