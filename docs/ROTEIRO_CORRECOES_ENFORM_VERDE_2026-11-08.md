# Roteiro único de correções — Enform Verde (a partir de 3.26.6 / V87.40)

Objetivo: concluir as correções sem regressões. Cada item tem critério de aceite verificável. Itens marcados ✅ já estão no patch 3.26.6.

## A. Processo (causa das falhas recorrentes)
- **A1 — Um agente por branch.** Nunca dois assistentes enviando commits ao mesmo tempo. Trabalhos paralelos em branches separadas, integradas por PR.
- **A2 — Código e testes juntos.** Toda mudança de comportamento atualiza os testes no mesmo commit. Antes do push: `python -m unittest discover -s tests` e `python tools/check_test_collection.py` verdes. Causa direta da quebra de 24 testes em V87.37–V87.38.
- **A3 — Política só pelo proprietário.** Limiares científicos (ex.: n mínimo, precisão mínima) não são alterados por agente sem decisão registrada no prompt.
- **A4 — EXE só com prova.** Citar executável apenas com run verde, SHA do commit, SHA-256 do EXE e `--module-check`, `--visual-check`, `--network-check` aprovados.
- **A5 — Regras escritas para agentes.** `AGENTS.md` (Codex/ChatGPT) e `CLAUDE.md` com as regras deste roteiro.

## B. Leitura de dados orbitais e mapeamento atual
- ✅ **B1 — Certificados (causa raiz SAR/CBERS).** Aceite: no Windows do usuário, triagem SAR com cenas lidas e CBERS-4A visível; no build, `--network-check` aprovado.
- **B2 — Esgotar provedores SAR.** MPC → INPE RTC → demais configurados; N/D só após registrar falha de todos. Aceite: auditoria lista cada tentativa.
- **B3 — Classificador SAR semântico (nativa × cultivo × outros usos).** Sentinel-1 VV/VH temporal; rótulos independentes (LEM/Campo Verde INPE, JECAM CIRAD, parcelas IFN, campo); validação em blocos espaciais e temporais, matriz de confusão, precisão/recall por classe com IC95%. Aceite: modelo com SHA-256 e relatório; MapBiomas proibido como rótulo.
- **B4 — Nome da fitofisionomia.** Só após nativa confirmada por SAR: interseção com IBGE; sem sobreposição perfeita, vizinho mais próximo com distância informada.
- ✅ **B5 — Decidido (08/11/2026, resposta 2B):** qualquer acurácia MEDIDA é aceita como experimental, com n independente e IC95% Wilson obrigatórios; sem limiar mínimo.
- **B6 — Sempre haver um classificador SAR (resposta 8A, prioridade máxima):** instalar classificador SAR semântico treinado com rótulos independentes (não MapBiomas) para nativa × cultivo × outros usos, com acurácia medida; sem ele, unidades radar sem nome apenas no mapa e no painel, sem carbono nem safra.

## C. Fundo óptico
- ✅ CBERS-4A/WFI primeiro (BAND15/14/13 + CMASK), Sentinel-2 só como contingência com a falha exibida. Aceite: `--network-check` lê pixels CBERS em Sinop.

## D. Carbono
- **D1 — Quadro executivo.** Uma linha por compartimento (tC/ha, tCO2e/ha, incerteza tCO2e/ha e %) e total; incerteza total só por propagação estatística (covariância/Monte Carlo com correlações declaradas), nunca soma simples. Aceite: teste com casos independentes e correlacionados.
- ✅ **D2 — Serapilheira (resposta 6A):** estimativa hierárquica com erro de transferência medido entre sítios para TODAS as fitofisionomias florestais com ≥ 1 estudo gravimétrico verificado; classes não florestais seguem como cenário até haver ≥ 3 sítios independentes.
- ✅ **D1b — Incerteza total (resposta 7B):** biomassa aérea, raízes e necromassa com ρ = 1; serapilheira e solo independentes; N/D se algum compartimento não tiver incerteza.
- **D3 — Necromassa e raízes** com a mesma lógica hierárquica (sítios independentes, τ entre sítios).
- Solo 0–100 cm: interseção exata com mapas Embrapa (mantido); validação aguarda dados independentes (pedidos SFB/Embrapa).

## E. Agricultura (identificação, vigor, previsão)
- **E1 — Identificador SAR de culturas** instalado e validado (hierarquia Brasil → CIRAD → internacional; candidatos INPE, JECAM, WorldCereal, CropHarvest). Sem ele: “cultura não identificada”.
- ✅/**E2 — Altura (resposta 4B):** altura de modelo SAR PUBLICADO aceita como experimental com RMSE e n publicados e erro propagado (`validation_tier=experimental_published`); falta registrar um conjunto de coeficientes verificável por cultura (Prudente et al. 2019/INPE publica as relações só em figuras).
- **E3 — Vigor em 3 classes** (altura, uniformidade, rugosidade) com probabilidades por bootstrap e referência de talhões SAR validados.
- **E4 — Séries PAM (resposta 3C):** manter 2015–2024 por decisão do proprietário (SIDRA 5457 tem dados desde 1974 se a decisão mudar).
- ✅ **E7 — Previsão sem vigor (resposta 5B):** produzida só com clima + histórico PAM, rotulada “PREVISÃO SEM VIGOR”, intervalo de todos os erros históricos; máscara SAR da cultura continua obrigatória.
- ✅ **Modelo (resposta 1A):** painel calibrado (tendência + β·RY) com vigor posicionando no terço dos erros históricos.
- **E5 — Calendário ZARC por município** e separação milho 1ª/2ª safra.
- **E6 — Termo de calor na floração** no índice climático.
- Aceite geral: hindcast deixando um ano de fora com ganho sobre a tendência, por cultura e região, publicado junto com a previsão.

## F. Validação científica (gate)
- Pedidos institucionais (SFB, Embrapa, MapBiomas) enviados; ferramenta de validação do solo pronta; nada promovido a `validated` sem dados independentes reais.

## G. Decisão PRODES/TerraClass e ordem de uso (08/11/2026)
- O proprietário autorizou rótulos cartográficos oficiais para treinamento experimental. Módulo: `terraclass_sar_experiment.py`; comando: `tools/train_terraclass_sar_experiment.py`.
- A saída informa `EXPERIMENTAL_MAP_AGREEMENT_ONLY`, métricas por classe, n, blocos e hash. É concordância com TerraClass, nunca validação de campo. Treino exige raster SAR e mapa contemporâneos e apenas categorias amplas.
- Ordem operacional: (1) modelo/dado testado e homologado compatível; (2) contingência experimental com rótulo, domínio e incerteza; (3) N/D com motivo. O experimental nunca substitui um modelo homologado.
- TerraClass 2024 tem classes para Amazônia e Cerrado; não extrapolar para os demais biomas nem separar soja/milho. PRODES é camada de supressão primária, não classe de uso atual pós-supressão. Outros biomas permanecem N/D sem referência compatível.
- Altura/vigor: coeficientes publicados não estão instalados; não usar valores transferidos nem inferir altura de retroespalhamento sem modelo/erro/estádio compatíveis.
- A ferramenta é opt-in, não foi treinada em dados reais nesta alteração, não está integrada ao painel/inferência e não altera resultados padrão. Antes de promoção, executar em dados oficiais e SAR reais, revisar a matriz espacial e adicionar validação independente de campo.
