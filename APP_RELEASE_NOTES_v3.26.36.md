# Enform Verde v3.26.36-PRECAMPO-EXPERIMENTAL

Data: 14/11/2026. Esta versão inicia a correção dos achados preliminares da revisão arquitetural V88.57.

- Todo processamento SAR, inclusive arquivos SAR locais, é encaminhado ao worker em segundo plano; a interface Tk não executa o pipeline de pixels no thread principal.
- A contingência por inventário reutiliza uma única leitura/processamento SAR e o certificado AOI-wide entre interseções de fitofisionomia, evitando repetir aquisições equivalentes.
- Foram acrescentados contratos de regressão para o caminho SAR local no worker e para a reutilização do resultado SAR no fallback.

Status de evidência: as alterações aguardam CI Windows e suíte de dashboard neste commit. O KML integral da Fazenda Maria Eduarda até o dashboard não está incluído nesta verificação. A homologação científica independente permanece reprovada por falta de medições de campo. Manter pré-campo experimental; não homologado.
