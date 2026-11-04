# REVISÃO V69 — PRESERVAÇÃO DA HIERARQUIA SAR E CONTRATO DE FITOFISIONOMIA IBGE — 04/11/2026

## Correção do último bloqueio de regressão
- A suíte de testes do commit d1a0e29a reprovou exclusivamente a expressão do campo `priority` em `land_use_sar.py`; `test_land_use_sar.LandUseTests.test_validated_sar_crop_precedes_mapbiomas_crop_layer` exigia `IBGE legenda_1 apenas nomeia fitofisionomia em interseção natural compatível`, removido durante a atualização do painel.
- Commit b5a142460ae11ae853e449dd6642832917ca5a1b restabelece literalmente essa frase e mantém a prioridade: classificador SAR recente ELEGÍVEL > MapBiomas C11 2025 como referência HISTÓRICA em lacunas > IBGE apenas denomina a fitofisionomia natural na interseção.
- O teste foi corrigido sem rebaixar o rigor: `SAR_NAO_VALIDADO` e `N/D_SEM_MODELO_EXECUTAVEL_VALIDADO` não são classificados como safra atual. Nenhum mapa de área agrícola recebe validação SAR por ser histórico.
- As rotas `sar_crop_live_probe.py`, `crop_monitoring_forecast.py` e `crop_vigor_auto.py` publicadas na v68 devem permanecer integradas, com sondagem de pixel SAR real e erro explicativo quando inexiste classificador calibrado.
- Biblioteca `international_crop_model_sources.py` documenta ESA WorldCereal, agroimpacts, WorldCereal RDM, Radiant MLHub e EuroCropsML; prova documental não equivale a modelo instalado e validado em Sinop.
- Catálogo nacional de serrapilheira, estoque de carbono nativo, solo PronaSolos 0–100 cm, delimitação de AOI e cálculos tC/tCO2e permanecem protegidos contra regressões.

## Critérios para disponibilização
1. Rodar todas as regressões no SHA final com zero falhas.
2. Compilar Windows no mesmo SHA, executar autoteste do EXE em pasta limpa, registrar SHA/checksum e publicar ZIP com link verificável.
3. Disponibilizar prompt e especificação técnica atualizados sem afirmar homologação científica independente enquanto faltam dados observacionais.
4. Homologação de identificador nominal SAR por cultura permanece PENDENTE até pesos treinados, classes compatíveis, cenas reais, licenças e validação regional independente; piloto experimental de sondagem SAR pode ser liberado separadamente.
