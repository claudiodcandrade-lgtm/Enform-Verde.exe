# Plano operacional de evidências independentes — 2026-10-30

Este documento **não é evidência de homologação**. Define a execução acelerada sem criar dados, métricas ou intervalos artificiais.

## Ordem de execução
1. Inventariar datasets observacionais acessíveis SFB/IFN, Embrapa, universidades e solos 0–100 cm, registrando URL, licença, versão, checksum, unidades, desenho amostral, período e fitofisionomia IBGE legenda_1. Rejeitar fontes sem direito de uso demonstrável.
2. Estratificar por fitofisionomia compatível e proximidade microrregional; usar estimadores estaduais IFN somente no último fallback, sempre declarando o erro de transferência e a perda de representatividade. Ausência de erro estimável => N/D para incerteza, não IC95% fictício.
3. Construir tabela de rastreabilidade dos 30 pares bioma × compartimento: AGB, raízes, necromassa em pé, necromassa caída, serrapilheira e solo 0–100 cm. Não preencher lacunas com médias bibliográficas não validadas na AOI.
4. Processar cenas SAR efetivamente baixadas com ID, horário, banda, geometria, pré-processamento, hash e pareamento espacial/temporal com parcelas. Altura de dossel exclusivamente ESA BIOMASS FH P ou TanDEM-X InSAR compatível, GEDI auxiliar; altura de inventário não substitui altura SAR. Produto ou erro não disponível => N/D motivado.
5. Executar validação espacial independente com RMSE, MAE, viés, R², intervalos de previsão/transferência e cobertura empírica, com protocolo de separação treino/teste. Intervalo descritivo não é IC95% da AOI.
6. Validar agricultura (área cultivada antes de espécie), vigor remoto, clima, previsão de safra somente quando sustentada; manter safras bloqueadas se modelo não validado. Testar painéis e regressões.
7. Gerar `validation/release_evidence.json` **somente a partir de artefatos reais verificados**, e validar hashes e caminhos. O manifesto não deve conter placeholders nem declarações de aprovação sem resultados observados.
8. Executar homologação, testes e build Windows no mesmo SHA; conferir teste de extração em máquina limpa, hashes e URL real. PR #50 permanece draft até todas as verificações passarem.

## Gate adicional necessário
O gate atual verifica presença e formato de metadados, mas não verifica a existência e o conteúdo dos arquivos citados por `validation_report`, nem confirma empiricamente que o intervalo marcado `ci95` é IC95% da AOI. Acrescentar verificação dos relatórios, hashes, critérios de independência, proveniência, domínio do modelo e semântica dos intervalos antes de considerar um gate verde suficiente.

## Situação
No SHA `cfd3c42e2f868c500a6f0f9ab19d1dbfdb413dd0`: dashboard e build Windows aprovados; homologação científica reprovada, sem manifesto. Nenhuma validação nova é afirmada por este plano.

## Matriz de decisão técnica — alternativas avaliadas em 30/10/2026

**Critério de escolha:** (a) dados reais e auditáveis, (b) compatibilidade fitofisionômica/espacial/temporal, (c) possibilidade de quantificar erro de transferência, (d) licença e acesso, (e) custo e tempo. A seleção abaixo é uma **prioridade de implementação**, não prova de que os insumos foram obtidos.

