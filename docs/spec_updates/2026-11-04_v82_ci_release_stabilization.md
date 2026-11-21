# REVISÃO V82 — Estabilização da compilação e cobertura insular (04/11/2026)
## Erro do build Windows real e correção
- Na reexecução 41947638188, o Windows executou o teste de leitura SAR VV/VH real de Tapajós e passou em seus dados observados. Foi bloqueado no passo “Official IBGE phytoregion classification — real Tapajos AOI” por contrato de UI antigo.
- O teste antigo exigia o texto “código IBGE” dentro do painel **fitofisionomia presente**. Isso era cientificamente inadequado: IBGE legenda_1 representa a REGIÃO FITOECOLÓGICA POTENCIAL, não prova de vegetação atual. O novo contrato exige código e classe no diagnóstico IBGE separado e a fitofisionomia atual mapeada na propriedade sob o título explícito.
- Não alterar o cálculo do inventário nem inventar classificação para passar na suíte.
## Gate de documentação e prevenção de cancelamentos
- O contrato Python tools/check_docs_updated.py retorna a chave estável docs/ESPECIFICACAO_TECNICA_COMPLETA.docx mesmo quando falta checkpoint, preservando retrocompatibilidade de testes; mantém opção de checkpoint sincronizado quando Word binário é commit posterior.
- Os workflows Windows e dashboard deixam de cancelar execuções de outros SHAs da mesma PR quando o bot documental publica somente o DOCX; grupo de concorrência agora é por SHA do código e cancel-in-progress=false.
- Continuar exigindo o SHA exato do checkout e pacote final e não liberar ZIP sem smoke completo Windows.
## Nacionalização geográfica
- O envelope de plausibilidade para coordenadas do Brasil é ampliado para abranger São Pedro e São Paulo, Fernando de Noronha e Trindade/Martim Vaz e o território continental; é mera triagem de coordenadas, não substitui fronteira oficial nem classifica biomas.
- A regra mantém processamento para AOIs nos seis biomas, cálculo de áreas em EPSG:6933, origem, data, incerteza por compartimento e N/D quando não estimável; triagem experimental SAR ≠ vegetação ou lavoura validada.
## Status
- Essas correções de engenharia precisam de novos testes, compilação, manifesto SHA/ZIP e link verificável. A homologação científica independente segue reprovada sem evidências de campo observacionais suficientes. Não declarar EXE novo pronto até a publicação de artefato resultante da execução exata.
