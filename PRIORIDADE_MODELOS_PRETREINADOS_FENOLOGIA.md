# Prioridade: classificadores agrícolas pré-treinados e fenologia

Atualização 24/10/2026. Exigir pesos acessíveis, licença, sensor compatível, classes, estágio, região, avaliação independente e teste no Brasil. NÃO afirmar que modelo identifica todas as fases sem evidência.

## Candidatos documentados
1. agroimpacts/croptypemapper — código de TCN/LSTM para séries Sentinel-1 + Sentinel-2, notebook com inferência de modelo pré-treinado, mas requer parâmetros e imagens adequados. https://github.com/agroimpacts/croptypemapper . Prioridade alta para avaliação SAR temporal; verificar disponibilidade/licença dos pesos e classes.
2. kavayam/s2-phenocnn — pesos publicados, CNN dupla para milho/arroz/soja; fases fenológicas explicitamente previstas para arroz (7 estágios), NÃO para todas as culturas. Sentinel-2, não SAR. https://huggingface.co/kavayam/s2-phenocnn . Prioridade alta como complemento óptico; verificar validade local.
3. STMA — método espaço-temporal SAR com código indicado pelos autores; dados Brandenburg e outros domínios; não assumir pesos treinados prontos ou validade no Brasil. DOI 10.1016/j.isprsjprs.2023.11.016.
4. Tsuchiya & Sonobe (2025) — TCN com atenção e Sentinel-1, classes incluem feijão e milho; demonstra arquitetura, não pesos brasileiros prontos. DOI 10.3390/rs17122095.
5. TempTL_S1 — transferência entre safras com Sentinel-1, código aberto e dados de referência com restrições; verificar pesos e licenças. https://github.com/milospandzic/TempTL_S1 .
6. CROPS (2026) — adaptação de domínio para soja em Brasil e outros países, Sentinel-2; avaliar código/pesos e evidência antes de integrar. https://www.sciencedirect.com/science/article/pii/S0924271626003254 .

## Matriz obrigatória de classes
soja, milho, sorgo, café, cana-de-açúcar, arroz, feijão, citros; adicionalmente pastagem, vegetação nativa e não determinada.
Para cada cultura exigir validação por fase: implantação/emergência, crescimento vegetativo, reprodutivo, maturação e pós-colheita quando aplicável; perenes (café/citros) requerem calendário próprio e indicadores de floração/frutificação, não ciclos anuais fictícios. Para arroz verificar inundação; para cana cortes/soqueiras.
Distinguir duas saídas: (1) tipo de cultura e (2) fase fenológica; ambas com probabilidades calibradas, data e status de validação independentes.
Modelos treinados com ciclo completo podem NÃO reconhecer com confiança no início da safra: medir curvas de desempenho por data relativa ao plantio e abster-se.
Fusão S1/S2 quando melhorar desempenho, com S1 para disponibilidade sob nuvens.
Critério de seleção: evidência reproduzível no domínio > pesos prontos > desempenho por fase > capacidade de atualização > custo computacional. Nenhum modelo estrangeiro recebe status de validado no Brasil sem teste independente local.
Não alterar AGB SAR, máscara de vegetação nativa, cálculos de carbono ou versão Windows funcional.
Estado: seleção e especificação, NÃO integração ou validação dos modelos.
