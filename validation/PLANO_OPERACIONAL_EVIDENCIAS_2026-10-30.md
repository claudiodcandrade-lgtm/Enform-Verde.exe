# Plano operacional de evidências independentes — 2026-10-30

Este documento **não é evidência de homologação**. Define a execução acelerada sem criar dados, métricas ou intervalos artificiais.

## Ordem de execução
1. Inventariar datasets observacionais acessíveis SFB/IFN, Embrapa, universidades e solos 0–100 cm, registrando URL, licença, versão, checksum, unidades, desenho amostral, período e fitofisionomia IBGE legenda_1. Rejeitar fontes sem direito de uso demonstrável.
2. Estratificar por fitofisionomia compatível e proximidade microrregional; usar estimadores estaduais IFN somente no último fallback, sempre declarando o erro de transferência e a perda de representatividade. Ausência de erro estimável => N/D para incerteza, não IC95% fictício.
3. Construir tabela de rastreabilidade dos 30 pares bioma × compartimento: AGB, raízes, necromassa em pé, necromassa caída, serrapilheira e solo 0–100 cm. Não preencher lacunas com médias bibliográficas não validadas na AOI.
4. Processar cenas SAR efetivamente baixadas com ID, horário, banda, geometria, pré-processamento, hash e pareamento espacial/temporal com parcelas. Altura de dossel exclusivamente ESA BIOMASS FH P ou TanDEM-X InSAR compatível, GEDI auxiliar; altura de inventário não substitui altura SAR. Produto ou erro não disponível => N/D motivado.
5. Executar validação espacial independente com RMSE, MAE, viés, R², intervalos de previsão/transferência e cobertura empírica, com protocolo de separação treino/teste. Intervalo descritivo não é IC95% da AOI.
6. Validar agricultura (área cultivada antes de espécie), vigor remoto, clima, previsão de safra somente quando sustentada; manter safras bloqueadas se modelo não validado. Testar painéis e regressões.
7. Gerar `validation/release_evidence.json` **somente a partir de artefatos reais verificados**, e validar hashes e caminhos. O manifesto não deve conter placeholders nem declarações de aprovação sem resultados observados.
8. Executar homologação, testes e build Windows no mesmo SHA; conferir teste de extração em máquina limpa, hashes e URL real. PR #50 permanece draft até todas as verificações passarem.

## Gate adicional necessário
O gate atual verifica presença e formato de metadados, mas não verifica a existência e o conteúdo dos arquivos citados por `validation_report`, nem confirma empiricamente que o intervalo marcado `ci95` é IC95% da AOI. Acrescentar verificação dos relatórios, hashes, critérios de independência, proveniência, domínio do modelo e semântica dos intervalos antes de considerar um gate verde suficiente.

## Situação
No SHA `cfd3c42e2f868c500a6f0f9ab19d1dbfdb413dd0`: dashboard e build Windows aprovados; homologação científica reprovada, sem manifesto. Nenhuma validação nova é afirmada por este plano.
