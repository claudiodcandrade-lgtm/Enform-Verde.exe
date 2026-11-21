# Enform Verde v3.26.58-PRECAMPO-EXPERIMENTAL

- Inicia a análise de vigor SAR e previsão PAM/clima em paralelo às consultas meteorológicas de apresentação, sem alterar os modelos e equações vigentes.
- Preserva o reconhecimento atual de uso da terra: pixel, máscara ou classe SAR bloqueia a contingência histórica.
- A contingência só é habilitada por certificado de busca completa, com paginação concluída nos catálogos MPC e INPE e nenhuma cena Sentinel‑1 VV/VH compatível para vigor na janela de 150 dias. Erro técnico, busca incompleta ou dados SAR atuais bloqueiam a contingência.
- Quando liberada, mostra no dashboard e na auditoria a estimativa de referência MapBiomas anual × mediana PAM microrregional (2015–2024), com faixa P05–P95. Isso requer área histórica de classe e pelo menos seis anos PAM e não comprova a cultura ou a produção da safra atual. Sem esses dados, retorna N/D com motivo.
- Fertilidade não é covariável de produtividade; modelos e equações anteriores foram mantidos. A contingência histórica PAM/área não recebe ajuste climático; os modelos PAM×clima e PAM×FAO continuam nas rotas próprias quando elegíveis.
- Validação: suíte integral 1.245 testes OK (1 skip headless); 45 testes focados; checker de coleta 183 módulos sem falhas; documentação 4/4 e diff-check aprovados. O gate visual não pôde ser repetido sem display nesta rodada. Build Windows/EXE, teste do KML integral privado Maria Eduarda e validação de campo permanecem pendentes. Versão experimental.
