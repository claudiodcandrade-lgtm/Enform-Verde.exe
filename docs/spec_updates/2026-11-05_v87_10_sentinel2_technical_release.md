# Revisão V87.10 — liberação técnica verificada 3.26.2

Data: 05/11/2026. Aplicativo: `3.26.2-PRECAMPO-EXPERIMENTAL`. SHA do código e da distribuição: `b4055ebbbfc9394616658c2c215603087dd5a60e`.

## Preview de entorno Sentinel-2
A janela de entorno usa exclusivamente imagem óptica. Earth Search/AWS Sentinel-2 L2A público é a rota automática prioritária sem chave do usuário; depois Planetary Computer, NASA GIBS VIIRS, Esri World Imagery, Esri Street Map e mapa IBGE offline. Google Maps é opcional somente com chave válida fornecida pelo usuário; nenhuma chave é gerada automaticamente. SAR/radar permanece separado e reservado às análises.

As bandas RGB Sentinel-2 B04/B03/B02 têm resolução nominal de 10 m. Leitura COG usa HTTP range limitada à janela AOI/viewport, reamostragem direta ao canvas e até três leitores paralelos independentes. Evita download da cena completa e quadrantes arbitrários. AOIs que cruzam telhas devem processar apenas telhas intersectantes. Não divulgar ganho percentual sem benchmark medido.

## Resultado de integração, regressão e executável
No mesmo SHA `b4055ebbbfc9394616658c2c215603087dd5a60e`:

- dashboard: suíte integral aprovada, 925 testes;
- Windows: build aprovado, incluindo prévia Sentinel-2 real para Tapajós e testes de integração;
- EXE testado em cópia limpa; checksum do executável registrado;
- artefato Windows: `Enform-Verde-Windows-v3.26.2-PRECAMPO-EXPERIMENTAL`;
- SHA-256 do executável: `8af9e7445b77cad603f94877befb510359f7b5564df60a451b57a4f86aa8c1a4`;
- digest SHA-256 do ZIP do artefato: `6aa511d6b5e864d23bec6bcf088f922ca07850a6bc0e3066a97f529492640ab5`.

## Limites científicos
Este marco libera uma compilação técnica experimental para testes. Não representa homologação científica independente. O gate científico permanece não aprovado por ausência de evidências observacionais suficientes; estimativas experimentais devem permanecer identificadas e com incerteza/limitações explícitas.
