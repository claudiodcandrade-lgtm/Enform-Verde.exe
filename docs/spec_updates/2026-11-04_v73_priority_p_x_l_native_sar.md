# ADENDO À ESPECIFICAÇÃO TÉCNICA — REVISÃO V73
**Enform Verde 3.26.0-SOLO-SAFRA — 04/11/2026 (UTC−3)**

Este adendo atualiza a hierarquia de sensores para identificação de estrutura e estimativa de altura de vegetação nativa, especifica as condições de uso dos modelos experimentais X/L e delimita o status comprovado. Deve ser lido em conjunto com a especificação técnica completa v72.

## 1. Hierarquia dos dados de altura e estrutura

| Ordem | Fonte | Uso autorizado |
|---|---|---|
| 1 | ESA BIOMASS banda P, produto oficial de altura/estrutura (quando disponível) | Fonte prioritária de altura física; preservar produto, unidade, máscara, incerteza e data de aquisição. |
| 1 | Cenas SAR recentes elegíveis, com P-band quando disponível e Sentinel-1 recente | Prioridade para observação atual. Sentinel-1 VV/VH mede retroespalhamento e fornece covariáveis de textura/estrutura e contexto temporal; não é medida direta de altura. |
| 2 | Banda X | Fallback para altura/estrutura quando a rota prioritária P-band ESA/SAR recente estiver indisponível para a AOI e houver cena/processamento compatível. |
| 3 | Banda L | Último fallback, permitido apenas quando também não houver X utilizável. |

A aplicação registra indisponibilidade por AOI, fonte, produto/cena, timestamp, resolução, pixels válidos e motivo de fallback. Disponibilidade é avaliada por cobertura efetiva e pixels válidos, não apenas por resposta do catálogo. Se requisitos não forem atendidos, o resultado será N/D com motivo.

## 2. Modelo experimental para X/L

O módulo contém funções de calibração por regressão linear e predição com incerteza observada out-of-fold por grupos espaciais. O módulo é experimental e ainda requer integração explícita ao pipeline de AOI/GUI, cenas SAR reais, preditores extraídos de pixels e pares parcela–pixel de campo. Não se deve descrever como operacional integrado enquanto esses itens não estiverem demonstrados.

### Requisitos mínimos de calibração e rastreabilidade

- Rótulos de altura oriundos de observações independentes de campo, com definição consistente (ex.: H100), fonte, URL/licença e SHA-256.
- Amostras do mesmo produto SAR e processamento/resolução por ajuste; mesmo bioma, fitofisionomia e região declarados.
- Erro de co-registro parcela–pixel ≤ 0,5 do tamanho de pixel.
- Diferença absoluta entre data de campo e aquisição SAR ≤ 365 dias, com justificativa fenológica/ecológica para a janela aplicada.
- Pelo menos cinco grupos espaciais independentes; separar por grupo na validação cruzada. Validação espacial out-of-fold é evidência de desenvolvimento, não substitui holdout externo independente.
- Registrar preditores, unidades, coeficientes, domínio mínimo/máximo, número de parcelas/grupos, datas, produto, versão do código e hashes.

A saída deve apresentar estimativa em metros, RMSE, MAE, viés, R², quantis 5–95% dos resíduos out-of-fold e o domínio de aplicação. O intervalo residual não deve ser chamado de intervalo de confiança de 95% sem calibração de cobertura demonstrada. Fora do domínio de calibração, com falta de incerteza, georreferenciamento insuficiente, janela temporal excedida ou fonte não verificável, retornar N/D.

## 3. Identificação de vegetação nativa via SAR

Texturas locais de VV/VH, estatísticas de retroespalhamento, granulometria/rugosidade de imagem e ausência de padrões geométricos regulares são variáveis candidatas para um classificador. Elas não constituem, sozinhas, confirmação de vegetação nativa. A classificação operacional exige treinamento com rótulos atuais independentes, separação espacial/temporal, matriz de confusão e métricas por bioma/fitofisionomia, além de integração no fluxo da AOI.

MapBiomas pode apoiar contexto histórico ou rótulos auxiliares explicitamente identificados; não substitui a observação SAR recente nem prova cobertura atual. A legenda oficial de fitofisionomias do IBGE serve para atribuir nomes às classes interceptadas ou próximas da AOI, com método de proximidade, distância e classe de origem expostos. Essa atribuição cartográfica não é identificação SAR.

## 4. Separação de produtos e estados

Manter resultados separados para: (a) presença de vegetação nativa; (b) classe fitofisionômica atribuída pelo IBGE; (c) altura do dossel; (d) AGB. Não inferir altura diretamente de Sentinel-1 C-band nem AGB sem modelo e validação compatíveis. O sistema distingue EXPERIMENTAL, N/D, FALLBACK_CARTOGRAFICO e operacional validado, com evidência, incerteza e limites visíveis.

## 5. Evidência atual e pendências

No HEAD e29da330d0b334568951da247e4ced34edf8bb9e, o contrato X/L foi reforçado para exigir QA espacial e temporal e correspondência de bioma/região/fitofisionomia. Os testes associados usam dados sintéticos e verificam regras de contrato; não demonstram acurácia de altura nem validação científica independente. No momento desta revisão, os workflows de testes do dashboard e compilação Windows estavam em execução; o gate independente de homologação científica havia falhado por ausência de evidências observacionais reais. Confirmar estados e artefato antes de qualquer anúncio de release.

**Conclusão de status:** a lógica experimental de calibração/predição está disponível no código, porém falta integração ao pipeline de AOI/GUI e demonstração com dados reais. A identificação SAR de vegetação nativa também não deve ser considerada plenamente operacional até integração e validação independente. A prioridade P/X e o fallback L descritos são requisitos de implementação e divulgação, não uma alegação de homologação concluída.
