# Registro de evidências para perfil experimental — Enform Verde
Data: 2026-11-03  
Escopo: inventário das evidências primárias/públicas já representadas no repositório e do que é necessário para aprovar capacidades experimentais. **Este arquivo não é laudo de homologação e não declara o gate aprovado.**

## Regra de decisão
A evidência pode sustentar: (a) resultado validado, se houver avaliação independente; (b) resultado experimental, se dados/parâmetros e equação tiverem origem verificável, o domínio estiver delimitado e a incerteza numérica estiver dimensionalizada; ou (c) N/D. Cenários e intervalos preditivos não são IC95% sem cobertura demonstrada. Erro sistemático de transferência não pode ser ocultado por um intervalo paramétrico.

## Evidência observacional/processada encontrada

| Capacidade | Evidência existente | Incerteza que pode ser dimensionada | Limite que impede alegação mais forte |
|---|---|---|---|
| AGB | IFN/SFB tem observações de árvore e o Painel Biomassa e Carbono publica estimativas baseadas no IFN. O cadastro local relaciona também inventários microrregionais e as fontes estaduais. | Com DAP, altura e densidade de madeira, pode-se executar a equação pantropical de Chave et al. (2014), propagar erro alométrico e amostral, e usar holdout por UA/região quando os dados brutos permitirem. | Estimativas do Painel SFB usam o IFN e não são validação independente do próprio IFN/SAR. A síntese bibliográfica não substitui a extração e auditoria dos dados primários, nem prova pareamento SAR parcela-pixel. |
| Raízes | Há rota alométrica por razão raiz:parte aérea na literatura internacional (Mokany et al., 2006). | Propagar a distribuição da razão e a incerteza da AGB; apresentar faixa preditiva/experimental por domínio. | A revisão excluiu 62% dos dados coletados por métodos inadequados ou não verificáveis. Não aceitar uma razão universal; filtrar domínio e documentar erro de transferência. |
| Necromassa caída | O repositório contém `data/ifn_necromass_biome_uf_v1.csv`, resumo por bioma×UF de dados do painel IFN/SFB. SHA-256 local: `7752fc4c8ff3ae23b30f182c75a848d5f42ab0fe2e0a81ecba4399a0936f5da7`. Soma informada: 42 estratos UF×bioma e 3.059 UA em quatro biomas: Amazônia 1.155/9 UFs; Caatinga 753/9; Cerrado 786/11; Mata Atlântica 365/13. Pantanal: nenhum registro nessa tabela. | Por estrato bioma×UF, a tabela traz média, DP entre UA, mínimo, máximo e n. Para piloto, conservar média + DP espacial ou intervalo empírico de valores observados em Mg de matéria seca/ha; se calcular intervalo preditivo, validar distribuição e desenho com microdados originais. | O arquivo local é resumo derivado, não os bytes originais da fonte. Ainda é necessário reacquirir/hashinizar o CSV oficial e confirmar licença/reprodutibilidade. Não há fitofisionomia nem posição física individual nesta síntese; não transferir silenciosamente para classe IBGE ou chamar de validação SAR. Matéria seca não é carbono. |
| Necromassa no Pantanal | Auditorias existentes registram 12 UAs físicas coincidentes entre madeira caída e serrapilheira, coleta IFN 2018. Nove levam classe de uso 45/pastagem cultivada e ficam fora do carbono nativo; três permanecem sem crosswalk IBGE confirmado. | A densidade amostral só será dimensionável depois de restaurar identificador de transecto, observações completas e densidade por classe de decomposição. | 12/13 registros não identificam transecto; não há estoque ou variância de madeira. A coincidência entre bases não é validação de carbono nem SAR. |
| Serrapilheira | SFB/IFN tem profundidade medida em cinco pontos por UA; a auditoria Pantanal identificou 12 UAs físicas e 60 leituras. Há estudos gravimétricos no inventário bibliográfico do repositório. | A profundidade tem DP entre pontos/UA; massa seca só pode usar regressão gravimétrica massa–espessura com amostras pareadas, erro de ajuste e holdout por UA/estação. | Profundidade em cm não é massa. Fluxo anual de queda de liteira não é estoque em pé. Sem calibração gravimétrica compatível, carbono = N/D. |
| Solo | SoilGrids publica quantis espaciais Q05/Q50/Q95, que formam intervalo preditivo de 90% por pixel/propriedade/profundidade. A documentação informa estoque SOC para 0–30 cm e descreve o subsolo 30–100 cm como ainda em desenvolvimento na versão consultada. | Valores 0–30 podem ser propagados como distribuição de previsão de pixel, preservando a semântica de 90%; agregação para AOI precisa modelar covariância espacial e entre camadas. | Não chamar Q05–Q95 de IC95% da AOI. Não declarar estoque 0–100 cm derivando-o automaticamente do produto 0–30, nem somar quantis marginais como se fossem independentes. A base IFN de solos local apresenta ressalva de licença ainda pendente. |
| Agricultura / culturas | O repositório tem catálogo de modelos e dados PAM municipais/microrregionais. | Para piloto, probabilidades/candidatos por cultura e estágio podem ser exploratórios com incerteza do classificador calibrada em fonte externa e saída de abstenção. | PAM e MapBiomas agregados não são rótulos de pixel independentes; faltam amostras brasileiras de lavoura com holdout por fazenda/região/safra para estimar acurácia local. Não publicar acurácia brasileira sem esse teste. |
| SAR, vigor e safra | Há catálogo de sensores/fontes, rotas de aquisição e séries climáticas. | A incerteza do produto/SAR pode ser propagada se o raster real, data, pré-processamento e modelo executado forem fixados; safras exigem intervalo preditivo e validação temporal. | Descoberta de cena, backscatter médio ou clima disponível não demonstram máscara de cultura, vigor, erro SAR ou produtividade prevista. Sem pareamento/holdout, bloquear a alegação validada. |

