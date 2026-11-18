# Enform Verde v3.26.71-PRECAMPO-EXPERIMENTAL

## Correção do aceite Windows para FH

- O aceite compilado Windows falhava em FH no Tapajós porque o passo EXE não recebia o segredo `ESA_MAAP_OFFLINE_TOKEN`; a prova MAAP separada e o live Linux tinham acesso à credencial. A ausência de token era falha de configuração de autenticação, nunca prova de ausência de cenas.
- O passo de aceite da pasta limpa do EXE agora recebe a credencial pelo ambiente de execução. O pipeline resolve token explícito primeiro e usa a variável protegida como fallback.
- Teste cobre a precedência do token explicitamente fornecido e o uso da variável de ambiente quando o chamador não fornece token.
- Também atualiza a trilha de auditoria live para apresentar altura FH/GTDX separada do AGB CCI e enumerar as rotas/fontes de inventário consultadas e compatíveis.

## Status

Candidata experimental/pré-campo. Aguardam nova suíte integral, handoff live, build e autoteste do EXE no SHA final. A evidência anterior confirmou pixels FH no Tapajós e a imagem óptica no runner, mas o EXE daquela revisão não passou no aceite FH por falta de credencial. Não distribuir antes dos gates da 3.26.71.
