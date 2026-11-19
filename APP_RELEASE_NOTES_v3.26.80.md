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

O build Windows da candidata pós-sincronização, o autoteste em pasta limpa e o checksum ainda precisam concluir para gerar o pacote desta candidata. Homologação científica independente e validação de campo permanecem pendentes.
