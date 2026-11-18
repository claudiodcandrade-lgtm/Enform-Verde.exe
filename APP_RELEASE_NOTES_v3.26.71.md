# Enform Verde v3.26.71-PRECAMPO-EXPERIMENTAL

## Correção do aceite Windows para FH

- O aceite compilado Windows falhava em FH no Tapajós porque o passo EXE não recebia o segredo `ESA_MAAP_OFFLINE_TOKEN`; a prova MAAP separada e o live Linux tinham acesso à credencial. A ausência de token era falha de configuração de autenticação, nunca prova de ausência de cenas.
- O passo de aceite da pasta limpa do EXE agora recebe a credencial pelo ambiente de execução. O pipeline resolve token explícito primeiro e usa a variável protegida como fallback.
- Teste cobre a precedência do token explicitamente fornecido e o uso da variável de ambiente quando o chamador não fornece token.
- Também atualiza a trilha de auditoria live para apresentar altura FH/GTDX separada do AGB CCI e enumerar as rotas/fontes de inventário consultadas e compatíveis.

## Status

Candidata experimental/pré-campo. Build Windows, suíte integral, handoff SAR live e autoteste EXE em pasta limpa passaram no SHA `f874140edebbe35ae503de91942a0e7fc3344f42`. A prova confirma imagem óptica até o canvas e leitura FH real; detalhes e ressalva de auditoria estão abaixo.


## Fechamento dos gates do runner — 18/11/2026

- O SHA `f874140edebbe35ae503de91942a0e7fc3344f42` passou no build Windows, autoteste compilado em pasta limpa, suíte integral (1.285 testes), handoff SAR live Sinop/Tapajós e prova FH ESA. A prévia óptica Tapajós, cobertura nacional de pixels ópticos e smoke worker→canvas Tk em Sinop passaram. O fallback Sentinel-1 RTC em locais dos seis biomas passou.
- FH `FP_FH__L2A` foi lido no handoff live: 333 pixels florestais válidos em Sinop e 1.263 no KML de teste do Tapajós. AGB CCI foi registrada separadamente; comparação com inventários amplos foi N/D por não haver correspondência exata elegível nessas classes/AOIs de teste.
- Ressalva de auditoria: o EXE compilado leu 1.512 pixels FH válidos em um candidato no Tapajós, mas seu resumo de aceitação deixou `priority_height_route_status` e `priority_height_route_gate` nulos. O handoff dashboard independente reportou H100 processado. Corrigir e fazer o autoteste exigir estado/proveniência FH antes de declarar auditoria completa.
- Disponível como pacote experimental/pré-campo; a homologação científica continua bloqueada pela falta de validação independente de campo. O teste não usou a geometria privada da Fazenda Maria Eduarda.
- SHA-256 do `Enform Verde.exe`: `10171e9a27c9124ecaedee477ae6eccf5c092831e39a189f65bea109b125e4b5`. Digest do ZIP: `sha256:6a9b88d8c6aa55ead7728495f0d245a1cf6786585bf217c9da9531fd42d06894`.
