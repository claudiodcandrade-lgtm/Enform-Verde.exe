# V87.44 — branch 3.26.6 publicada; build pendente (08/11/2026)

## Registro de publicação
- A branch `patches-3.26.6` foi publicada no repositório `claudiodcandrade-lgtm/Enform-Verde.exe`. HEAD da versão de código publicado antes desta sincronização documental: `d92a91371007b2adb7bf0c6839197f610298e33c`. A integração gravou a sequência de seis commits da linha V87.39–V87.43; os SHAs remotos diferem dos hashes locais por terem sido recriados via API.
- O blob do módulo `terraclass_sar_experiment.py` e o DOCX completo foram comparados entre remoto e local e coincidem. Branch principal inalterada.
- O status combinado do GitHub não apresenta verificações para esse commit. Build Windows, autoteste do executável com `--network-check` e ZIP não foram executados nem publicados. Portanto esta é uma atualização da branch e da documentação, não uma liberação de EXE.

## Estado científico e política de dados
Modelos e dados testados e homologados têm prioridade quando compatíveis com local, período e sensor. PRODES/TerraClass é contingência experimental opt-in; concordância com mapa não é validação de campo, não distingue culturas individuais e ainda não foi treinado com dados reais nesta branch nem integrado à inferência padrão. Fora de domínios sustentados, retornar N/D com motivo. O gate científico independente permanece fail-closed.

## Próximos gates para liberação
Confirmar workflows de regressão, compilar o Windows no mesmo SHA, executar `--network-check` com pixels reais e TLS verificado, validar o executável em pasta limpa e gerar ZIP com hash publicado. Não afirmar operação nacional homologada nem liberar artefato antes desses resultados.
