# Enform Verde v3.26.29-PRECAMPO-EXPERIMENTAL

## Correção de integridade do processamento Sentinel-1

- O pipeline agora só sinaliza processamento Sentinel-1 completo quando VV e VH foram lidos da mesma aquisição. Se uma polarização falhar, as leituras parciais e o erro ficam na auditoria, `available=false` e o estado é `VV_VH_PAIR_INCOMPLETE`.
- A rota de assinatura de ativos MPC repete falhas transitórias em até três chamadas, respeita `Retry-After` limitado, mantém TLS verificado e encerra sem promover pixels parciais.
- A auditoria e o dashboard continuam distinguindo pixel SAR, candidato experimental de uso da terra e estimativa quantitativa de carbono; C-band não gera AGB sozinho.
- Testes locais: 1.145 aprovados, 1 ignorado por ausência de display; coleta de 168 módulos. A primeira execução completa encontrou um desalinhamento no teste do limite de tentativas, que foi corrigido e a suíte passou na execução seguinte.

**Limites:** não houve leitura live bem-sucedida de VV/VH nesta sessão. O teste multiprovedor em oito AOIs dos seis biomas, os workflows/compilação Windows, o ensaio integral do KML da Fazenda Maria Eduarda e a validação científica independente permanecem pendentes. Os AOIs são amostras de cobertura e não prova de atendimento a cada localização do Brasil. A candidata segue pré-campo experimental e não homologada.
