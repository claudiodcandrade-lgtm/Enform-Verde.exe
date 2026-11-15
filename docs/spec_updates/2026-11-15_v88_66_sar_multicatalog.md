# V88.66 — integração da busca anual SAR MPC e INPE

Candidata 3.26.39-PRECAMPO-EXPERIMENTAL. Relatório da Fazenda Maria Eduarda em 15/11/2026: 12 cenas SAR VV/VH recentes lidas; classes semânticas atuais N/D; classificador LEM+ registrou MESES_RTC_SEM_PARES_VV_VH para todos os meses da janela 2025/2026.

Causa confirmada: sar_landcover_lemplus.py buscava somente Microsoft Planetary Computer, embora a triagem recent_sar_landcover.py já use MPC e INPE. O modelo ENFORM_SAR_BRASIL_RF_V2 está empacotado e exige atributos de doze meses; o leitor anual não consumia a rota INPE.

Implementação proposta nesta candidata: descobrir ano agrícola em MPC+INPE; selecionar apenas um provedor e órbita, maximizando meses observados e usando MPC como desempate; ler INPE COG sem assinar como MPC; registrar provedor/orbita/meses faltantes; abster-se se não houver 12 pares válidos. Não completar meses nem classificar por limiar heurístico.

O teste atualizado usa rasters sintéticos locais para reproduzir doze pares INPE e verificar os 36 atributos. Ele não equivale a validação live. Aceite exige CI completa, prova live da janela anual e execução do KML da fazenda até o painel, carbono, agricultura, vigor e relatório no mesmo run_id/hash. Acurácia e incerteza de transferência local continuam declaradas; status pré-campo experimental, não homologado.


## Correção de regressão do teste de handoff

A primeira execução do contrato modificado falhou por barras de continuação duplicadas no fixture Python. O fixture foi corrigido para testar que a contingência reutiliza sar_details e não chama automatic_pipeline outra vez. Isso é falha do teste, não da rota live SAR; a suíte deve ser repetida no commit final.

# Atualização de correção V88.66 — validação em andamento

O workflow live 43667205598 confirmou a integração MPC+INPE e a inferência de modelo SAR em pixels Sentinel-1 RTC reais num recorte de 0,03° em Sinop: 30 cenas e 12 meses da safra 2025/2026. O recorte (1.084,73 ha) não é o KML integral de 1.459,91 ha; a prova permanece experimental e não demonstra resultado integral no dashboard do usuário.

O dashboard CI detectou syntax error no fixture do teste de contingência por barras de continuação duplicadas; o teste foi corrigido. O build bloqueou porque faltava a nota APP_RELEASE_NOTES_v3.26.39.md; arquivo incluído. Os workflows devem ser repetidos no SHA final.