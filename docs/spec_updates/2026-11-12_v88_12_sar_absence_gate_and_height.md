# V88.12 — bloqueio de contingência por erro SAR e gate de altura (12/11/2026)

## Regra de contingência

A contingência MapBiomas + PAM ou de inventário só pode ser executada quando a ausência de cobertura SAR estiver comprovada para a AOI. Erro de autenticação, transporte, paginação, leitura/decodificação de pixel, timeout, rota não executada ou missão não configurada significa `ERRO_TECNICO`/incompleto e bloqueia a contingência.

O gate exige certificado explícito por rota, busca global completa, paginação completa, leitura concluída, zero pixels válidos, zero erros técnicos e nenhuma rota SAR não configurada. Um `N/D` genérico, acesso restrito ou falha de leitura não equivale a ausência de dados. Até que todos esses campos sejam produzidos por auditorias reais, a contingência permanece bloqueada.

## Altura estrutural

A altura de vegetação deve ser buscada primeiro no produto FH da ESA BIOMASS e lida na geometria da AOI. Se a cobertura FH não estiver disponível ou não for compatível, consultar alternativa estrutural com cobertura documentada, como GTDX (GEDI + TanDEM-X), registrando sensor, produto, período, resolução, pixels válidos, cobertura, unidade e incerteza. Falha técnica em qualquer fonte permanece erro e não autoriza declarar altura inexistente.

Altura isolada não é estoque de carbono. A estimativa exige ainda estratos nativos confirmados por SAR, área basal/diâmetros e equações/modelo compatíveis, com incerteza por compartimento. Não transferir altura ou biomassa de caixa regional para o imóvel.

## Área basal por inventário

Quando não houver medição de campo na AOI, a área basal pode ser estimada somente por extrapolação de parcelas de inventário compatíveis com bioma, fitofisionomia, estrutura, período e domínio ambiental. Priorizar inventários microrregionais; explicitar parcelas elegíveis/excluídas e distribuição espacial; ajustar pesos/amostragem; propagar incerteza amostral e de transferência e apresentar estimativa, erro/IC95% quando o desenho permitir. Inventário estadual ou de outro domínio é sensibilidade/fallback estatístico claramente rotulado, nunca observação da propriedade. Se não houver suporte amostral adequado, área basal e carbono ficam N/D, sem substituir por média publicada simples.

## Modelo publicado e distribuição diamétrica

Priorizar alometrias publicadas e aplicáveis ao domínio. A referência pantropical de Chave et al. (2014, DOI: 10.1111/gcb.12629), `AGB_árvore = 0,0673 × (ρ × DAP² × H)^0,976` (DAP em cm, altura em m, densidade da madeira em g/cm³), pode gerar rótulos de biomassa em parcelas de inventário quando as três variáveis forem medidas/identificadas e a equação for compatível. Isso não torna a estimativa da fazenda automaticamente validada: a altura do imóvel continua exclusivamente SAR; altura medida em inventário serve apenas ao rótulo/calibração. Densidade ausente, altura ausente ou incompatibilidade não será imputada silenciosamente.

O resumo por parcela deve preservar a distribuição diamétrica e área basal por classes **5–10, 10–20, 20–30, 30–40, 40–60 e ≥60 cm**, além de densidade de indivíduos por classe. Para não duplicar G, o candidato experimental integra altura de dossel SAR, área basal total média do inventário e composição relativa da área basal entre classes: `ln(AGB) = β₀ + βH ln(H_SAR) + βG ln(G_total) + Σ βk share(Gk)`, usando 5–10 cm como classe de referência. A retransformação de log para escala original exige fator de Duan estimado somente no conjunto de treino. Comparar contra alometria publicada e modelos-base, com validação espacial agrupada por sítio e holdout externo; reportar RMSE, MAE, viés, R², intervalos e domínio. Sem validação independente e transferência defendível, coeficientes permanecem exploratórios e não alimentam estoque no painel.

## Perspectiva fitossociológica no painel

Com CSV de inventário licenciado e proveniência verificável, selecionar apenas registros compatíveis com bioma, fitofisionomia e microrregião. Listar as 10 espécies mais frequentes por presença em parcelas, informar frequência, área basal média por espécie calculada sobre todas as parcelas (incluindo zeros), área basal comunitária de todas as espécies, riqueza e Shannon como estatísticas descritivas. Distribuições e intervalos refletem o desenho da região de origem; IC95% t simples só é mostrado para amostragem aleatória simples independente, sem apresentar esse intervalo como incerteza de transferência para o imóvel. Sem fonte compatível, mostrar N/D e motivo. Esta composição é referência regional, nunca observação da biodiversidade da fazenda.

## Aba de gráficos da planilha exportada

