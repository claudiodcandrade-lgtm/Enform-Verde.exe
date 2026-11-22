# V88.90 — inventários nacionais e controle de extrapolação SAR

## Fontes florestais e contagem

Manter rotas federais, estaduais, institucionais, acadêmicas e agregadas: SFB/SNIF/IFN; IBAMA/Sinaflor/licenciamento/PAMGIA; PNLA; SIMLAM PA/MT; SIAM/SLA/IDE-Sisema/IEF/COPAM; IPAAM/SEDAM/IMAC; IFFSC/FURB; ICMBio; Embrapa REDAPE/Alice/Infoteca/Paisagens LiDAR; INPA/PPBio/Acta; Museu Goeldi; universidades e periódicos; ForestPlots/Rainfor, SiBBr, NeoTropTree, speciesLink, BDTD/CAPES, SciELO, Zenodo, Dryad e Dados.gov.br. O catálogo separa rota, metadado, publicação, download, parcela harmonizada e fonte elegível.

Na captura de 15/11/2026, PMFS e IF100 somam 9.284 IDs de autorização distintos após deduplicação exata, sem identificador coincidente. São autorizações administrativas, não inventários. O arquivo federal de licenciamento contém 2.532 processos únicos (761 com ASV), que são apenas localizadores. Há 27 referências bibliográficas agregadas candidatas no catálogo, 80 registros catalográficos, 53 rotas e um arquivo local com 30 resumos por parcela do Tapajós. O total de inventários independentes e de anexos aceitos não é mensurável antes de recuperar, ler e deduplicar os próprios estudos/documentos.

## Hierarquia e aceite de anexos ambientais

1. Parcelas abertas, georreferenciadas e licenciadas de instituição reconhecida na mesma fitofisionomia, priorizando microrregião e proximidade.
2. Na falta de parcelas, inventário publicado e totalizado por instituição reconhecida, com método, unidade, n, estatística e incerteza preservados.
3. Somente na ausência de fonte melhor compatível, usar inventário de processo ambiental se o próprio anexo estiver identificado por URL e SHA-256 e um parecer/decisão oficial aceitar explicitamente esse inventário. Aprovação da licença, ASV, plano de manejo, PMFS ou processo isoladamente não basta.

Exigir acesso autorizado, identificação do processo e do anexo, evidência explícita do aceite, método/unidades, métrica extraída e compatibilidade espacial/fitofisionômica. Sem qualquer item, manter como pista sem uso numérico. Sem erro amostral publicado, reportar literalmente “incerteza não mensurável”. Inventário de órgão não se torna automaticamente dado de calibração SAR.

## Altura SAR e uso agrícola em AOIs fora da região de treinamento

A altura de dossel SAR continua prioritária, mas retroespalhamento VV/VH não é altura. Aplicar equações biométricas apenas no domínio compatível documentado; declarar ausência/extrapolação e incerteza fora dele.

Auditoria do relatório Tapajós recebido em 15/11: modelo `ENFORM_SAR_BRASIL_RF_V2`, grade de 80 m e somente 0,64 ha de soja (um pixel de 80 × 80 m) e 1,92 ha de café (três pixels). O código recalcula atributos Sentinel-1 para a geometria da AOI e não usa cache compartilhado de rótulos entre fazendas. O problema encontrado foi que, fora do envelope geográfico de treinamento, a extrapolação experimental ainda podia receber nomes específicos de cultura e entrar em previsão específica.

A correção exige que a extensão completa da AOI esteja dentro do envelope de treinamento para liberar nomes de cultura. Fora dele, preserva eventual indicação experimental genérica de “Área cultivada — cultura não identificada”, suprime soja/café/etc. e bloqueia o uso dessas culturas pela previsão específica. Sinop permanece dentro do envelope e preserva o resultado experimental com identificação de cultura. Área/cobertura permanece experimental e sem validação de campo.

A regressão testa Tapajós fora do domínio, Sinop dentro, AOI que cruza a borda e bloqueio da previsão quando a classe é genérica; os cinco testes novos passaram. Ao todo, 42 testes focados disponíveis passaram. O teste integrado `test_sar_landcover_lemplus.py` não roda neste ambiente por falta de `geopandas`; build Windows, CI, pixels live do KML privado e validação de campo continuam pendentes. Esta correção reduz sobredeclaração; não confirma por si só o uso real de qualquer pixel Tapajós.
