# V88.06 — paridade do runtime em todos os workflows (12/11/2026)

## Falha detectada e correção
- O workflow live `sinop-sar-experimental-live.yml` instalava `scikit-learn` sem versão; o `dashboard-dual-tests.yml` aceitava qualquer versão `>=1.4,<2`. No commit `09b88b48c84b65efbd57c72f586d525f669706fe`, o teste live falhou de forma segura antes da classificação: o manifesto exige 1.8.0 e o ambiente instalou 1.9.1 (`VERSAO_SKLEARN_INCOMPATIVEL`).
- Ambos os instaladores agora fixam `scikit-learn==1.8.0`, alinhados ao `requirements_desktop.txt` e ao modelo serializado.
- Adicionado contrato que compara as versões fixadas pelos requisitos e pelos workflows live/dashboard. A recusa explícita no loader permanece como segunda barreira contra divergência.

## Verificação local e estado de integração
- Contrato de paridade e testes do loader: 3 aprovados. Suíte completa após a correção: 1.084 testes executados, 1 ignorado, sem falhas; coleta/importação: 158 módulos.
- Esses resultados são locais. As execuções GitHub Actions precisam ser refeitas no novo SHA; logs e artefatos do commit anterior não provam esta correção.
- A versão 3.26.20 continua sem EXE validado. A imagem óptica no KML integral, o dashboard da fazenda e a estimativa de altura/carbono permanecem pendentes de prova Windows.
