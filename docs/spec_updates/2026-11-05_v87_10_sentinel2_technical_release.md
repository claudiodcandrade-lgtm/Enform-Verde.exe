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


## REVISÃO V87.11 — CORREÇÃO OPERACIONAL CAR/KML — 05/11/2026
Identificador da aplicação: `3.26.2-PRECAMPO-EXPERIMENTAL`. O erro reportado em propriedade real foi `name 'redraw' is not defined`: ao importar KML testado ou consultar CAR, o perímetro abria, mas `_show_geom` não completava seu fluxo. A rotina `desktop_app.py::_schedule_offline_map_fit` chamava uma variável global inexistente em `self.after(420,redraw)`. Essa linha foi removida no commit `d99634cf29cb6f6b7d4fb951b5654890dcd1e456`; desenho imediato da AOI, busca online e fallback offline já ocorriam sem ela. Com isso, a preparação passa a alcançar inicialização do diagnóstico IBGE e o caminho posterior de análise, sujeito a disponibilidade das fontes. Regressão automática `tests/test_car_kml_map_setup_regression.py` verifica a inexistência do callback solto e o fluxo comum de CAR/vetor. Manter o histórico, as funções de Sentinel-2 e SAR, os seis biomas, carbono 0–100 cm, fertilidade, agricultura e modelos pré-campo. Nova distribuição só pode ser declarada corrigida após testes de integração reais e build Windows verificado no mesmo SHA; não confundir correção de NameError com homologação científica.
