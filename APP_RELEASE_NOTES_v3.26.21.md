# Enform Verde v3.26.21-PRECAMPO-EXPERIMENTAL

- Gate de contingência: falha técnica, paginação incompleta ou leitura de pixels interrompida não libera MapBiomas/PAM nem referências de altura regionais.
- Inventário fitossociológico licenciado: resumo regional Top 10 por frequência de parcelas, área basal média por espécie, área basal comunitária e distribuição de DAP.
- Referência de AGB de parcela com a equação publicada de Chave et al. (2014), usando DAP, altura medida e densidade da madeira; não constitui validação local nem altura da fazenda.
- Candidato exploratório combina altura SAR, área basal média e composição relativa da área basal por classe DAP. Permanece bloqueado para estoque até validação externa.
- Nova aba Excel “Gráficos”: distribuição diamétrica média, distribuição de altura SAR ou referência de inventário somente após ausência SAR certificada, e barras de frequência média das 10 espécies; fontes explícitas.
- Gráficos agora exibem a instituição junto à URL/citação rastreável do inventário; referência regional de altura sem proveniência identificável é bloqueada e aparece como N/D.
- O gráfico diamétrico passou a apresentar, em porcentagem comparável, tanto a frequência média de indivíduos por classe DAP quanto a participação média da área basal; a tabela auxiliar mantém os valores absolutos por hectare.
- Certificado de ausência ligado a auditorias ESA BIOMASS FH e GTDX/CMR; rota incompleta, não auditável ou com erro bloqueia médias regionais.
- Valores negativos são removidos das estatísticas de altura SAR. A série de inventário informa alturas de árvores medidas, não altura SAR do dossel.
- Diagnóstico live ESA alinhado ao limite de consulta de produção (100 itens, com paginação) para não omitir cenas FH por janela inicial curta.
- Painéis N/D do Excel confinados às próprias colunas para evitar colisões entre mensagens de inventário e altura.

## Situação de validação

Versão experimental. Testes direcionados e smoke local da exportação Excel passaram, incluindo os três gráficos com pixels SAR e com contingência regional certificada. Build Windows no SHA atualizado, leitura de altura no perímetro integral da Fazenda Maria Eduarda e homologação científica ainda devem ser confirmados antes de declarar uso operacional.
