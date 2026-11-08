# V87.38 — contrato de alternativas para o fundo óptico

## Hierarquia obrigatória

O aplicativo deve tentar CBERS-4A/WFI do INPE como fonte óptica prioritária. Se a consulta, leitura COG, máscara ou cobertura válida falhar, tenta Sentinel-2 L2A por Earth Search/AWS e, depois, Planetary Computer. Se ambas as fontes ópticas falharem, aceita cache óptico somente quando a fonte original, data e compatibilidade geométrica/viewport estiverem registradas. Cache de origem desconhecida é rejeitado. Apenas depois de todas essas falhas o mapa cartográfico IBGE offline pode ser exibido.

## Rotulagem e semântica

A interface apresenta a melhor alternativa visual disponível, mantém o perímetro e registra fonte, data, cobertura e motivo de fallback. O mapa final deve exibir claramente “MAPA CARTOGRÁFICO — SEM IMAGEM ÓPTICA”; não é uma cena orbital, não comprova cobertura atual e não pode entrar em classificação SAR/óptica ou cálculo. Se também não houver mapa cartográfico disponível, preservar a geometria e mostrar o diagnóstico das tentativas sem criar imagem falsa.

## Contratos de regressão

1. Com CBERS válido, provar que ele é o provedor exibido antes de qualquer outro.
2. Com falha CBERS e Sentinel-2 válido, apresentar Sentinel-2 e não reprovar por não ter usado CBERS.
3. Com falha das fontes atuais, aceitar cache óptico compatível e identificado; rejeitar cache sem origem óptica.
4. Com falha de todas as fontes ópticas, exibir mapa IBGE como contingência rotulada e conservar AOI.
5. Com falha também do mapa IBGE, conservar AOI e mostrar todos os estados/erros.
6. Smoke distribuído inclui o centro informado para Fazenda Maria Eduarda, Sinop (-55.190498, -11.872667). Registrar imagem, sensor, data e cobertura real. O teste amostral não prova cobertura contínua de cada pixel do Brasil.

MapBiomas permanece separado e não determina cobertura corrente, unidade de mapeamento, cultura, máscara, vigor, previsão, validação ou carbono. O mapa cartográfico excepcional é somente um fundo de localização.


## Legenda cartográfica IBGE não representa cobertura atual
Renomear a saída de legenda_2 para “Cobertura vegetal cartográfica IBGE (legenda_2; referência, não comprova cobertura atual)”. A área não pode ser apresentada como ocorrência observada, nem compor unidades atuais, área de cultura ou carbono. Manter esse contexto separado da ocorrência nativa aceita por SAR semântico.
