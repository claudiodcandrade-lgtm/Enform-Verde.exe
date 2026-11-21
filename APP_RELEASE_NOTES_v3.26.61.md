# Enform Verde v3.26.61-PRECAMPO-EXPERIMENTAL

## Registro V88.124 — apresentação e rolagem de resultados

Data: 16/11/2026
Versão de aplicativo: 3.26.61-PRECAMPO-EXPERIMENTAL

## Ajustes de interface

- As abas Monitoramento de áreas cultivadas e Balanço de compartimentos passam a ter rolagem vertical da página inteira, além das barras internas dos relatórios. Isso permite alcançar cabeçalhos, cartões e abas de resultado em telas menores.
- O relatório de carbono troca a tabela larga por linhas que se ajustam à largura do painel.
- Cada compartimento mostra estoque conhecido (tC e tCO₂e), densidade na área quantificada, cobertura e incerteza disponível.
- A soma dos estoques conhecidos é exibida explicitamente. Se faltarem compartimentos ou cobertura, o texto marca a soma como parcial e mantém densidade/total completo como N/D quando não defensáveis. Dados ausentes e cenários experimentais não são tratados como zero nem incluídos no total conhecido.

## Verificação

Foi incluído teste de regressão da exibição da soma parcial. A execução local de testes e do verificador não estava disponível neste ambiente; o commit deve ser verificado pelo workflow Windows. Resultado ainda experimental, sem alterar o gate de homologação científica.
