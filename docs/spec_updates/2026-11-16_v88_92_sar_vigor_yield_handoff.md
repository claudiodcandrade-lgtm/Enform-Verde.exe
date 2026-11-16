# V88.92 — vigor SAR condicional conectado à previsão de safra

## Caminho matemático e passagem até o painel

Para máscaras agrícolas anuais SAR experimentais, o sistema pode avaliar o sinal estrutural relativo de uma aquisição Sentinel-1 VV/VH atual (idade máxima de 30 dias) em blocos espaciais da máscara da safra anterior. O desenho cria blocos-alvo e referências internas não sobrepostas; exige pelo menos seis referências espacialmente válidas por alvo. Esses blocos não são talhões independentes, validação de campo nem confirmação de que a cultura permaneceu no local.

As probabilidades das três classes de vigor SAR relativo alimentam o modelo de produtividade existente. O modelo combina histórico de rendimento IBGE/PAM em escala microrregional, resposta climática e hídrica FAO-56/FAO-33 com NASA POWER e, quando elegível, o tercil correspondente de resíduos de validação temporal do painel. Os valores e a proveniência entram no relatório de auditoria e no quadro executivo; a máscara anual permanece retrospectiva e condicional. A transferência de área/cultura para a safra corrente é explicitamente `NAO_QUANTIFICADA` e não integra o intervalo numérico de produtividade.

O processamento reutiliza uma consulta Sentinel-1 por cultura/AOI e token em memória por execução, sem repetir a busca para cada bloco. Cada alvo ainda precisa passar pelas verificações próprias de cena, par VV/VH, idade, cobertura e pixels válidos. Com menos de sete blocos utilizáveis no total ou menos de seis referências que atendam ao raio/pixels mínimos, o vigor é `N/D`; a previsão continua sem vigor, com esse estado identificado.

## Domínio e validação

O artefato de produtividade disponível nesta candidata contém modelos para soja e milho. As demais culturas prioritárias não devem receber esse modelo por analogia: permanecem N/D para estimativa específica até existir artefato e dados históricos compatíveis. A validação out-of-sample do modelo usa leave-one-year-out da série PAM; não é validação independente de produtividade ou vigor em campo na propriedade. O classificador de cultura possui envelope espacial de treinamento, e rótulos específicos continuam bloqueados fora desse domínio. Os sinais de vigor são experimentais, relativos a referências SAR internas, não diagnóstico fitossanitário, altura do dossel ou vigor agronômico calibrado.

## Verificação desta alteração

38 testes focados de contrato SAR-vigor-safra, modelo PAM/clima e balanço hídrico passaram localmente; compilação dos módulos alterados e `git diff --check` passaram. Inclui teste de blocos disjuntos, insuficiência de amostra, passagem das probabilidades ao modelo e proveniência no painel/auditoria. Essa validação não inclui busca live Sentinel-1, execução Windows, EXE, KML privado integral da Fazenda Maria Eduarda, CI remota ou validação de campo. A versão `3.26.50-PRECAMPO-EXPERIMENTAL` não é homologada.
