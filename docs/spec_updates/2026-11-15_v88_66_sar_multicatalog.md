# V88.66 — integração da busca anual SAR MPC e INPE

Candidata 3.26.39-PRECAMPO-EXPERIMENTAL. Relatório da Fazenda Maria Eduarda em 15/11/2026: 12 cenas SAR VV/VH recentes lidas; classes semânticas atuais N/D; classificador LEM+ registrou MESES_RTC_SEM_PARES_VV_VH para todos os meses da janela 2025/2026.

Causa confirmada: sar_landcover_lemplus.py buscava somente Microsoft Planetary Computer, embora a triagem recent_sar_landcover.py já use MPC e INPE. O modelo ENFORM_SAR_BRASIL_RF_V2 está empacotado e exige atributos de doze meses; o leitor anual não consumia a rota INPE.

Implementação proposta nesta candidata: descobrir ano agrícola em MPC+INPE; selecionar apenas um provedor e órbita, maximizando meses observados e usando MPC como desempate; ler INPE COG sem assinar como MPC; registrar provedor/orbita/meses faltantes; abster-se se não houver 12 pares válidos. Não completar meses nem classificar por limiar heurístico.

O teste atualizado usa rasters sintéticos locais para reproduzir doze pares INPE e verificar os 36 atributos. Ele não equivale a validação live. Aceite exige CI completa, prova live da janela anual e execução do KML da fazenda até o painel, carbono, agricultura, vigor e relatório no mesmo run_id/hash. Acurácia e incerteza de transferência local continuam declaradas; status pré-campo experimental, não homologado.
