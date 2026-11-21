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

## V88.179 — checkpoint de revalidação e diagnóstico do timeout (21/11/2026)

- O FH real ESA MAAP passou no ensaio CI separado e o EXE passou build, módulo/dados, paridade, visual e leitura real de CBERS/Sentinel-1, mas o aceite Tapajós em pasta limpa expirou novamente aos 900 s no SHA `5c31cd705307a2f76df02207719ad142d5d544a1`.
- A leitura progressiva FH não resolveu o timeout. `acceptance_test` agora registra etapas e stack traces de todas as threads a cada 60 segundos; o workflow inclui o arquivo de progresso na saída de diagnóstico. Identificar a chamada bloqueante antes de uma nova correção; não mascarar com aumento do timeout.
- Regressão funcional passou, porém o gate documental falhou porque a última mudança funcional não alterou Word e especificação PronaSolos após o SHA de código. A documentação V88.179 sincroniza o prompt V52, este checkpoint, o DOCX e a especificação de solo.
- Reexecutar regressão integral, coletor, regra documental, build, SAR live e aceite limpo no novo SHA. Sem EXE disponível até o aceite e handoff final passarem. Sem homologação científica independente ou validação de campo.


## V88.177 — FH, inventários horizontais e evidência Embrapa (21/11/2026)

A candidata `3.26.85-PRECAMPO-EXPERIMENTAL` acrescenta metadados verificáveis por cultura para rotas de previsão encontradas na Embrapa. Isso não integra automaticamente solvers nem altera o painel PAM/FAO calibrado (soja e milho). Modelos de domínio regional/varietal permanecem restritos ao domínio publicado; vigor SAR só entra como preditor após validação apropriada.

Na rota de carbono, FH×G quantitativo segue restrito ao suporte local calibrado de Tapajós. Consultas IFN por fitofisionomia e proximidade e os agregados horizontais publicados ficam anexados como evidência regional. DAP, altura e área basal brutos não são por hectare sem desenho/expansão harmonizados. Se FH for lido sem equação compatível, o relatório o explicita e não inventa AGB. CCI pode ser a segunda estimativa, com inventários AGB/horizontais reportados para comparação; não há recalibração numérica CCI–inventário sem pares AGB parcela–pixel adequados. Médias AGB compatíveis de diferentes fontes permanecem a contingência final. Não transferir coeficientes Tapajós nacionalmente.

Validação do código no commit local: 1.360 testes passaram, 1 ignorado; 197 módulos inspecionados pelo coletor. Integrações FH sintéticas e CCI secundário passaram. Gates Windows, build, verificações do EXE e teste limpo ainda precisam passar no CI. Sem homologação científica de campo.

### Checkpoint V88.180 (21/11/2026)
No SHA f4d44e7, o EXE Windows passou build e gates de SAR/FH, mas a aceitação Tapajós em pasta limpa expirou a 900 s. O progresso instrumentado não apareceu nos logs, indicando que o coletor consultou caminho temporário incorreto ou o dispatcher não entrou na rotina. O código atual grava marcador anterior à rota e o workflow buscará todos os arquivos diagnósticos em diretórios temporários Windows alternativos. Aguardam-se testes e novo gate Windows; sem aceite não distribuir.
