# Enform Verde v3.26.47-PRECAMPO-EXPERIMENTAL

## Altura SAR e carbono

- A busca de altura SAR passa a ter prioridade explícita em todas as AOIs brasileiras e inclui os seis biomas.
- Quando há pixels válidos ESA BIOMASS FH e a geometria tem suporte horizontal e domínio de calibração Tapajós compatíveis, a estimativa H100 × área basal passa a alimentar o carbono principal. A AGB oficial BIOMASS permanece registrada como comparação independente.
- Fora do domínio local, altura e AGB continuam separadas; altura não compatível, ausência de pixels e falha técnica são reportadas sem converter retroespalhamento em metros.
- Downloads e extração dos produtos FH e AGB BIOMASS são reutilizados entre estratos durante a mesma análise. Estatísticas zonais ainda usam cada geometria de estrato.

## Limites e validação

- A equação H100 × G está implementada somente nos suportes publicados/cadastrados da FLONA Tapajós; a prioridade de busca nacional não significa cobertura nacional nem autoriza extrapolação da equação.
- O erro de validação do modelo estrutural não inclui erro de mensuração/transferência do produto FH; essas parcelas permanecem explicitadas separadamente.
- Build Windows, CI completa e validação privada da Fazenda Maria Eduarda não foram executados neste ambiente. Esta versão é candidata pré-campo experimental, não homologada.
- O carregamento automático de inventários para biodiversidade segue pendente; os resultados dependem de CSV fitossociológico licenciado compatível por bioma, fitofisionomia e microrregião.
