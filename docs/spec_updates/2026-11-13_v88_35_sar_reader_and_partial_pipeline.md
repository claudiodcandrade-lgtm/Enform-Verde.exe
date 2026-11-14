# V88.35 — leitura SAR alternativa e publicação parcial auditável (13/11/2026)

## Diagnóstico confirmado no arquivo de auditoria da Fazenda Maria Eduarda

O arquivo `uso_solo_auditoria.json` registra 13 cenas SAR candidatas no Microsoft Planetary Computer, 12 selecionadas, 48 tentativas de leitura e zero cenas/pixels legíveis. Os erros incluem `UnicodeDecodeError` na leitura COG pelo transporte GDAL, falhas HTTP e indisponibilidade de token SAS. Portanto, esse caso é `ERRO_TECNICO_LEITURA_SAR`; não é ausência de cenas e não libera contingência como se a busca SAR tivesse terminado sem dados.

## Correções de código na candidata 3.26.25

- Após quatro estratégias GDAL, a rota MPC realiza uma quinta tentativa com URL assinada renovada, Requests/HTTPS com verificação TLS ativa, transferência em streaming para TIFF temporário, limite máximo por ativo, validação do status/tipo/assinatura TIFF e leitura local pelo Rasterio. O temporário é removido ao fechar o contexto. Tokens e URLs assinadas não entram em arquivos de saída ou mensagens de erro.
- O contrato do pipeline permite expor um estado técnico declarado como resultado parcial/N/D quando explicitamente autorizado pelo orquestrador. `result.error`, hash AOI divergente, esquema incompleto e falha interna continuam bloqueando a publicação. A etapa SAR permanece marcada como erro; etapas independentes não são falsamente declaradas concluídas.
- O dashboard recebe `PARCIAL_COM_ERRO_TECNICO` e motivo da etapa, mantendo classes atuais como N/D. Falha do fundo óptico permanece independente dos cálculos quantitativos.
- Fonte de versão: `desktop_app.APP_VERSION = 3.26.25-PRECAMPO-EXPERIMENTAL`, notas de release e este checkpoint. Não reutilizar o artefato ou checksum de 3.26.24.

## Verificações e limites

- Passaram localmente os testes específicos da leitura HTTPS temporária, status parcial, versionamento e rotas de transporte, compilação dos módulos alterados e coleção (166 módulos); suíte completa: 1.130 aprovados e 1 ignorado por ausência de display.
- O teste live do Planetary Computer leu VV e VH no ponto central da área de Sinop. É uma leitura real pontual, não validação do KML integral.
- Uma execução local do leitor no KML integral produziu raster e vetor SAR experimental. O raster tem 146.014 pixels válidos a 10 m (área nominal de células 1.460,14 ha); a soma vetorial recortada é 1.457,793 ha, frente à AOI de 1.459,907 ha. O residual de 2,114 ha permanece não reconciliado e não recebe classe; a soma nominal das células de borda difere da área vetorial e não deve ser reportada como área exata da fazenda. As três classes representam assinatura estável, candidato a uso cultivado e assinatura ambígua — não confirmam agricultura ou vegetação nativa.
- Essa execução direta não conclui a cadeia do aplicativo: faltam um resultado persistido com cenas/data/órbita, execução dos módulos de carbono e agricultura no mesmo `run_id`, conferência da área vetorial e apresentação final na janela do dashboard.
- Teste de regressão da suíte completa encontrou uma falha documental esperada antes da sincronização deste DOCX: falta do novo número de versão. O teste live de VV/VH passou; o `--network-check` do EXE foi ampliado para também ler pixels reais pelas rotas HTTPS locais para VV e VH, exigindo ao menos 100 pixels válidos em cada polarização. A aprovação desta rota depende do workflow Windows no SHA final. Não declarar ainda o build distribuível nem funcionamento ponta a ponta homologado.
- Homologação científica permanece separada e não aprovada sem dados de campo e validação independente.

- O teste do EXE exercita as duas rotas, GDAL e HTTPS local; a rota corrigida só será considerada comprovada no Windows quando o workflow registrar pixels reais válidos para VV e VH no artefato do SHA final.