| Pendência | Alternativas viáveis | Escolha preferencial e contingência | Bloqueio verificável |
|---|---|---|---|
| Inventários cinco biomas | Parcelas abertas SFB/IFN; inventários Embrapa/universidades; relatórios agregados IFN estaduais | Parcelas microrregionais com legenda_1 compatível; depois inventários regionais; estadual apenas último recurso com erro de transferência demonstrado | Sem dados primários/licença/estratos ou sem dispersão defensável: não homologar intervalo |
| AGB | SAR BIOMASS P calibrado; SAR L/X com pares parcela-pixel; CCI AGB como referência secundária | Produto SAR processado e validação espacial independente; CCI como comparação/fallback com incerteza de transferência, nunca prova de aquisição SAR da AOI | Catálogo sem raster, ausência de parcelas independentes ou extrapolação fora de domínio |
| Raízes | Equações alométricas tropicais por formação; razão raiz/parte aérea estratificada; inventários diretos | Alometria compatível por fitofisionomia, propagação de parâmetros/AGB e covariância quando disponível | Não chamar alometria de medição direta; extrapolação não quantificável => N/D |
| Necromassa em pé/caída | Parcelas IFN com madeira morta; estudos microrregionais; fatores de transferência | Observações primárias por formação, densidade e variância; transferência regional somente com erro mensurado | Não inferir necromassa de AGB sem modelo validado |
| Serrapilheira | Pesagens secas observadas; parcelas IFN; literatura por formação | Dados gravimétricos por fitofisionomia e época; propagar variação espacial e temporal | Sem variância/transferência: estimativa exploratória claramente separada, não IC95% |
| Solo 0–100 cm | Perfis Embrapa/PronaSolos; perfis regionais completos; predição digital com validação | Perfis 0–100 cm com densidade aparente, C e fragmentos; integração por horizontes e validação espacial | Não extrapolar 0–30 cm a 100 cm sem modelo local validado |
| Altura dossel | BIOMASS FH P; TanDEM-X InSAR com GEDI auxiliar; altura de inventário | Primeira rota SAR orbital real quando produto adequado e acessível; segunda rota TanDEM-X+GEDI com correção e validação; inventário apenas checagem independente | Sem produto de altura SAR efetivamente processado => N/D; não converter RH98 em H100 sem calibração |
| Máscara de cobertura atual | MapBiomas anual; cache oficial íntegro; classificação SAR validada | MapBiomas + interseção IBGE; fallback SAR classificado com validação e data; três estados nativa/antropizada/indeterminada | Falha de rede não é ausência de vegetação |
| Agricultura | Série Sentinel-1 + amostras independentes; modelos regionais publicados; MapBiomas como referência auxiliar | Primeiro separar cultivada/nativa/pastagem quando possível; depois cultura por classificadores com calibração local e matriz de confusão | Classe genérica 'áreas cultivadas' quando espécie incerta; não afirmar cultura sem evidência |
| Vigor | Séries SAR multitemporais e fenologia; modelos SAR+óptico; regra heurística | SAR multitemporal com três classes apenas após calibração e validação independente; heurística só como indicador exploratório, nunca classe validada | Sem validação, sinalizar N/D ou bloqueado |
| Clima | NASA POWER; INMET/BDMEP; CPTEC | NASA POWER para histórico diário de grade; INMET para contraste quando viável; CPTEC para previsão com permissão/licença aplicável | Não tratar reanálise/grade como estação medida na AOI |
| Safra | PAM microrregional + SAR e máscara de cultura; modelos publicados transferidos; modelo experimental hierárquico | PAM real + SAR real temporalmente alinhado, validação fora de amostra e intervalos calibrados; fallback de modelo publicado só dentro de domínio com erro de transferência | Sem máscara/cenas/validação => previsão bloqueada |
| Painel, regressão, desempenho | Testes unitários; golden AOIs; testes Windows limpos | Golden AOIs independentes + benchmarks de memória/tempo e smoke no EXE, preservando tC/tCO2e e auditoria | Testes sintéticos não substituem validação observacional |
| ZIP Windows | Build no merge ref; build no SHA da branch; release imutável | Checkout explícito do SHA homologado, testes Windows do EXE extraído, hash EXE/ZIP e URL GitHub verificada | Build verde sem gate científico não libera versão |

### Paralelização e ordem crítica
- **Trilha A (dados):** inventários e perfis de solo por bioma/legenda_1; licenças e hashes; preparar tabela de amostras reais.
- **Trilha B (sensoriamento):** corrigir cobertura MapBiomas, adquirir cenas SAR e testar alturas/AGB com pares parcela-pixel; manter proveniência orbital.
- **Trilha C (agricultura):** máscaras, amostras, séries SAR e validação de classificação; só depois vigor e safra.
- **Trilha D (engenharia):** reforçar gate com verificação de relatórios/hash, testes golden, desempenho e Windows; pode ocorrer em paralelo às trilhas A–C.
- **Caminho crítico de homologação:** evidências observacionais independentes, erro de transferência e altura SAR; nenhum build isolado resolve isso.

### Definição de pronto por entrega
Cada evidência aceita precisa apontar para dataset real acessível, licença, hash conferido, recorte geográfico, fitofisionomia, período, método, unidades, amostras treino/teste espacialmente separadas, métricas calculadas e relatório verificável. Registrar limitações e N/D quando faltar produto ou erro; **não transformar lacunas em resultados aprovados**.

## Política de acurácia e incerteza — revisão de homologação 30/10/2026

