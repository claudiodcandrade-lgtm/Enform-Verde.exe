# V88.96 — fecha conexão SQLite no teste Windows (16/11/2026)

## Diagnóstico

A suíte completa do dashboard no Windows, execução `43793752888` sobre V88.94, executou 1.221 testes e falhou com um erro em `test_discovered_records_are_leads_not_calibration_inputs`. A asserção de conteúdo passou; a limpeza de `TemporaryDirectory` falhou com `WinError 32` porque o teste usava o gerenciador de contexto `with sqlite3.connect(...)`, que não fecha a conexão SQLite ao sair. O arquivo `inventories.sqlite` permanecia bloqueado no Windows.

## Correção

O teste agora fecha a conexão explicitamente em `finally`, garantindo liberação do arquivo antes da exclusão do diretório. A correção é restrita ao teste e não altera o banco nem o comportamento de produção. O teste local específico deve passar; a suíte completa e o build precisam ser repetidos no novo SHA.

## Estado

V88.95 já contém o bloqueio de nomes de culturas SAR fora do envelope e seu teste de integração, mas a execução Windows dessa nova revisão ainda não terminou; o teste integrado será considerado validado apenas se o runner executar GeoPandas e passar. Nenhum EXE foi liberado nesta documentação. A amostra pública de Sinop não é o KML da Fazenda Maria Eduarda. A leitura SAR ao dashboard foi demonstrada em amostra de Sinop e KML de teste Tapajós; não significa homologação de campo.
