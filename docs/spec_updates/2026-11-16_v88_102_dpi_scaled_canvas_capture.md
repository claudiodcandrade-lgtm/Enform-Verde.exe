# V88.102 — captura DPI do canvas Windows

## Evidência da rodada anterior

A CI V88.101 passou a suíte integral, o fluxo SAR real Sinop/Tapajós, a prova ESA BIOMASS FH e a cobertura óptica nacional. O smoke final do canvas terminou em timeout. A observação final mostrou `canvas_viewable=true`, um item de imagem Sentinel-2 e `visible_fraction=0.0498`.

A discrepância sugere que o recorte do Pillow ImageGrab usou coordenadas Tk lógicas como coordenadas físicas da tela em runner Windows com escala DPI. A causa ainda é hipótese até a nova captura ser aprovada.

## Correção

O smoke captura a tela e escala as coordenadas do canvas pela razão entre as dimensões capturadas e as dimensões de tela reportadas pelo Tk. O JSON registra tamanho do widget, da foto, da tela Tk, da captura e o retângulo recortado. Se o gate falhar, o workflow preserva um PNG do recorte para inspeção.

## Validação necessária

Doze testes focados passaram localmente, incluindo escala 1,5× e escala 1×; compilação do módulo passou. A suíte completa, pixels SAR integrados, smoke óptico final do canvas e build/autoteste Windows ainda precisam passar. A candidata continua pré-campo e não homologada.
