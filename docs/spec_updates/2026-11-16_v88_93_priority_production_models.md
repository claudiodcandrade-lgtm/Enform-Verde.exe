# V88.93 — inclusão integral dos cultivos e sistemas produtivos prioritários (15/11/2026)

## Escopo de alvos

O registro executável passa a contemplar soja, milho, arroz, algodão, sorgo, cana-de-açúcar, café, feijão, citros, pastagens, silvicultura/florestas plantadas e ILP, IPF e ILPF. Cada alvo traz unidade de produção, equação/rota, entradas exigidas, estado e bloqueios próprios. Os modelos de grãos não são reutilizados para forragem, madeira ou sistemas integrados.

## Rotas matemáticas e dados

- Soja e milho: preservado o painel experimental PAM microrregional + rendimento relativo hídrico FAO-56/FAO-33, tendência tecnológica por microrregião, erro de hindcast por safra e condicionamento por vigor SAR quando elegível. O artefato versionado atual contém somente essas duas culturas. A previsão continua experimental e não equivale a homologação de campo.
- Arroz, algodão, sorgo, cana, café, feijão e citros: encaminhados ao cenário experimental PAM microrregional + clima + classe de vigor, com calendário/Kc por cultura e propagação Monte Carlo já existente. Não são declarados painéis calibrados específicos. Algodão herbáceo (em caroço; produto SIDRA 40099) é consultado na API pública SIDRA para a microrregião quando ausente da série local empacotada; sem resposta ou histórico suficiente, permanece N/D, sem substituição por média nacional/municipal.
- Pastagens: calculadora separada de matéria seca, Σ(10 × PAR × RUE × fIPAR × fágua), em kg MS/ha por período. Requer radiação PAR, fração interceptada, estresse hídrico e RUE específica da espécie/local. Só propaga erro de RUE quando sua dispersão é informada; declara “incerteza não mensurável” quando faltam erros suportados. PAM pecuária não é tratada como produtividade de forragem.
- Silvicultura: calculadora de incremento anual de volume entre dois inventários, (V₂ − V₁)/Δt, em m³/ha/ano, com erro parcial somente quando ambos os inventários informam dispersões. Não projeta madeira futura sem espécie, idade, sítio, manejo e inventário compatíveis; PEVS não substitui dados do talhão.
- ILP/IPF/ILPF: contrato de vetor de componentes e unidades (grão, matéria seca, produto animal e/ou madeira), sem somar grandezas incompatíveis. Interação do sistema fica N/D até haver experimento ou coeficientes e dados de manejo da mesma unidade/período. A coexistência de classes SAR não prova integração.

## Fluxo SAR → modelo → relatório

O contrato do modelo prioritário é inserido no JSON de auditoria para cada alvo; o relatório informa a rota e suas variáveis bloqueantes. Máscaras anuais continuam retrospectivas e não confirmam a safra atual. A máscara e a data SAR, vigor, histórico PAM N9 e clima permanecem identificados separadamente na proveniência. MapBiomas não identifica cultura atual.

## Limites desta candidata

As rotas e cálculos foram incluídos no código. A suíte local completa executou 1.221 testes e passou, com um skip esperado, incluindo o teste live de leitura de pixels. O teste decodificou 9 pixels VV e 9 pixels VH válidos na cena `S1D_IW_GRDH_1SDV_20261112T091635_20261112T091700_005432_00A5E9_rtc`, no recorte pontual de Sinop; medianas nativas VV 0,143119 e VH 0,031320. Os testes direcionados de cultivos, modelos e sistemas integrados passaram (35 testes). compileall, guard documental e git diff --check passaram. Não foi criado coeficiente experimental sem fonte. O aplicativo não tem dados de manejo/inventário para calcular pastagem, silvicultura ou interações ILP/IPF/ILPF automaticamente; nesses casos emite N/D justificado até que os dados entrem na análise. A leitura pontual não demonstra máscara semântica, execução do KML completo até dashboard, consulta live à SIDRA, build Windows, validação independente ou homologação científica.

## Referências específicas para sistemas integrados

A revisão do histórico identificou e conferiu as referências primárias já listadas em PROMPT_CONTINUIDADE_2026-10-24.md:

1. ILP — Embrapa Territorial/Unicamp, Silva et al. (2025), sul do Maranhão, Random Forest com MOD13Q1/MODIS (250 m, 16 dias) e perfis NDVI/EVI SATVeg em janeiro, fevereiro e maio/junho. O artigo usa 518 pontos (259 ILP/259 sem integração), divisão aleatória 333 treino/185 validação e reporta AUC 1,0, acurácia/F1 0,995 e MCC 0,989. Os autores alertam que a amostra pequena e específica pode enviesar os resultados. Referência: https://www.alice.cnptia.embrapa.br/alice/handle/doc/1175472 . O algoritmo entra no catálogo como referência para ILP, com preditores documentados e estado ready=False; não há pesos/dataset reutilizáveis incorporados e não se transfere a métrica para outras regiões.
2. ILPF — Embrapa Solos/UERJ (2025), U-Net com Sentinel-2 e entradas NDVI+RGB, para segmentar áreas com árvores em linhas. O estudo parte de 638 localizações, cria 493 imagens e divide imagens aleatoriamente antes de recortar/aumentar os dados; informa precisão 94,58%, F1 93,91% e IoU 88,15%. A abrangência brasileira do conjunto de pontos é promissora, porém as métricas do artigo não substituem validação independente por bioma/propriedade, e pesos/dados necessários à inferência não estão incorporados ao EXE. Referência: https://www.alice.cnptia.embrapa.br/alice/handle/doc/1178498 . O modelo é rota óptica complementar e não é um classificador SAR.
3. IPF: as duas referências acima não entregam um modelo específico de IPF. O programa deve manter abstenção até possuir dados e modelo/critério validado para esse arranjo.

integrated_system_classifier.py executa verificação conservadora de coocorrência validada na mesma unidade e período e agora admite ILP, além de ILF, IPF e ILPF. Isso é um gate de evidência de manejo, não inferência de imagem nem modelo de produtividade. O relatório recebe essa decisão e o estado do classificador científico; nenhuma produtividade integrada é inferida por esses artigos.

## Auditoria complementar da hierarquia nacional de inventários

A rodada integral de regressão identificou divergência entre a hierarquia documentada e os ranks efetivamente usados. Corrigida para priorizar: (1) parcelas institucionais abertas; (2) resumos institucionais com erro amostral publicado; (3) medições verificadas de bases públicas oficiais; (4) inventário de licenciamento/plano de manejo somente quando o próprio anexo está explicitamente aceito e não há fonte melhor; (5) metadados usados apenas para localizar anexos; (6) registro privado sem aceite, bloqueado para uso numérico. A aprovação do processo não satisfaz o aceite do inventário. Regressões agora conferem ordem e rank emitido pelos avaliadores.

Validação da correção: a suíte local completa executou 1.221 testes, passou com um skip esperado; o teste live passou e leu pixels reais VV/VH em Sinop. O workflow `.github/workflows/build-windows.yml` ganhou uma etapa live bloqueante, com limite de 12 minutos e falha se o serviço de assinatura não estiver disponível. A etapa grava cena, data, contagem de pixels e medianas no log. A CI Windows dessa revisão ainda não foi executada, pois o push remoto não completou.
