# Enform Verde v3.26.51-PRECAMPO-EXPERIMENTAL

## Alterações

- Incluídas rotas explícitas de previsão para todas as culturas prioritárias atuais e anteriores: soja, milho, arroz, algodão, sorgo, cana-de-açúcar, café, feijão e citros.
- Soja e milho mantêm o painel PAM + balanço hídrico já implementado. As demais culturas anuais/perenes recebem cenário exploratório PAM + clima + vigor, identificado como não calibrado por cultura.
- Algodão herbáceo foi acrescentado ao identificador, aos parâmetros climáticos e à consulta oficial SIDRA por microrregião quando não houver série empacotada.
- Pastagem, silvicultura, ILP, IPF e ILPF têm rotas de cálculo com unidades próprias, requisitos de entrada e incerteza explícita. Não são submetidos ao modelo de rendimento de grãos.
- O JSON de auditoria registra o contrato e os bloqueios de cada cultura/sistema; MapBiomas permanece referência histórica.
- Corrigida a ordenação operacional da base de inventários: microdados institucionais abertos (1), inventário institucional totalizado com erro publicado (2), medições verificadas em base pública oficial (3), inventário anexado explicitamente aceito pelo órgão (4), metadado de licenciamento (5) e registro privado sem aceite comprovado (6).

## Verificação local

1.221 testes do conjunto local passaram (1 skip esperado), incluindo o teste live de leitura real de Sentinel-1 VV/VH em Sinop. Na cena `S1D_IW_GRDH_1SDV_20261112T091635_20261112T091700_005432_00A5E9_rtc`, o teste leu 9 pixels VV e 9 VH válidos; medianas nativas: VV 0,143119 e VH 0,031320. O passo bloqueante para leitura live está incluído no workflow Windows. Os testes direcionados ILP/IPLF/cultivos também passaram (35 testes); `compileall`, guard documental e `git diff --check` passaram.

## Estado

Candidata experimental/pré-campo. A leitura live foi comprovada somente em um recorte pontual de Sinop; não prova máscara semântica, execução com o KML integral, passagem até todos os painéis nem cobertura nacional. Build Windows/CI remota, consulta live à SIDRA, validação independente de campo e homologação ainda pendem. Pastagens, silvicultura e sistemas integrados retornam N/D se medições de manejo/inventário não forem fornecidas. A série PAM empacotada ainda não contém algodão; a rota SIDRA exige conectividade para completar a microrregião.

## Correção de CI Windows — V88.94

A primeira CI Windows materializou 150.660 registros oficiais PAM/SIDRA e encontrou um teste que ainda fixava o total histórico de 133.920. O contrato de teste agora confere contagem, checksum e completude com os metadados da execução, mantendo validação de unicidade, produtos, anos e variáveis. Os dois testes focados passaram localmente. O novo build Windows, os smokes, o handoff SAR até os painéis e o executável ainda precisam passar no SHA corrigido antes da distribuição.
## Supressão de nomes de culturas fora do domínio — V88.95

A execução ponta a ponta real provou que o SAR alcançou os painéis em Sinop-amostra e Tapajós, mas expôs rótulos específicos de soja/café ainda presentes no Tapajós fora da área de treinamento. O bloqueio agora é aplicado aos pixels antes das classes e polígonos. Teste de integração incluído no gate Windows. A primeira rodada V88.94 não liberou executável por falha do teste de cardinalidade PAM; o novo build e a execução do teste de supressão ainda precisam passar. A amostra de Sinop não é o KML privado da Fazenda Maria Eduarda.
## Compatibilidade de teste Windows — V88.96

Corrigido o cleanup de uma conexão SQLite aberta pela fixture de teste. O resultado anterior passou 1.221 testes, mas falhou ao apagar o banco temporário bloqueado no Windows. A conexão agora é fechada explicitamente. É necessária nova suíte e novo build no SHA atualizado.
## Completa fixture de regressão SAR — V88.97

O teste geoespacial Windows recém-executado revelou métricas ausentes no fixture (`overall_accuracy` e intervalo Wilson), não no fluxo de classe. O fixture foi completado; a nova CI precisa provar que a supressão dos nomes fora do envelope chega tanto às classes como aos polígonos. O ambiente local não tem GeoPandas.
