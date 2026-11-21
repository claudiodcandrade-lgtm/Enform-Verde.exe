# Enform Verde v3.26.41-PRECAMPO-EXPERIMENTAL

## Correções sobre a 3.26.40

- Corrige o relatório de monitoramento para não exibir mensagens de ausência de classificador depois que o LEM+ embarcado aplicou máscaras SAR experimentais. Diagnósticos de modelos externos instalados permanecem separados do modelo embarcado.
- Mantém explícito que as classes SAR são experimentais, sem validação local de campo; se nenhuma classificação semântica for aplicada, mantém N/D e informa a contingência acionada.
- A versão 3.26.40 já comprovou em CI a leitura óptica CBERS-4A em 11 pontos nacionais, o envio da imagem real ao canvas Tk em Sinop e o handoff SAR real até uso do solo/carbono/dashboard em Sinop amostral e Tapajós. O smoke Windows teve correção de fixture sintético e deverá ser repetido nesta versão.
- A regressão nova cobre o caso que gerou a contradição: ausência de modelo instalado em diretório externo junto com aplicação do LEM+ embarcado.

## Estado e limites

- Testes direcionados: 44 aprovados. Suíte integral local: 1.170 aprovados, 1 ignorado. CI, build Windows, canvas, SAR nacional e handoff ponta a ponta ainda devem passar no SHA final 3.26.41.
- A AOI integral privada da Fazenda Maria Eduarda permanece fora dos artefatos públicos; o teste nacional usa janela amostral centrada nas coordenadas informadas. Executar o KML integral em ambiente controlado antes de declarar aceite da fazenda.
- Carbono permanece parcial quando necromassa/serapilheira, transferência ou IC total não forem mensuráveis; apresentar explicitamente “incerteza não mensurável” onde aplicável. Classificação experimental não equivale a validação científica.
