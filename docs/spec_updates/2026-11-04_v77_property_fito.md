# REVISÃO v77 — Fitofisionomia presente na propriedade (04/11/2026)
## Correções do painel e sintaxe
- Falha do CI v76: fechamento da string em ibge_area_summary_lines de desktop_app.py, corrigido na revisão v77.
- O painel Mapas e limites apresenta agora BIOMA e FITOFISIONOMIA PRESENTE NA PROPRIEDADE, com hectare e percentual da área total para cada classe nativa, a partir de native_carbon.strata (interseção de cobertura com o nome fitofisionômico IBGE).
- Antes do processamento de cobertura, a interface não exibe a área potencial do IBGE como presença atual; o diagnóstico IBGE potencial fica separado na auditoria.
- Exemplo do relatório da Fazenda Maria Eduarda: AOI 1.459,91 ha, área nativa mapeada no MapBiomas anual 917,81 ha (62,87%), não 100%. Somente declarar esta área para Floresta Estacional Sempre-Verde se todos os estratos nativos mapeados tiverem esse nome na interseção. Não é validação orbital da cobertura atual.
- Fórmula: área_fitofisionomia(ha) = soma áreas dos estratos nativos com mesma fitofisionomia; percentual_total = 100 * área_fitofisionomia / área_total_AOI.
- Fontes e qualidade explícitas: cartografia anual MapBiomas + nome IBGE, ou classificação SAR com nome IBGE. Nenhuma das duas equivale a confirmação independente em propriedade real. Falta de classificação resulta NÃO DETERMINADA, não 100% de floresta.
- Testes novos em tests/test_property_physiognomy_display.py verificam imóvel misto, 62,87%, fitofisionomias múltiplas, cobertura indeterminada e retorno N/D.
## Próximas verificações e versões
- Manter triagem SAR orbital experimental recente e alertas do classificador; não usar pixels candidatos para afirmar lavoura ou vegetação nativa sem modelo apropriado.
- Reexecutar toda a suíte e novo EXE em Windows no SHA final; build anterior do SHA 8839435 não contém estas mudanças.
- Gate científico independente continua reprovado até evidência observacional real. Modelos biomassa P/X/L continuam com hierarquia e limites originais.
