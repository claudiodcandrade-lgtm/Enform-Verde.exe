# Enform Verde v3.26.82-PRECAMPO-EXPERIMENTAL

## Correções desta candidata

- A rota ESA CCI Biomass pode ser tentada como segunda rota independente depois da tentativa FH × inventário. Erros e leituras incompletas FH permanecem explícitos na auditoria e nunca são descritos como ausência de cobertura.
- O estado do pipeline distingue rota apenas elegível/tentada de produto AGB realmente obtido. Um erro FH continua sendo falha técnica mesmo quando a consulta CCI é permitida.
- A triagem SAR recente retém localmente os pares VV/VH das cenas lidas com até 30 dias para que a análise de vigor possa reutilizar os pixels da mesma AOI, sem uma segunda busca obrigatória. A saída continua condicional/experimental e pode ficar N/D quando não há blocos ou referências elegíveis.
- O congelamento reportado foi ligado à proveniência SAR integral embutida inline: uma única linha tinha 1.229.817 caracteres. A tela usa extrato compacto, mantém o JSON completo em arquivo lateral e apresenta textos longos em blocos para devolver o ciclo de eventos ao Tk.

## Limites e gates pendentes

Os relatórios enviados em 19/11/2026 mostram AGB, raízes e necromassa N/D; FH BIOMASS retornou HTTP 401 e GTDX exigia autenticação. O relatório agrícola não incorporou vigor à previsão. Estas correções de encadeamento ainda precisam de integração real no Windows até o dashboard/Excel. A rota óptica ainda não foi confirmada na Fazenda Maria Eduarda. Não declarar AGB, vigor, imagem óptica ou correção geral do congelamento como comprovados na AOI sem o teste correspondente.

Verificação local: `python -m unittest discover -s tests` passou com 1.349 testes e 1 ignorado; `python tools/check_test_collection.py` inspecionou 196 módulos; `py_compile` e `git diff --check` passaram. O verificador gráfico `ui_visual_standard.py` não pôde abrir a janela porque o ambiente não tem servidor de display. Build Windows, `--module-check`, `--visual-check`, `--network-check`, EXE em pasta limpa e integração live FH/CCI/inventários→dashboard/Excel permanecem obrigatórios antes de disponibilizar o pacote. A imagem óptica e o vigor na AOI da Fazenda Maria Eduarda também não foram confirmados. Esta candidata ainda não está liberada para distribuição e não representa homologação científica.
