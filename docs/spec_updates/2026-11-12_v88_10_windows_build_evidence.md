# V88.10 — build experimental Windows e resultados reproduzíveis (12/11/2026)

## Build e teste do EXE
- Commit de código: `cba8b13792a6ae805c8ce4366d64f7ed69a77766`; workflow Windows #2628/run `43235313158`, build `success`. Versão `3.26.20-PRECAMPO-EXPERIMENTAL`; EXE SHA-256 `fc007bc416fdf647e2822f407b8d05e6d3917fecd351cde79e1d51920419fb86`.
- Artefato `Enform-Verde-Windows-v3.26.20-PRECAMPO-EXPERIMENTAL`, ID `13953123396`, tamanho 531.891.569 bytes, digest ZIP SHA-256 `523ca5aed0cbaf28e5cb732c3722c2eb2c2ee496a9bfe4123e287f1ed71ab1b6`; disponibilizado pelo Actions run `43235313158`. `--ui-smoke`, `--module-check`, paridade Python/EXE e aceite SAR do KMZ de teste Tapajós passaram em pasta limpa. `publish-release` foi skipped; é um artefato experimental de Actions, não release científico.

## Pixels e limites espaciais
- Smoke óptico: CBERS-4A/WFI carregou pixels em 11/11 amostras brasileiras, cada uma com cobertura reportada de 100% e limiar contratual 95%; amostras cobrem biomas/extremos, não exaurem todos os pixels/datas do país.
- Smoke worker→fila→canvas Tk em Sinop: imagem real CBERS-4A/WFI/INPE desenhada (673×562, 1 item de imagem), status `PASS_CBERS`. A geometria é a caixa de teste centrada no centroide, explicitamente `NOT original KML`. Não prova a imagem sobre o perímetro exato da Fazenda Maria Eduarda. Prévia Sentinel-2 de pixels do KMZ de teste Tapajós passou.
- SAR Sentinel-1 do KMZ real de teste Tapajós passou, e ALOS-PALSAR/Cerrado passou como rota quantitativa de baixa biomassa. Esses resultados não validam carbono/altura de alta biomassa na fazenda de Sinop.
- Workflow SAR #150 (`43235313209`): `SAR_EXPERIMENTAL_POLYGONS_OBSERVED`, scikit-learn 1.8.0; 1.692 pixels, 30 cenas e caixa de aproximadamente 1.084,73 ha junto ao centroide. Nunca é classe/área da propriedade: o script não processa o KML privado. Safra 2025/2026; sem campo e sem transferência. A leitura ESA MAAP FH ocorreu em BBOX regional, não no polígono.
- O teste detectou ausência de produto FH L2B no Tapajós inventariado; não aceitar altura H100/AGB SAR de alta biomassa ali sem pixels e modelo compatível.

## Regressão e situação científica
- Dashboard workflow #3394 (`43235313385`): 1.086 testes aprovados, compilação completa e sincronização documental aprovadas. Contrato rápido #751 (`43235313409`) passou. A correção da falha de chave `polygon_area_ha` foi reexecutada no relatório de teste e passou.
- Gate de homologação científica independente permanece reprovado. CBERS/Sentinel-2 no KML original da Fazenda Maria Eduarda, pixels/classes SAR no polígono, painel de cultivo e safra, altura/carbono no imóvel e validação de campo continuam sem prova end-to-end. Não chamar a versão de homologada nem apresentar números de caixa como dados da fazenda.

