# V88.43 — integridade do par SAR e status operacional (13/11/2026)

Uma leitura isolada de VV podia ser registrada como processamento SAR concluído mesmo quando a leitura VH da mesma aquisição falhava. A rota MPC agora publica resultados completos somente quando VV e VH são lidos da mesma cena; leituras parciais ficam separadas em `partial_stats`/`partial_paths`, com estado `VV_VH_PAIR_INCOMPLETE`, e `available=false`. Isso impede que o dashboard ou os módulos seguintes interpretem uma polarização isolada como par SAR processado.

O teste `test_mpc_single_polarization_is_partial_not_processed` reproduz falha de VH após VV válido. Verificação local concluída: 1.145 testes passaram, 1 foi ignorado por ausência de display; a coleta inspecionou 168 módulos. O contrato do assinador MPC também foi ajustado para exercer até três tentativas transitórias; o teste de 429 agora comprova limite de três chamadas e encerramento fechado. Nenhuma tentativa ignora TLS, Retry-After ou limites configurados.

A candidata é `3.26.29-PRECAMPO-EXPERIMENTAL`. O ensaio local mede contratos, não demonstra conectividade remota. Catálogo encontrado não equivale a pixels decodificados: só declarar acesso operacional após leitura VV/VH real, recente (≤30 dias) e auditada no SHA final. A cobertura amostral em oito AOIs distribuídas nos seis biomas não é garantia para toda coordenada/época do Brasil; cada AOI deve preservar N/D/ERRO quando aplicável.

A atualização do prompt, da especificação de solo e da especificação técnica registra o estado de testes, build Windows, leitura live e ensaio do KML como gates independentes. A checagem visual local não pôde abrir Tk por falta de display; requer CI/Windows. Não declarar homologação científica sem validação observacional independente.
