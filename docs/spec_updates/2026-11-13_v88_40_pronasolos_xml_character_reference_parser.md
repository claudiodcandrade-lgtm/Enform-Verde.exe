# V88.40 — parsing resiliente do XML de capacidades PronaSolos

**Versão do programa:** `3.26.26-PRECAMPO-EXPERIMENTAL`.

## Diagnóstico

O estoque SOC Embrapa/PronaSolos de 0–100 cm foi calculado, mas a leitura das camadas WCS de incerteza parou em `ParseError: reference to invalid character number`. O erro ocorre antes da descoberta das dez camadas (limite inferior/superior para cinco horizontes). Ele caracteriza conteúdo de resposta inválido para XML 1.0, não ausência de serviço ou credencial. Não zerar incerteza nem eliminar o estoque já calculado por esse erro secundário.

## Correção de software

Antes do `ElementTree.fromstring`, inspecionar referências numéricas XML e remover somente aquelas cujo código Unicode não pertence à produção `Char` do XML 1.0. Preservar referências válidas e todo o restante da resposta. O hash SHA-256 da resposta WCS original e a quantidade de referências removidas entram na proveniência. Respostas truncadas, estruturalmente inválidas ou sem as dez camadas continuam como `ERRO_TECNICO`/N/D; nunca são interpretadas como ausência confirmada.

Após a descoberta, manter os contratos existentes: baixar limites inferior e superior para os cinco horizontes, validar formato GeoTIFF, CRS, resolução, NoData, grade alinhada, cobertura da AOI e conteúdo dos rasters. Repetir somente falhas transitórias com tentativas limitadas e TLS validado. Enquanto qualquer requisito falhar, manter estoque SOC quando disponível e exibir sua incerteza como N/D com motivo específico. O envelope marginal publicado não deve ser rotulado como IC95% conjunto.

## Teste e limites

Teste de regressão: referência inválida `&#x0;` é removida, referência XML legal `&#x20;` permanece, e o identificador de cobertura reparado é descoberto. A suíte completa e os workflows devem ser reportados pelo SHA exato antes de atualizar o branch. A candidata 3.26.26 continua pré-campo experimental, não homologada; não declarar resultado de incerteza até leitura de dados reais passar no runtime.
