# Revisão V87.9 — Sentinel-2 aberto, desempenho do preview e candidato 3.26.2

Data: 05/11/2026 (UTC). Versão do aplicativo: `3.26.2-PRECAMPO-EXPERIMENTAL`.

## Decisão de visualização
O mapa de entorno deve usar imagens ópticas. A camada SAR/radar permanece exclusiva das análises e não deve ser apresentada como fundo óptico.

## Fontes e fallback
Prioridade: Earth Search STAC/AWS com Sentinel-2 L2A público e sem credencial do usuário; Microsoft Planetary Computer Sentinel-2; NASA GIBS VIIRS True Color; Esri World Imagery; Esri Street Map; por último, mapa IBGE offline. Google Maps pode ser usado somente quando o usuário configurar uma chave válida; chave oficial não é gerada automaticamente. O fallback avança quando uma fonte falhar.

## Resolução e desempenho
Preview RGB usa B04 vermelho, B03 verde e B02 azul, cada banda com resolução nominal de 10 m. Ler os COGs por HTTP range e limitar a requisição à janela do AOI/viewport, reamostrando diretamente para as dimensões do canvas. Executar as três bandas em concorrência limitada (máximo três workers, cada um com seu próprio leitor/rasterio Env). Não baixar cena completa nem criar quadrantes arbitrários quando uma janela do COG atende ao viewport. Mosaicagem de cenas multi-telha deve limitar-se às telhas que intersectam o recorte visível. Não declarar ganho de velocidade sem benchmark reproduzível; medir latência, bytes, memória de pico e completude espacial.

## Estado de teste e correção necessária
No commit `4b729bbb28d33ec2598cc2b5ee08c44d6fd5cd3e`, 924 testes da suíte completa passaram e um falhou: a especificação Word versionada não continha a string da versão atual. O build Windows também parou na mesma validação documental. Atualizar este DOCX via workflow sincronizado, validar integridade ZIP e presença da versão, e rerodar regressões/build no novo SHA. A liberação do EXE só ocorre após ambos passarem no mesmo SHA e após confirmar artefato, checksum e smoke test.

## Limites da liberação
O preview de satélite é contexto visual, não entrada para estimativas. Os módulos agrícolas e de carbono permanecem sujeitos às suas próprias evidências. A homologação científica independente segue reprovada enquanto faltarem observações verificadas; a versão deve permanecer claramente identificada como experimental/pre-campo.
