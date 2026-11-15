# V88.05 — paridade entre modelo SAR e runtime (12/11/2026)

## Correção
- O manifesto do `sar_brasil_rf_v2.joblib` agora declara que o modelo foi serializado com scikit-learn 1.8.0. `requirements_desktop.txt` fixa `scikit-learn==1.8.0`; `sar_landcover_lemplus.load()` recusa um runtime divergente com `VERSAO_SKLEARN_INCOMPATIVEL`, antes de carregar o artefato.
- Teste adicionado para assegurar que incompatibilidade da biblioteca não gere classificação silenciosamente. O teste positivo carrega o modelo no runtime 1.8.0.

## Evidência na AOI de Sinop e limites
- Reprocessamento direto do KML completo sob scikit-learn 1.8.0 retornou as mesmas áreas experimentais sazonais reportadas anteriormente: corte raso/solo exposto 576,00 ha; soja 399,36 ha; café 1,92 ha; área cultivada sem cultura identificada 3,20 ha; floresta nativa por assinatura SAR 471,68 ha; outra vegetação nativa por assinatura SAR 5,12 ha; área úmida 0,64 ha. Total classificado 1.457,92 ha de 1.459,91 ha; 1,99 ha sem classe.
- Estas classes são sazonais, experimentais e não validadas em campo nesta fazenda. Resultado do classificador não mede altura, biomassa nem estoque de carbono, e ainda não comprova atualização dos painéis do dashboard.
- No runtime compatível: suíte completa 1.083 testes aprovados e 1 ignorado; coleta/importação 157 módulos; 12 testes direcionados passaram. A suíte não substitui o gate de GUI/EXE.
- A imagem óptica no KML integral, o dashboard completo e o EXE Windows permanecem pendentes; não declarar a versão Windows concluída.
