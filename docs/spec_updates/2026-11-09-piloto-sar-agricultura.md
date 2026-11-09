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


## Checkpoint V87.54 — integração piloto e falhas CI (09/11/2026)

O SHA auditado foi `07061b450c6ebc62e8bdf868da236b8c07799164`, com versão `3.26.7-PRECAMPO-EXPERIMENTAL`. O fallback temporal SAR VV/VH da classe sazonal é exibido como “Área cultivada — candidato SAR experimental; cultura N/D”; não identifica cultura nominal, não confirma vegetação nativa e não gera probabilidade, acurácia ou IC. CBERS-4A/WFI continua prioritário para fundo óptico, Sentinel-2 como alternativa. A renderização da geometria privada Fazenda Maria Eduarda dentro do EXE ainda não está demonstrada.

No SHA auditado, contratos rápidos passaram. O dashboard falhou em dois contratos: versão ausente no DOCX e expressão textual de classe semântica N/D divergente. O build Windows falhou no job `42676730241`, antes de empacotar/publicar o EXE; o dashboard `42676730580` registrou 999 testes com duas falhas; contratos rápidos `42676730626` passaram. O gate científico `42676730154` segue reprovado (`accepted_count=0`). Corrigir a sincronização documental e a redação do contrato, depois executar novo CI no SHA final. Não declarar build, regressão privada, homologação ou liberação concluídos até as evidências correspondentes passarem.

Prioridades do piloto: série temporal SAR observável com proveniência por cena; modelos executáveis por cultura e domínio com incerteza; vigor SAR + clima + PAM para safra; altura e estrutura nativa com inventário microrregional e alometria; serapilheira compatível por fitofisionomia; carbono do solo Embrapa/PronaSolos 0–100 cm por interseção. A geometria privada não pode entrar em commits nem em logs públicos.