- **Nenhum limiar universal de acurácia é imposto pelo gate.** Acurácia de classificação deve ser observada em amostras independentes, reportada como fração 0–1 e acompanhada de matriz de confusão, prevalência por classe e incerteza da métrica. Acurácia global sozinha não prova a capacidade de distinguir culturas raras.
- Para regressões de AGB/altura/estoques: registrar RMSE, MAE, viés, R² (inclusive valores negativos), tamanho amostral, desenho de validação e cobertura empírica de intervalos. RMSE/MAE não podem ser negativos; R² não pode superar 1. Não impor R² mínimo.
- Para inferência por fitofisionomia: propagar erro de modelo, amostragem e transferência espacial/temporal. Só chamar um intervalo de **IC95%** quando sua construção, hipótese e cobertura forem demonstradas para o estimando; caso contrário usar intervalo preditivo, intervalo de transferência ou faixa exploratória, devidamente rotulados.
- **Nível de uso distinto de homologação do software:** (1) estimativa operacional com incerteza validada; (2) estimativa exploratória com erro de transferência quantificado e advertência; (3) N/D quando não houver mensuração defensável. Certificação exige avaliação própria de adequação ao método, adicionalidade e MRV; não decorre de uma acurácia numérica isolada.
- A permissão de baixa acurácia **não** autoriza simular dados observacionais, omitir erro, usar classe IBGE como cobertura atual, declarar altura SAR sem raster processado ou publicar safras sem validação independente.

## Alternativa de homologação modular e progressiva — proposta técnica 30/10/2026

**Problema:** o gate atual exige aprovação simultânea de cinco biomas × seis compartimentos e das funcionalidades SAR/agricultura/clima/vigor/safra, embora os dados observacionais não estejam integralmente disponíveis. A ausência de `validation/release_evidence.json` é sintoma da ausência de relatórios independentes, não a causa científica principal.

**Alternativas consideradas:**
1. **Homologação nacional integral:** preservar exigência de 30 pares aprovados; maior cobertura, mas cronograma condicionado a dados escassos e licenças.
2. **Homologação modular por bioma × fitofisionomia × compartimento (preferida):** validar individualmente modelos/domínios e expor no produto uma matriz de cobertura científica. Estimativas não validadas não recebem selo de aprovação; funcionalidades podem operar com bloqueio/N/D quando faltam insumos.
3. **Homologação apenas de contratos de software:** rápida, mas insuficiente para comprovar estimativas; rejeitada como homologação científica.
4. **Modelos experimentais com validação externa transferida:** admissíveis como resultados exploratórios somente com quantificação de erro de transferência e domínio explícito; não contam como validação independente local sem teste de transferência.

**Arquitetura recomendada (não implementada):** dois gates independentes, `software_release_gate` (execução correta, bloqueios seguros, painéis, proveniência, regressões e Windows) e `scientific_model_gate` (aprovação por combinação bioma/fitofisionomia/pool/sensor/domínio). O manifesto deve declarar `capability_status` para cada combinação e o produto deve impedir que uma capacidade N/D seja anunciada como validada. A liberação operacional com escopo limitado exige autorização explícita do responsável, rótulo visível de escopo e exclusão de alegações de certificação científica nacional. **Não modificar o gate atual para aprovar dados inexistentes**; primeiro especificar os critérios, implementar testes e aprovar formalmente a mudança de escopo.

**Rotas de dados em paralelo:**
- SFB/IFN: aproveitar observações por unidade amostral com desenho e dispersão conhecidos; se não houver coordenadas abertas, usar agregados por fitofisionomia para estimativas exploratórias, com incerteza de transferência demonstrável.
- Solo 0–100: combinar horizontes medidos com densidade aparente e fragmentos, ou usar modelos digitais calibrados com perfis independentes até 100 cm. Não multiplicar 0–30 por fator arbitrário.
- Raízes: equações alométricas por formação e propagação conjunta de incertezas de AGB e parâmetros; não exigir medição direta de raízes se o modelo for validado dentro do domínio.
- Necromassa/serrapilheira: dados gravimétricos ou inventários publicados por formação com dispersão; caso contrário N/D ou faixa exploratória rotulada, nunca IC95% inventado.
- SAR: processamento orbital real e pareamento com parcelas, com fallback a estimativa de AGB não SAR identificada quando o sensor estiver indisponível. Altura SAR permanece N/D se não houver produto orbital compatível.
- Agricultura/safra: classificação binária de áreas cultivadas primeiro; espécie, vigor e safra são capacidades separadas, bloqueadas quando não validadas.
- Clima: NASA POWER pode fornecer série de grade com origem e resolução; validação de previsão de safra não decorre automaticamente da disponibilidade climática.

**Requisitos de auditoria:** evidência por capacidade, dados reais, licença, hash, data, AOI, legenda_1, métricas independentes e erro de transferência; relatório acessível e checksum; incerteza e tipo de intervalo; escopo geográfico/temporal; versão e SHA exato. Nenhuma acurácia mínima arbitrária, mas métricas e cobertura empírica verificáveis.

**Decisão pendente:** autorização de homologação **operacional de escopo limitado** separada da homologação científica nacional integral. Até essa decisão, o gate nacional continua bloqueando a liberação definitiva.
