# V88.29 — candidata 3.26.24-PRECAMPO-EXPERIMENTAL (13/11/2026)

- Fonte única: `desktop_app.APP_VERSION = 3.26.24-PRECAMPO-EXPERIMENTAL`; notas de release, prompt, especificação e identificação do PR foram alinhados.
- O painel agrícola discrimina todas as classes espaciais intersectadas com ha, % da AOI, fonte/status e fechamento; áreas não classificadas/não reconciliadas ficam explícitas. Exibe tipo de cultivo e “Produtividade estimada no momento dessa análise”, com t/ha e, para soja, sacas/ha, além do intervalo preditivo.
- O vigor/previsão adquire cenas SAR recentes com janela máxima de 30 dias e registra data/fonte; MapBiomas + PAM permanecem contingência histórica identificada, sem se apresentar como SAR atual.
- Serapilheira gravimétrica e transferida de inventários compatíveis é exibida por estrato, fonte, método e incerteza; valores experimentais permanecem fora do total conhecido.
- Suíte integral local: 1.123 testes passaram; 1 skip. `git diff --check` e gates de versão/documentação devem passar antes do commit.
- Estado: candidata experimental não homologada. Build Windows, artefato e execução no KML integral da Fazenda Maria Eduarda ainda dependem de evidência no SHA exato desta candidata.
