# Enform Verde v3.26.81-PRECAMPO-EXPERIMENTAL

## Correção do encadeamento entre upload KML/vetorial e execução

O carregamento KML/KMZ/SHP/GeoJSON/GPKG ocorre em segundo plano. Se o usuário acionava EXECUTAR ANÁLISE antes de o worker entregar a geometria à interface, o aplicativo ainda via a AOI como ausente e mostrava a instrução para carregar CAR ou arquivo vetorial. Além disso, a conclusão do worker limpava novamente o estado da análise e podia descartar a solicitação de execução.

Nesta versão, o clique durante a validação vetorial fica enfileirado. Após confirmar a geometria, o fluxo segue para o diagnóstico territorial e inicia a análise automaticamente; se a leitura falhar, a solicitação pendente é cancelada e o motivo é mostrado. A conclusão do upload não limpa novamente o estado que já foi reiniciado antes do worker.

## Estado de validação

Esta candidata deve passar a regressão do caso upload assíncrono → clique antecipado → confirmação da geometria → início automático antes da disponibilização do pacote Windows. Build, teste do EXE limpo e checksum ainda pendentes neste checkpoint. Manter caráter pré-campo experimental; homologação científica independente exige validação de campo.

## Diagnóstico da imagem óptica por AOI

A rota anterior confirmou Sentinel-2 até o canvas somente em Sinop; isso não garante cobertura ou leitura para cada propriedade. A interface agora permite copiar o resultado da AOI atual, com status, provedor, erros e área, removendo URLs assinadas e valores de token. A evidência copiada permite distinguir ausência de cena, indisponibilidade do catálogo, falha de transporte/raster e falha de apresentação. A imagem só é considerada carregada quando pixels ópticos reais são exibidos; o botão melhora o diagnóstico e não é apresentado como prova de que uma fonte já falha foi corrigida. Aceite Windows da cópia sanitizada e os gates ópticos por AOI continuam necessários antes de liberar o pacote.

A sincronização Word desta candidata aceita o estado atual da capa V88.170 em reexecuções, com teste dedicado de idempotência. A cópia final da especificação Word ainda depende do workflow de sincronização na branch da candidata.

## Responsividade ao apresentar relatórios extensos

O relato de congelamento após os relatórios aparecerem levou a duas mudanças nesta candidata: auditorias JSON volumosas são serializadas e gravadas em segundo plano; textos longos são apresentados em blocos agendados, cedendo o ciclo da interface entre inserções. A cópia usa o texto integral mesmo enquanto a tela termina de renderizar. A captura recebida em 19/11/2026 mostra serrapilheira e solo 0–100 cm quantificados, enquanto AGB, raízes e necromassa aparecem como N/D. N/D indica que esses compartimentos não foram estimados nesta análise, não estoque zero. A correção de responsividade precisa passar o gate Windows e o teste do EXE desta candidata antes de ser declarada entregue.

A leitura do relatório completo identificou o bloqueio visual: a proveniência SAR bruta era repetida no texto por estrato, com uma linha de 1.229.817 caracteres. A interface agora exibe apenas estado, indicadores e rotas resumidas; a estrutura integral, inclusive erros e proveniência, permanece no JSON lateral `carbono_formacoes_nativas.json`.

O relatório agrícola anexado para Sinop confirma 30 cenas Sentinel-1 e 2.278 pixels no mapa experimental de 2025/2026, mas não uma classificação semântica atual validada. A triagem recente contém candidatos, não classes confirmadas. O vigor está N/D por ausência de Sentinel-1/referências compatíveis nos polígonos amostrados; a previsão de soja usa PAM/clima sem vigor e aplica área de safra anterior sob transferência não quantificada. Não reportar esses resultados como monitoramento de safra confirmado.
