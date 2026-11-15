# Auditoria funcional V88.66

Data: 15/11/2026. Candidata 3.26.39-PRECAMPO-EXPERIMENTAL. AOI relatada: Fazenda Maria Eduarda, Sinop/MT. A versão 3.26.38 passou CI/build, mas o relatório de execução posterior demonstrou falha real; as aprovações anteriores não comprovam esse percurso.

## Causa confirmada

O modelo ENFORM_SAR_BRASIL_RF_V2 já está no pacote e exige pares VV/VH por 12 meses agrícolas. O classificador anual consultava somente Microsoft Planetary Computer; a triagem recente usava MPC e INPE e por isso lia cenas que não chegavam ao vetor de atributos do classificador. A triagem gerava candidatos experimentais, mas não classe semântica. O carbono só processava estratos nativos classificados, então a falha semântica também deixava compartimentos N/D.

## Correção da rota principal

A busca anual usa agora MPC e INPE. Escolhe uma única fonte e órbita com maior cobertura mensal, prioriza MPC apenas em empate e lê assets INPE diretamente. Não mistura provedores. Se a janela ainda não tiver 12 pares lidos, abstem-se e registra provedor, órbita e meses faltantes, sem fabricar máscara. O teste local usa GeoTIFFs sintéticos.

## Correções secundárias

A contingência de inventário não relança SAR e pode executar cenário condicional, sempre separado do estoque medido. Falha ao atualizar fundo mantém a última imagem óptica válida. Nenhum desses itens substitui a classificação principal.

## Situação

CI anterior falhou porque um teste esperava a segunda execução SAR. O teste foi atualizado para exigir reutilização das evidências da execução corrente. A CI da busca anual MPC+INPE e o live de Sinop ainda estão pendentes. O teste sintético não é prova de disponibilidade real. Não distribuir como funcional nem homologado até todos os gates aceitarem o mesmo commit e o KML integral chegar aos painéis/relatórios com o mesmo run_id/hash.
