# Atualização de especificação — fallback SAR agrícola piloto

Data: 09/11/2026. Escopo: apresentação operacional de evidência temporal SAR sem forçar uma cultura nominal.

## Regra

Quando a série VV/VH apresentar a assinatura temporal variável da heurística existente, o sistema pode exibir “Área cultivada — candidato SAR experimental; cultura N/D”. As classes estável e ambígua permanecem com uso/cobertura N/D. Essa é uma hipótese para inspeção de campo, não um mapa de cultura confirmado.

## Limites de uso

- Não converter quantis ou sensibilidade de limiar em probabilidade, intervalo de confiança ou acurácia.
- Não usar o candidato para carbono de vegetação nativa ou produtividade PAM.
- Não atribuir soja, milho, sorgo, café, cana, arroz, feijão, citros ou algodão sem modelo executável compatível e avaliação por classe.
- Preservar fontes, identificadores e datas das cenas; geometria privada não vai para o repositório.

## Critérios de integração a cumprir

CBERS-4A/WFI é o fundo óptico primário e Sentinel-2 é contingência; demonstrar pixel real e cobertura da AOI, sem tratar sucesso em outra área como prova. Para cultivos, integrar modelos nacionais e internacionais com domínio e incerteza documentados, depois combinar vigor SAR, clima e PAM na previsão. Para formações nativas, combinar altura SAR, inventários microrregionais, estrutura horizontal, alometria acima e abaixo do solo e serapilheira da mesma fitofisionomia. Carbono no solo permanece Embrapa/PronaSolos 0–100 cm por interseção exata.

O gate científico independente permanece separado. Esta atualização não declara homologação nem liberação.
