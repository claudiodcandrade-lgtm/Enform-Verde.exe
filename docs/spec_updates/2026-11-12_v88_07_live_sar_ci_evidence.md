# V88.07 — processamento SAR real em Sinop após alinhamento do runtime (12/11/2026)

## Evidência reproduzível
- Commit testado: `41d6b14bac637800e4dcdc21ea4ff5b0653919e4` (`Pin SAR model runtime across CI workflows`).
- Workflow Sentinel-1 SAR experimental #144: run `43231012155`, conclusão `success`; artefato `sinop-real-sar-experimental-144` (ID `13949044333`, SHA-256 do ZIP `9293e9c9af5a87a08192d89a80a9b7d186f5112eeb2532b950fd4a3294492bae`). O instalador usou scikit-learn 1.8.0, os contratos VV/VH passaram, e o classificador executou com pixels Sentinel-1 RTC reais.
- Resultado do diagnóstico experimental: 1.692 pixels válidos, 3 cenas; área com pixels observados reportada `1.084,73 ha` de `1.459,91 ha` da fazenda; área vetorial classificada `1.079,26 ha`; área não classificada dentro da cobertura processada `5,47 ha`. Cobertura espacial incompleta: não extrapolar classes para o restante da AOI nem renormalizar percentuais para 100% da fazenda.
- Período inferido: safra 2025/2026. O relatório marca `field_validated=false`, `current_sowing_season_2026_27_verified=false` e `ready_for_property_transfer=false`. É evidência operacional de leitura e inferência SAR experimental, não validação agronômica/biológica.
- Workflow dashboard #3390: run `43231012125`, `success`; suíte integral: 1.084 testes em 147,606 s, todos aprovados; compilação integral e contrato documental também passaram. Workflow de contratos rápidos #747 (`43231012162`) passou.

## Limites que permanecem
- O gate independente de homologação científica (`43231012004`) continua reprovado por ausência de evidências científicas independentes exigidas. CI verde não significa modelo homologado.
- A execução SAR acima não demonstra que a GUI/EXE consumiu e exibiu esses polígonos. Não houve build Windows associado a esse commit nem prova ponta a ponta no dashboard da Fazenda Maria Eduarda.
- Não foram calculados altura de dossel, biomassa ou carbono nesse run; a classificação de cobertura não substitui esses parâmetros. Imagem óptica CBERS/Sentinel-2, integração do SAR ao dashboard, altura/carbono e validação com dados de campo permanecem pendentes.
- A proteção contra a regressão específica consiste no runtime fixo `scikit-learn==1.8.0` no requisito desktop e nos workflows, contrato automatizado de paridade e bloqueio fail-closed no loader antes de desserializar modelo incompatível. Isso impede a repetição silenciosa dessa divergência, mas não prova disponibilidade universal de cenas ou pixels em qualquer AOI/data.

