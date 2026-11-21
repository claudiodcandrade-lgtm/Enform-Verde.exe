# Enform Verde v3.26.66-PRECAMPO-EXPERIMENTAL

Candidata experimental para pré-campo. Esta revisão melhora a apresentação dos resultados agrícolas e preserva o resumo de vigor no quadro executivo após a atualização assíncrona do clima.

## Alterações

- Todos os relatórios apresentam quadro executivo no início, antes do conteúdo extenso, e mantêm a trilha de auditoria em área separada.
- O quadro agrícola mantém a classe/estado de vigor SAR por cultura e informa uso na previsão PAM×clima somente quando a auditoria do modelo declara `vigor_model_audit.used_in_yield_distribution=true`.
- A síntese por cultura inclui probabilidades de vigor, área e cobertura da amostra, data da aquisição e safra da máscara.
- Se os rótulos esperados de um resumo mudarem, o cartão mostra as primeiras linhas do resultado em vez de ficar vazio.
- Foram adicionados contratos automatizados para comprovar o uso do vigor, impedir inferência de uso a partir da classe isolada e preservar o diagnóstico quando não houver auditoria específica.

## Evidência experimental disponível

No teste live de Sinop, uma cena Sentinel‑1 RTC de 12/11/2026 produziu uma amostra de vigor de soja de aproximadamente 8 ha, com seis blocos de referência. A auditoria confirmou participação do vigor na distribuição PAM×clima. A amostra cobre 2,456% de uma máscara SAR retrospectiva da safra 2025/2026, e não confirma cultura atual nem transferência da área para a safra projetada. Café permaneceu N/D por não haver blocos elegíveis.

## Status de validação

Esta nota identifica a candidata 3.26.66 e não declara sua validação concluída. A regressão integral, o build Windows, o autoteste do EXE em pasta limpa e o handoff SAR devem passar no SHA da versão 3.26.66. Resultados de uma versão anterior não substituem esses gates. A homologação científica independente segue bloqueada enquanto não houver validação de campo independente. Não tratar esta candidata como versão cientificamente homologada.
