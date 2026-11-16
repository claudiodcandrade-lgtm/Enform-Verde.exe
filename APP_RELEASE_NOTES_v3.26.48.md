# Enform Verde v3.26.48 — pré-campo experimental

## Inventários florestais e indicador qualitativo de biodiversidade

- Adiciona catálogo nacional SQLite com 15 rotas institucionais e 57 registros catalográficos locais: 27 referências publicadas não harmonizadas, 27 registros candidatos de fontes/portais, um conjunto local de 30 resumos de parcelas do Tapajós e dois arquivos tabulares agregados/candidatos do IFN.
- Prioriza dados abertos de parcelas georreferenciadas da mesma fitofisionomia; dentro desse grupo, a distância orienta a seleção. Na ausência de parcelas, permite referência totalizada publicada de instituição idônea, mantendo fonte, n, métrica e incerteza disponíveis e sem promovê-la automaticamente a calibração SAR.
- O indicador qualitativo lista as 10 espécies com maior dominância por área basal média, primeiro na mesma microrregião e, se ausente, na escala regional do mesmo bioma e fitofisionomia. Mostra nome vulgar e científico somente quando fornecidos/normalizados pela fonte; caso contrário, informa N/D.
- Relatório e exportação Excel identificam “espécies de ocorrência mais provável” e deixam explícito que a lista regional não confirma ocorrência na propriedade.
- O pacote Windows passa a incluir catálogo, registro de portais e módulos correspondentes.

## Limites desta candidata

- A base é um catálogo inicial federado, não um censo completo de todas as publicações brasileiras.
- O único conjunto fitossociológico local incluído tem 30 resumos por parcela e não contém registros árvore a árvore nem composição de espécies. Portanto, por si só, ele não produz a lista top 10. A composição só pode ser calculada quando dados taxonômicos licenciados e compatíveis forem carregados/harmonizados.
- Inventários agregados e descobertas de portais permanecem referências ou pistas até auditoria de conteúdo, licença, fitofisionomia, desenho, geografia e incerteza.
- Não é build Windows; não declarar a candidata homologada.