## Modelo matemático candidato para necromassa (somente piloto, escopo limitado)
O arquivo local já calcula fallback bioma×UF com centro \\(\bar{x}\\) em Mg matéria seca/ha e dispersão \(s\) entre UA. Para n UA, o código vigente constrói uma aproximação t de intervalo preditivo:  
\[
\bar{x}\;\pm\;t_{0.975,n-1}\,s\sqrt{1+1/n}.
\]
O intervalo precisa ser rotulado **aproximado e condicional à permutabilidade das UAs no estrato bioma×UF**. A distribuição IFN é assimétrica e tem extremos grandes; portanto a cobertura de 95% não está comprovada pela fórmula. Para a aprovação experimental, usar intervalo preditivo apenas após reprocessar microdados e checar cobertura/assimetria; enquanto isso, publicar média, n, DP e mínimo–máximo observados como resumo descritivo, sem chamar o envelope observado de IC ou PI.

Conversão matéria seca→carbono exige fração C rastreável. Estudos globais reportam média de fração de carbono da madeira morta de 48,5% (SE 0,8 p.p.) e estimativa tropical de 47,16% (SE 0,79 p.p.), com variação por bioma, grupo taxonômico, tecido e decomposição. Esses parâmetros internacionais podem sustentar **cenário experimental** com sensibilidade propagada, não equivalem a fração medida nas UAs brasileiras nem validam transferência local.

## Critério para green experimental
Criar um perfil versionado que nomeie cada capacidade e seu estado; não exigir evidência inexistente para a capacidade explicitamente marcada N/D. Para cada saída `experimental`, exigir:
1. equação implementada e versão/hash do código; parâmetros, unidades, fontes e domínio;
2. observações/dados fonte reais, licença, SHA-256 original e do derivado, transformação reproduzível;
3. incerteza dimensionalizada (p.ex. Mg/ha, tC/ha, tCO2e/ha), componentes amostral/paramétrico/sensor/transferência identificados, correlações tratadas ou limitadas;
4. nome correto do intervalo: IC, intervalo preditivo, intervalo de transferência ou envelope de cenário; cobertura empírica apenas se medida;
5. limites geográficos/temporais e taxonômicos; rótulo visível **EXPERIMENTAL — NÃO VALIDADO LOCALMENTE** e abstenção quando extrapolar;
6. protocolo prospectivo de campo, com predições congeladas antes da leitura dos resultados e separação por UA/fazenda/bloco e safra;
7. CI independente para `software_release`, `experimental_pilot`, `modular_scientific_homologation` e `national_scientific_homologation`. O gate integral só é verde quando sua cobertura integral estiver comprovada.

## Fontes primárias/metodológicas consultadas
- SFB, Painel de Biomassa e Carbono — licença CC BY; dados derivados do IFN; anos-base 2011–2024, consulta ao IFN em 2025, publicado no SNIF em março de 2026: https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono
- SFB, metadados do Painel: https://dados.florestal.gov.br/pt_BR/dataset/2d579a3b-29f7-41af-b35c-8fb8f51ef819/resource/dcd83340-a57b-4a2f-bd08-4cf2a84edb78/download/metadados_painelbiomassacarbono_snif_fonte_ifn_sfb.pdf
- Chave et al. (2014), alometria pantropical AGB: https://doi.org/10.1111/gcb.12629
- Mokany, Raison & Prokushkin (2006), revisão crítica de razões raiz:parte aérea: https://doi.org/10.1111/j.1365-2486.2005.001043.x
- Martin et al. (2021), frações de C de madeira morta: https://doi.org/10.1038/s41467-021-21149-9
- IPCC, incerteza e propagação: https://archive.ipcc-nggip.iges.or.jp/faq/faq.html
- ISRIC SoilGrids 2.0, camadas e quantis: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html

## Situação e próximos passos
- **Não há, neste registro, aprovação do gate nacional nem dados de acurácia local.**
- Reacquirir e verificar bytes/licença dos arquivos oficiais SFB; reconstruir os resumos a partir dos dados brutos.
- Completar a análise experimental de AGB e necromassa por capacidades/biomas que tenham dados e variância, e manter os estratos incompatíveis como N/D.
- Recuperar pares gravimétricos para serapilheira, perfis licenciados para solo no escopo autorizado, amostras rotuladas para culturas e pareamentos SAR atuais com campo.
- Implementar o gate de piloto experimental e conectar o status à interface; depois executar build e CI no mesmo SHA. Até então, não declarar gate aprovado.
