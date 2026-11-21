# Enform Verde v3.26.80-PRECAMPO-EXPERIMENTAL

## Correções desta candidata

- O resumo fitossociológico IFN para até 100 unidades amostrais agora agrega os registros selecionados em uma única consulta SQLite, em vez de executar uma consulta por unidade. Mantém a mesma seleção espacial e os mesmos indicadores de frequência, abundância, DAP, altura, área basal e classes diamétricas.
- Acrescenta regressão que exige uma única consulta agregada para a rota compacta de biodiversidade e compara seus números com a leitura detalhada.
- O autoteste do EXE agora identifica cada subprocesso (`ui-smoke`, `module-check`, `visual-check`, `network-check`, `tapajos-acceptance`) e interrompe uma etapa que exceda seu limite. Um runner preso não fica mais sem diagnóstico por tempo indefinido.
- Mantém a validação IFN por manifesto e a seleção espacial indexada; nenhuma leitura integral do banco é feita por consulta.

## Estado

Candidata experimental. FH real em Sinop e handoff FH/AGB até o payload do dashboard passaram na candidata anterior. A conclusão do EXE limpo da v3.26.79 permaneceu presa no autoteste por mais de 25 minutos, sem expor qual subprocesso estava aguardando. A v3.26.80 melhora a consulta fitossociológica e adiciona limites/identificação de etapa para localizar esse bloqueio.

**Correção do gate GUI (19/11/2026):** o teste de upload GeoJSON verificava a confirmação imediatamente, embora `pick_vector()` leia em worker e atualize a interface por fila. O gate agora aguarda um estado terminal para KMZ e GeoJSON, com limite de 30 s, e verifica o polígono renderizado. A falha registrada foi uma corrida no teste, não uma reprodução confirmada de congelamento geral do programa. O build/autoteste Windows deve passar novamente antes de disponibilizar o pacote desta candidata.

**Correção documental:** uma repetição da sincronização Word não reconhecia o rótulo da própria capa V88.170. O atualizador agora aceita esse prefixo e tem regressão específica de reexecução. A sincronização V88.170 passou no run `44576920853`; capa, versão, baseline, HEAD, controle de SHA, histórico e rodapé foram atualizados e o DOCX foi validado como ZIP íntegro no commit `6ceadd82be7ef0b098e0e38f03a05f04f9a32fc8`.

Os sincronizadores Word históricos também observavam o arquivo utilitário compartilhado e iniciaram commits concorrentes para versões antigas. Seus gatilhos foram limitados aos próprios arquivos de checkpoint; somente a V88.170 observa agora o utilitário. Isso evita que uma atualização histórica concorra com a documentação desta candidata.

**Gate Windows no SHA `37b54b23` — falhas de contrato corrigidas em `2fc7c64`:** as verificações live ópticas, o worker até o canvas em Sinop, SAR público, FH+inventários até o dashboard, IFN e GUI passaram. A compilação foi interrompida por duas asserções de aceite desatualizadas: uma esperava um rótulo IBGE antigo, e outra esperava “pixels SAR” em vez do motivo atual de rotas SAR incompletas. Os contratos agora conferem os rótulos/condições semânticas vigentes e têm regressão local. No novo run `44581942105`, source self-test, FH/dashboard, IFN, estratificação, fallback Pantanal, GUI e preview Sentinel-2 já passaram; pixels ópticos live e EXE limpo seguem pendentes. Não liberar o ZIP até esses gates concluírem no mesmo SHA.

**Documentação atualizada:** a repetição Word do checkpoint V88.170 passou no run `44585670591`; todos os campos da capa/controle/histórico foram atualizados e o DOCX foi validado. Cópia sincronizada no commit `882eba445b48ba9470846939e06c860b847f02f6`. O novo build final deve partir do SHA pós-sincronização; este arquivo não constitui liberação do pacote.

O build Windows da candidata pós-sincronização, o autoteste em pasta limpa e o checksum ainda precisam concluir para gerar o pacote desta candidata. Homologação científica independente e validação de campo permanecem pendentes.

Uma segunda atualização do Word passou no run `44577483837`, com baseline, HEAD, data, SHA de controle, capa, versão, histórico e rodapé atualizados e DOCX íntegro. A cópia sincronizada está no commit `8faed8917e2a461cac9621f6d6990504c0e38256`. O próximo push dispara o build Windows contra esse estado documental.

## Reteste final da candidata 3.26.80 — 19/11/2026

O workflow Windows `44586180376` concluiu com sucesso no SHA `f82cf7f8541ebff07ef4d7ca66ac9c2470023430`. Passaram a regressão e os contratos de FH + inventários até o painel executivo renderizado, as verificações IFN, os gates SAR/BIOMASS live aplicáveis, o preview Sentinel-2, os pixels ópticos reais em biomas e extremos brasileiros e o worker óptico até o canvas Tk em Sinop. A compilação do EXE e o autoteste em cópia limpa também passaram; o artefato Windows foi criado.

Artefato: `Enform-Verde-Windows-v3.26.80-PRECAMPO-EXPERIMENTAL` (271.306.574 bytes; SHA-256 do ZIP `fff87b8d440406e450ac191fc51ced27e243002233cd3ddff70ad6bee173186b`). Download no workflow: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/44586180376 . O checksum identifica o arquivo ZIP do artefato publicado pelo Actions. O build foi produzido na branch de trabalho ligada ao PR #51; o PR continua em rascunho e não foi mesclado nem publicado como release em main.

**Limites de interpretação:** a prova óptica live confirma a rota Sentinel-2 testada, inclusive leitura real e desenho no canvas em Sinop; não é prova de que a rota CBERS-4A tenha sido validada. O autoteste limpo passou, mas não reproduziu todos os cenários de congelamento relatados em uso; portanto registra-se o problema de bloqueio no autoteste anterior como diagnosticado e protegido por limites/identificação de subprocessos, sem afirmar eliminação universal de congelamentos. A estimativa FH + balizas horizontais de inventários pertinentes chegou ao dashboard no contrato de integração; as balizas podem ser agregadas e multifonte, preservando compatibilidade regional/fitofisionômica, origem e incerteza. A homologação científica independente e a validação de campo permanecem pendentes; resultados continuam experimentais.
