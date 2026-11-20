# Complemento de continuidade ao prompt V43 — V88.173 (20/11/2026)

O arquivo `PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md` neste checkout não está legível como texto (conteúdo binário, sem assinatura UTF-8/UTF-16 reconhecida); não foi sobrescrito para preservar o histórico. Use este checkpoint junto com o prompt canônico V52.

- Candidata `3.26.83-PRECAMPO-EXPERIMENTAL`: o mapa usa localmente os polígonos vetoriais de uso/cobertura e legenda classe/origem/área/percentual; não inicia busca de imagem óptica.
- O painel destaca soma conhecida de carbono em tC e tCO₂e, rotulada parcial quando incompleta. O Excel pergunta qual workbook exportar; carbono contém gráficos de tC e tCO₂e, monitoramento agrícola contém classe/área/origem e relatório de vigor/safra.
- Incerteza de biomassa entre estratos segue ρ=1 conservador; dispersão do solo é descritiva; sensibilidade parcial de raízes é separada da incerteza total.
- Relatório da Fazenda Maria Eduarda: IFN expandido consultado (5 UAs e 1.023 árvores), sem agregado publicado ou fonte externa pertinente associada à AOI; portanto não há evidência de calibração do CCI por inventários. ESA CCI v7 foi estimador de AGB (183,49 Mg/ha; incerteza de produto 63,62 Mg/ha). FH não entregou pixels válidos ao painel nessa execução, por erro técnico e leitura incompleta; ausência não foi demonstrada. FH real aprovado em Sinop não comprova o fluxo desta fazenda. Estoque conhecido 91.581,58 tC / 335.799,14 tCO₂e é parcial; incerteza total permanece N/D.
- Não declarar liberação de EXE até regressão integral, coleta de testes, build Windows, gates module/visual/network, teste em pasta limpa e integração visual/exportação no SHA final. A correção do congelamento não está provada para todos os cenários; homologação científica independente segue pendente.


## V88.175 — mapa temático local e gates de liberação (20/11/2026)

- O requisito de imagem óptica foi retirado do fluxo e dos gates de liberação conforme decisão do proprietário. O workflow não exige mais CBERS/Sentinel-2, cobertura óptica amostral nem renderização de imagem orbital no canvas.
- O gate GUI agora verifica a apresentação local dos polígonos de uso/cobertura com legenda de classe, área, percentual e origem, sem iniciar consulta óptica ao carregar a geometria. Permanecem obrigatórios os gates independentes de SAR, FH/AGB, inventários, painéis, Excel, responsividade, build Windows, verificações do EXE e autoteste em pasta limpa.
- A falha anterior `CBERS-first tiled optical-background contract missing` era uma asserção obsoleta, contraditória com a decisão de abandonar imagem óptica. A alteração corrige o critério de aceitação; não declara aprovada a versão nem altera resultados científicos.
- Os cinco testes locais `test_dashboard_release_features` passaram e o YAML do workflow foi interpretado. O coletor geral inspecionou 197 módulos, mas não passou por dependências ausentes neste runtime; a suíte integral ainda não foi executada novamente. A nova execução Windows precisa validar o mapa local, os demais gates e produzir o EXE antes da distribuição.
- A candidata permanece experimental. A validação científica independente de campo continua pendente.
