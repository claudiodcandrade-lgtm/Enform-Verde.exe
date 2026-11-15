# V88.08 — correção do escopo das provas em caixa de teste (12/11/2026)

## Correção explícita de interpretação
- Corrigindo V88.07: o workflow de classificação SAR não processou o KML da Fazenda Maria Eduarda. `tools/live_sinop_semantic_sar.py` construiu uma caixa fixa de teste `box(-55.205498, -11.887667, -55.175498, -11.857667)` e declara `NOT original KML`. Os valores observados em V88.07 (1.692 pixels, 3 cenas; 1.084,73 ha da caixa; 1.079,26 ha de polígonos e 5,47 ha sem classe) pertencem exclusivamente a essa caixa e não representam parcela ou porcentagem processada da fazenda.
- A checagem ESA MAAP usou outra caixa retangular `--bbox -55.21 -11.89 -55.17 -11.85`, não o perímetro da fazenda. `FH_PIXELS_READ`, 2.304 pixels e média 18,284 m provam acesso a pixels do produto FH no retângulo regional; a média não é estimativa da altura do dossel dentro do imóvel.
- Para impedir a repetição dessa leitura equivocada, o relatório SAR renomeia seus campos para `sample_box_*` e explicita `reference_farm_area_ha_not_processed`. Foi adicionado teste automático garantindo que os campos ambíguos antigos não voltem.

## Estado do produto
- As evidências V88.07 comprovam que o caminho CI consegue obter/processar pixels reais Sentinel-1 RTC numa caixa experimental próxima a Sinop, e que o endpoint/produto ESA FH retorna pixels numa caixa próxima. Não provam ingestão da geometria real nem que os pixels chegam ao dashboard.
- O run dashboard V88.07 passou 1.084 testes em 147,606 s, compilação integral e sincronização documental. O SAR executado está fora do dashboard e usa caixa amostral; o gate científico foi reprovado.
- Não declarar resolvidos o KML completo da fazenda, a abertura óptica na geometria real, a integração visual SAR, a altura do imóvel, carbono ou monitoramento agrícola de ponta a ponta. Os valores do teste em caixa não são resultados da propriedade.