O Excel exportado inclui a aba **Gráficos** com: (1) linha de área basal média por classe diamétrica, ponderada pela área dos estratos nativos e baseada em inventários compatíveis; (2) linha da distribuição de altura do dossel a partir de frequências dos pixels SAR realmente lidos na geometria processada; e (3) barras das 10 espécies de maior frequência média de ocorrência nas parcelas dos inventários pertinentes. Cada bloco informa URL/instituição, fitofisionomia, microrregião, número de pixels ou parcelas e a natureza observada ou regional da referência.

Se nenhum pixel de altura SAR for efetivamente encontrado, a linha de altura só pode usar a distribuição média de alturas medidas em inventários pertinentes da mesma fitofisionomia e microrregião/região quando houver certificado de ausência SAR: catálogo global e paginação completos, leitura de pixels concluída, todas as rotas configuradas auditadas, zero pixels válidos e zero erros técnicos. O pipeline registra auditorias por coleção/produto da ESA BIOMASS FH L2A/L2B e paginação CMR do GTDX. O certificado de ausência só é emitido se as quatro consultas FH e a rota GTDX estiverem completas e sem produtos/pixels; se uma rota tiver erro, produto encontrado sem leitura concluída ou paginação sem contagem verificável, o certificado é bloqueado. Em falha, interrupção ou consulta incompleta, o gráfico permanece N/D com o motivo; não se mascara erro com média de inventário. A série regional é rotulada como altura de árvores medidas em inventário, nunca como altura SAR do dossel nem medição da propriedade. Valores SAR negativos são excluídos do histograma e das estatísticas de altura. Sem altura medida e fonte compatível, permanece N/D.

## Evidência e escopo

- No checkpoint anterior, o teste ESA MAAP leu 2.304 pixels FH em uma caixa próxima ao centroide de Sinop (média da amostra: 18,284 m). Essa leitura prova acesso ao produto na caixa de teste; não é média de altura da Fazenda Maria Eduarda nem prova de altura integrada ao dashboard.
- No workflow Windows iniciado sobre o commit anterior, o smoke óptico leu CBERS-4A/WFI com cobertura de pixels de 95% ou mais em 11/11 AOIs amostrais, incluindo uma janela centrada em Sinop. O teste worker→canvas em Sinop também passou. A amostragem não prova cobertura exaustiva nacional nem processa o KML privado integral.
- A triagem SAR sazonal da área de teste de Sinop e a máscara SAR no KMZ de teste Tapajós são experimentais; não demonstram acurácia de cultura, altura ou carbono na Fazenda Maria Eduarda.
- A versão agora inclui carregamento de inventário fitossociológico com licença/proveniência, quadro regional Top 10, área basal e distribuição DAP; a referência de biomassa por árvore implementa a equação publicada de Chave et al. (2014) somente com DAP, altura e densidade medidos no inventário. O candidato com altura SAR + bins DAP é exploratório e bloqueado para publicação de estoque até calibração/validação externa; altura da propriedade não pode vir do inventário.
- A planilha inclui a aba de gráficos para distribuição diamétrica média, altura e frequência Top 10. A distribuição de altura de inventário só substitui a série SAR se todas as rotas SAR certificarem ausência real; erros técnicos bloqueiam a substituição. Smoke local do exportador criou os três gráficos no cenário de pixels SAR e no cenário de fallback regional certificado, incluindo a fonte e o número de parcelas.
- A suíte direcionada do novo gate executou 23 testes e passou; `py_compile` e `git diff --check` também passaram localmente. O smoke XLSX revelou e corrigiu uma sobreposição de células mescladas que abortava a exportação quando a altura estivesse N/D. Essas evidências são da revisão local; o build Windows precisa ser repetido no novo SHA para validar a correção.

## Gate ponta a ponta para a Fazenda Maria Eduarda

Processar o KML original (1.459,91 ha) sem substituir seus limites por BBOX/centroide. O dashboard deve registrar cobertura e saldo sem classe; classificar pixels atuais por SAR; identificar “área cultivada” quando a cultura não for sustentada; verificar a presença nativa sem preencher lacunas com IBGE/MapBiomas; buscar FH e a alternativa de altura quando necessária; estimar carbono apenas em estratos nativos compatíveis, com inventário/equação e incerteza explícitos. Erro técnico em qualquer etapa permanece visível e não dispara contingência histórica. Resultado em caixa ou subjanela não é resultado da propriedade.

## Estado

A regra de bloqueio está implementada localmente e coberta pelos testes direcionados. A versão é experimental; o CI do novo SHA, a geração e o autocheck do EXE, a execução integral do KML no dashboard e a homologação científica ainda precisam ser comprovados antes de declarar conclusão operacional.
