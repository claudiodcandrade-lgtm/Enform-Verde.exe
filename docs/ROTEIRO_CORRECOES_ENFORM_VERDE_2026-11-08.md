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
- **B5 — Decisão pendente do proprietário:** critério de aceite do classificador (hoje n ≥ 30 e limite inferior Wilson ≥ 0,70 por classe vs. regra anterior “sem acurácia mínima”).

## C. Fundo óptico
- ✅ CBERS-4A/WFI primeiro (BAND15/14/13 + CMASK), Sentinel-2 só como contingência com a falha exibida. Aceite: `--network-check` lê pixels CBERS em Sinop.

## D. Carbono
- **D1 — Quadro executivo.** Uma linha por compartimento (tC/ha, tCO2e/ha, incerteza tCO2e/ha e %) e total; incerteza total só por propagação estatística (covariância/Monte Carlo com correlações declaradas), nunca soma simples. Aceite: teste com casos independentes e correlacionados.
- ✅ **D2 — Serapilheira FESV (norte de MT)** hierárquica com erro de transferência quantificado. Próximo: ampliar sítios gravimétricos por fitofisionomia; IFN só com modelo massa/espessura calibrado.
- **D3 — Necromassa e raízes** com a mesma lógica hierárquica (sítios independentes, τ entre sítios).
- Solo 0–100 cm: interseção exata com mapas Embrapa (mantido); validação aguarda dados independentes (pedidos SFB/Embrapa).

## E. Agricultura (identificação, vigor, previsão)
- **E1 — Identificador SAR de culturas** instalado e validado (hierarquia Brasil → CIRAD → internacional; candidatos INPE, JECAM, WorldCereal, CropHarvest). Sem ele: “cultura não identificada”.
- **E2 — Altura de plantas validada** (modelo SAR por cultura/estádio/região ou fonte estrutural), requisito do vigor combinado.
- **E3 — Vigor em 3 classes** (altura, uniformidade, rugosidade) com probabilidades por bootstrap e referência de talhões SAR validados.
- **E4 — Séries PAM longas.** SIDRA 5457 tem dados desde 1974 (verificado); recalibrar o painel com ≥ 30 anos (ex.: 1990–2024; NASA POWER diário desde 1981) e quebras estruturais. Hoje só 2015–2024.
- **E5 — Calendário ZARC por município** e separação milho 1ª/2ª safra.
- **E6 — Termo de calor na floração** no índice climático.
- Aceite geral: hindcast deixando um ano de fora com ganho sobre a tendência, por cultura e região, publicado junto com a previsão.

## F. Validação científica (gate)
- Pedidos institucionais (SFB, Embrapa, MapBiomas) enviados; ferramenta de validação do solo pronta; nada promovido a `validated` sem dados independentes reais.
