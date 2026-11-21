# V88.119 — verificação local da candidata e contagens do catálogo (16/11/2026)

- Corrigidas as expectativas do catálogo após ingestão IFN e ORNL/Tapajós: 4 conjuntos primários locais, 2 conjuntos harmonizados em nível de parcela, 30 registros de datasets públicos curados.
- IFN/DAP10: 841.387 observações arbóreas e 8.951 unidades amostrais locais. Continua com `model_eligible=0` enquanto não houver revisão do desenho, das chaves, das variáveis, da representatividade e validação independente. Tapajós/ORNL é o outro conjunto em nível de parcela harmonizado; Mexiana/Santo Ambrósio e Jalapão preservam limitações específicas.
- Suíte integral: 1.247 testes passaram; 1 skip. `tools/check_test_collection.py` passou para 183 módulos.
- Leitura live isolada Sentinel-1 VV/VH: uma cena, 9 pixels válidos por polarização. Não valida vigor, previsão, cobertura nacional ou calibração.
- Padrão visual não executado por ausência de servidor gráfico. Continuam pendentes build Windows/EXE, handoff completo carbono→dashboard, teste end-to-end com AOI integral da Fazenda Maria Eduarda e validação independente de campo. Não houve benchmark de tempo; não alegar ganho de desempenho.
- Versão do aplicativo permanece 3.26.59-PRECAMPO-EXPERIMENTAL; sem homologação.
