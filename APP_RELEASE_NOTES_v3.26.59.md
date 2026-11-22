# Enform Verde v3.26.59-PRECAMPO-EXPERIMENTAL

- Integra previsão contingencial PAM×clima sem vigor ao dashboard, liberada somente após certificado de busca completa MPC+INPE sem cenas Sentinel-1 VV/VH compatíveis para vigor.
- Mantém as equações anteriores para soja/milho e a matriz PAM×déficit climático/vigor para outras culturas elegíveis. Sem vigor, percorre o envelope de quantis sem atribuir classe; a saída segue experimental e não calibrada.
- Reserva histórica MapBiomas anual × mediana PAM é usada somente quando a rota normal falha após o gate exigido; fonte, intervalo e limitação são auditados. MapBiomas permanece vedado para inferir uso, vigor ou carbono atuais.
- Busca climática reutiliza cache por ponto/período dentro da execução. Fertilidade não é covariável. Nenhuma redução de tempo é alegada sem benchmark comparável.
- Verificação local: 1.247 testes OK, 1 skip; coleta de 183 módulos aprovada. Leitura live Sentinel-1 VV/VH passou em uma cena com 9 pixels válidos por polarização.
- Estado: candidata experimental, não homologada. Padrão visual sem execução por ausência de display; build Windows/EXE, handoff integral carbono→dashboard, ensaio end-to-end do KML da Fazenda Maria Eduarda e validação de campo continuam pendentes.
