# REVISÃO V72 — PRIORIDADE P/X/L, ALTURA EXPERIMENTAL E IDENTIFICAÇÃO NATIVA — 04/11/2026

## Hierarquia de fontes e fallback
ESA BIOMASS banda P FP_FH__L2B continua como primeira fonte direta de altura de dossel (H100), com unidade, máscara, incerteza, data de aquisição e pixels válidos preservados. Sentinel-1 VV/VH recente é covariável complementar de estrutura/textura e contexto temporal; não produz altura física por si só. A banda X é a alternativa seguinte apenas quando P-band ESA e a observação SAR recente prioritária não estiverem disponíveis para a AOI. A banda L é a contingência seguinte, somente quando X também estiver indisponível. A trilha de auditoria registra tentativas, datas, ativos, cobertura, falhas e razão de escolha.

## Modelo de altura experimental em X/L
O módulo native_biomass_sentinel1_height.py agora oferece ajuste e predição por regressão linear multivariada com coeficientes explícitos, restrita a observações independentes de altura de campo pareadas com pixels SAR, mesma definição de altura, fitofisionomia, footprint e período compatíveis. O ajuste exige cinco sítios espaciais independentes, fonte e SHA-256 dos dados, validação espacial GroupKFold e publica RMSE, MAE, viés, R², coeficientes, limites observados dos preditores e quantis 5–95% dos resíduos out-of-fold.

A função de predição respeita a precedência: não executa X/L se a rota P/Sentinel-1 prioritária tiver observação válida; L só é aceita depois de X ser declarado indisponível. Preditores fora do domínio, incompatibilidade de formação/banda, ausência de pares ou falta de erro out-of-fold resultam em N/D. Saídas desse modelo são experimentais, não homologadas nacionalmente, e seu intervalo empírico não substitui validação externa por região.

Os testes novos cobrem os contratos de código com dados sintéticos. Eles demonstram que as rotas executam e respeitam os bloqueios definidos, mas não constituem validação ecológica nem evidência de acurácia real. O novo código ainda precisa ser chamado pelo pipeline de análise da AOI e alimentado com pares observados licenciados antes de entrar como resultado automático no aplicativo.

## Identificação de vegetação nativa por SAR
A presença e a geometria da vegetação nativa são determinadas por classificador SAR supervisionado com referências de campo independentes. Sentinel-1 pode fornecer VV/VH, granulometria/textura em múltiplas escalas e contraste espacial. A regularidade geométrica dos segmentos (retangularidade, razão perímetro/área, orientação e repetição) pode atuar como preditor auxiliar de conversão. Rugosidade radiométrica é proxy textural e não deve ser descrita como rugosidade física em metros. A falta de padrões geométricos, isoladamente, não prova vegetação nativa.

O código atual já contém sondagem real Sentinel-1 e extração de contraste/textura, contrato de classificação com referências independentes e name_native_from_ibge para denominar fitofisionomias IBGE compatíveis. Entretanto, a sondagem não classifica natividade; ainda não foi demonstrada a integração dos preditores multiescala e geométricos à inferência com pesos executáveis e acurácia independente por classe. Portanto, a identificação SAR nativa permanece não homologada e não pode ser declarada plenamente operacional até cumprir essa etapa.

A geometria identificada pelo SAR conserva precedência. IBGE legenda_1 só fornece o nome da formação compatível: primeiro por interseção exata e, se ausente, por proximidade limitada a 3 km, com rótulo "inferido" e distância no relatório. IBGE não cria cobertura atual nem amplia a área identificada.

## Estado técnico e critérios de fechamento
- Ajuste de altura X/L adicionado ao PR #50 nos commits e1ece3aa632d4983b9d53a06d10e7fef3ff18f6c e a037009d6567b8714fe48d8b4f2a1c8019ada960.
- A suíte Dashboard dual e o build Windows estavam em execução no SHA de código; consultar de novo após este adendo porque a atualização documental dispara novas execuções.
- Homologação independente segue pendente. Não usar testes sintéticos como evidência observacional, não declarar EXE concluído antes de artefato ZIP e smoke test no mesmo SHA e não atribuir IC95% calibrado sem evidência de cobertura.
- Para reconhecer vegetação nativa, exigir pixels Sentinel-1 reais, modelo executável com granulometria/textura e forma de objetos, holdout espacial independente, dados de campo licenciados, métricas por classe/fitofisionomia e incerteza de área.
- Para estimar altura X/L, exigir produto/pixels compatíveis, pares independentes de campo, definição de altura equivalente, domínio ecológico, licença, SHA-256, métricas out-of-fold e validação externa por região antes de elevar o status além de experimental.
- Não regredir o cálculo de carbono existente, raízes alométricas, necromassa, serapilheira e solo por interseção Embrapa/PronaSolos 0–100 cm.
