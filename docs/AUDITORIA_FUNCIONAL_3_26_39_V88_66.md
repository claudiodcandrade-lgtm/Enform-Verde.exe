# Auditoria funcional V88.66 — atualização live

A conexão principal foi corrigida no classificador anual: a busca RTC MPC+INPE encontrou pares VV/VH para a janela agrícola completa. No workflow live 43667205598, recorte de 0,03° próximo ao centroide de Sinop (não KML integral): 30 cenas, doze meses da safra 2025/2026, 1.692 pixels; modelo ENFORM_SAR_BRASIL_RF_V2 gerou polígonos experimentais. Classificou áreas experimentais de soja, floresta nativa, área antrópica/corte raso e úmida. A área do recorte foi 1.084,73 ha, inferior à AOI reportada de 1.459,91 ha. Sem validação de campo; incerteza de transferência para a fazenda não mensurável.

A prova confirma o mecanismo da falha anterior e que a rota principal opera num recorte real. Ainda não confirma processamento do KML integral, entrega de máscaras a carbono/agricultura/dashboard na execução do usuário, imagem óptica persistente, ou build Windows final. O dashboard CI detectou erro de sintaxe no fixture do teste de contingência (dupla barra de continuação); teste corrigido e precisa ser repetido. O build Windows também barrou a ausência de APP_RELEASE_NOTES_v3.26.39.md; arquivo incluído. CI após ambos os ajustes é obrigatória.

Status: 3.26.39-PRECAMPO-EXPERIMENTAL em validação; não homologado. Não liberar como final até dashboard, build Windows e processamento ponta a ponta da AOI real passarem no mesmo SHA.
