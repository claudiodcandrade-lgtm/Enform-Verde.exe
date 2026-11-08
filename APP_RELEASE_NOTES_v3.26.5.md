# Enform Verde 3.26.5-PRECAMPO-EXPERIMENTAL

## Correções nesta candidata

- Retira o MapBiomas da classificação atual de uso/cobertura, cultura, área de cultivo e seleção de referências para vigor. A camada não é consultada no fluxo atual.
- Mantém somente classes SAR semânticas que passem a validação independente por classe. O gate exige pelo menos 30 unidades independentes e limite inferior Wilson de 95% da precisão ≥ 0,70; classes não elegíveis permanecem N/D.
- Adiciona unidades experimentais de assinaturas SAR apenas quando VV/VH atuais foram lidos; as unidades não recebem nome de cultura ou formação sem classificador semântico validado.
- Preserva estados desconhecidos como N/D, sem convertê-los em zero hectares nem uso não nativo.
- Prioriza imagem CBERS-4A/WFI do INPE; se falhar, tenta Sentinel-2 Earth Search e Planetary Computer. Depois admite cache óptico apenas com origem identificável e compatibilidade da AOI/viewport. O mapa cartográfico IBGE só aparece como contingência excepcional, rotulada “MAPA CARTOGRÁFICO — SEM IMAGEM ÓPTICA”, após falha das rotas ópticas. Exige pixels e proveniência explícita para qualquer imagem orbital.
- Remove MapBiomas da identificação e do vigor agrícola; vigor composto depende de altura válida em metros, uniformidade e textura/rugosidade comparáveis.
- Renomeia legenda_2 do IBGE como referência cartográfica que não comprova cobertura vegetal atual, sem incorporá-la às classes SAR atuais.
- Acrescenta quadro delimitado de estoques por compartimento. Incerteza agregada exige independência explícita entre estratos ou covariância total; onde a evidência não sustenta o valor, exibe N/D.

## Estado de verificação

Testes locais do contrato SAR/MapBiomas/CBERS/carbono: 8 passaram. Compilação dos módulos alterados passou. A versão permanece candidata experimental até a regressão completa do repositório, leitura real de CBERS na AOI de referência, execução do EXE em ambiente limpo e build Windows no mesmo SHA.

Não há evidência nesta release de que o classificador semântico de culturas ou vegetação nativa esteja validado para todo o Brasil. A falta de modelo compatível permanece N/D. A medição gravimétrica da serrapilheira só entra na soma quando massa seca, fração de carbono e incerteza de transferência forem sustentadas para o estrato; espessura IFN não é massa seca.
