# Prompt de continuidade — Enform Verde V88.73

Use como fonte de continuidade a revisão arquitetural docs/ARCHITECTURE_REVIEW_V88_73.md e o código candidato 3.26.42.

## Objetivo
Completar a separação entre resultados anuais e atuais, eliminar as causas de tela preta e leitura SAR lenta, e entregar relatórios claros sem extrapolar áreas ou ocultar estimativas parciais.

## Regras de execução
1. Não declare versão concluída apenas porque testes unitários ou workflow parcial passaram. Inspecione o status de todos os jobs no SHA exato.
2. Teste captura real de pixels no canvas Windows; metadados e existência de item Tk não provam imagem visível.
3. Trate LEM+ 2025/26 como mapa sazonal anual. Não misture sua área com candidatos Sentinel-1 de 150 dias, não chame essa máscara de cobertura atual e não permita que ela desative a rota de contingência atual.
4. Mantenha mapa anual, monitoramento atual, candidatos orbitais e contingência como produtos separados, com período e estado próprios.
5. Mostre cada compartimento de carbono por área quantificada e cobertura (ha/%); não extrapole. Mantenha estoque total parcial/N/D enquanto faltar área ou compartimento e declare “incerteza não mensurável” quando aplicável.
6. Limite leituras SAR redundantes e imponha orçamento temporal por cena/AOI; registre descoberta, autorização, leitura, processamento e renderização. N/D e erro técnico permanecem distintos.
7. CBERS/Sentinel-2 são fundos visuais. Se falharem, desenhe a camada IBGE potencial já disponível e o perímetro, indicando imagem óptica indisponível. Se a camada IBGE não estiver carregada, exiba o mapa de contingência AOI claramente. Nunca deixe painel preto nem trate o fundo como dado analítico.
8. Não reivindique validação em campo/nacional sem evidência externa. Teste o KML privado da Fazenda Maria Eduarda quando puder ser executado em ambiente Windows; fixture pública Sinop não o substitui.

## Gates de encerramento
- Suíte integral e regressões novas no commit final.
- Smoke live óptico avaliando pixels reais do canvas.
- Smokes SAR e build Windows verdes no mesmo SHA.
- Relatórios Tapajós e Maria Eduarda sem mistura temporal e com cobertura parcial exibida.
- Evidência reproduzível de duração total e por estágio.

Enquanto algum gate faltar, registrar como candidata pré-campo e enumerar pendências concretas, sem afirmar resolução definitiva.
