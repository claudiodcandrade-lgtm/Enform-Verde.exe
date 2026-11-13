# Enform Verde v3.26.24-PRECAMPO-EXPERIMENTAL

- Exibe todas as classes de cobertura espacialmente intersectadas com hectares, percentual da AOI, origem e fechamento da área; resíduos permanecem não classificados/não reconciliados.
- O painel agrícola mostra o tipo de cultivo e “Produtividade estimada no momento dessa análise”, com unidades t/ha e, quando pertinente ao padrão da cultura, sacas/ha e intervalo preditivo.
- Mantém a busca SAR mais recente com tolerância máxima de 30 dias para o monitoramento de vigor e previsão, registrando a data da aquisição; a contingência histórica MapBiomas + PAM não é rotulada como previsão SAR atual.
- O painel de carbono expõe serapilheira por estrato, origem e incerteza, preservando cenários experimentais fora do total conhecido.
- Versão experimental; não declara homologação científica. Build Windows, execução no KML integral da Fazenda Maria Eduarda e disponibilidade de artefato dependem de validação no workflow desta versão.

- Commit `d8ffb4147d52039ae7addffdff345c91c49b6433` publicado na branch `patches-3.26.6`. Testes experimentais de SAR Sinop, pré-campo e acesso ESA FH passaram; build Windows e dashboard aguardam resultado final. Homologação científica independente segue reprovada por ausência de evidência real.

- V88.31 impede que vigor SAR atual seja inferido da máscara anual anterior: usa a máscara corrente de candidato cultivado para diagnóstico relativo com pixels VV/VH de até 30 dias, ou informa N/D/erro com motivo; cultura e sanidade permanecem não confirmadas.
