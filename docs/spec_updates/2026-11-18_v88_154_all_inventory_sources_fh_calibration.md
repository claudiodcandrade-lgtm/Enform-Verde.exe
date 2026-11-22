# V88.154 — Calibração FH com toda a base de inventários

Data: 18/11/2026  
Aplicativo de referência: 3.26.71-PRECAMPO-EXPERIMENTAL

## Regra de seleção da base

Calibração da altura ESA BIOMASS FH não pode depender exclusivamente do IFN/SFB. Consultar a base expandida inteira e selecionar cada fonte conforme as variáveis e a qualidade disponíveis. Inventários de árvore/parcela, bases institucionais, levantamentos acadêmicos, inventários de manejo e estudos publicados podem contribuir para calibração de altura, estrutura horizontal, AGB ou validação, desde que cada uso respeite a unidade amostral, o domínio e a proveniência.

Para pares de calibração H100–FH, exigir altura de campo compatível com H100 ou dados individuais suficientes para derivá-la, área amostral conhecida, localização/footprint, data, método, definição da métrica, fitofisionomia compatível e produto FH identificado. A métrica H100 é a média das 100 árvores mais altas por hectare; em parcelas menores, derivar o número equivalente a partir da área amostral. Não derivar H100 a partir de fonte sem área. Isso não impede que essa fonte contribua para parâmetros horizontais ou AGB quando esses indicadores tiverem denominadores e métodos compatíveis.

No pareamento, agregar FH ao footprint da parcela, respeitar resolução e erro de localização, manter a defasagem temporal explícita e impedir pseudorreplicação. Harmonizar a tipologia com IBGE legenda_1 e estratificar por microrregião/fitofisionomia. Validar por sítios/estudos independentes e propagar a incerteza de campo, produto, pareamento, tempo e transferência. Preservar FH bruto e calibrado em campos distintos. O modelo FH×estrutura horizontal gera uma estimativa única de AGB; CCI é contingência exclusiva para ausência FH real certificada.

## Correção da evidência de teste

No SHA `96f279c8d03e4e32376f5b6c2a2480c600efaa93`, a regressão Python e os checks de UI, imagem óptica CBERS-4A e pixels Sentinel-1 passaram. A prova MAAP separada leu pixels reais ESA FH em Sinop. Contudo, o autoteste do EXE compilado falhou no AOI de aceitação Tapajós com `ERRO_TECNICO_ROTA_PRIORITARIA` em FH/GTDX; o gate bloqueou corretamente a contingência e a publicação. O resumo detalhado da aceitação não foi impresso no log, então o próximo build inclui sua emissão sanitizada para identificar a causa concreta. Não liberar o artefato desse SHA como versão aprovada.

## Estado de implementação

A rotina de derivação H100 foi generalizada para aceitar um quadro harmonizado de qualquer fonte confiável e manter fontes distintas separadas mesmo quando os códigos de parcela coincidem. A rotina continua não criando pares FH–parcela nem integrando calibração ao fluxo AGB. A consulta de todas as fontes, a harmonização geoespacial/temporal, a calibração com validação espacial, a propagação de incerteza e o handoff até dashboard seguem como gates. A homologação científica permanece separada e pendente de validação de campo independente.
