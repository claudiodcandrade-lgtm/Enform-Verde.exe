# V88.09 — correção do KeyError no resumo da caixa SAR (12/11/2026)

## Falha reproduzida
- No workflow SAR #147 (`43234476197`), a coleta e classificação Sentinel-1 na caixa de teste concluíram, mas a etapa final do relatório falhou com `KeyError: 'polygon_area_ha'`. A renomeação para `sample_box_polygon_area_ha` deixou uma referência antiga no cálculo de área não classificada. O job falhou fechado e não deve ser descrito como resultado concluído.
- Corrigida a referência por meio de `summarize_sample_box()`, que calcula as áreas por classe, total classificado e saldo não classificado usando somente chaves `sample_box_*`. Teste unitário verifica os três resultados e a ausência da chave antiga.
- Esta correção é para o relatório da caixa de teste próxima ao centroide, não processa o KML da fazenda e não altera resultados ou métodos de carbono.

## Verificação
- Reexecutar teste unitário, workflow SAR real e compilação/regressão no commit desta correção. Não reutilizar artefatos do run #147 como saída bem-sucedida; o run #147 serve somente como reprodução do defeito.
- Continuam sem prova: integração à GUI/EXE, execução no KML integral, imagem óptica no perímetro real, estimativa de altura/estoque de carbono e monitoramento da fazenda.