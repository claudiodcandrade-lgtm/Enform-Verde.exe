# V88.11 — runtime geoespacial disponível e regressão integral (12/11/2026)

## Solução para GeoPandas

- GeoPandas não foi substituído por mock: os testes dependem de operações reais de geometrias, CRS, interseção vetorial e leitura de raster. A solução correta é instalar as dependências declaradas pelo próprio projeto.
- O runtime-base do ambiente não traz o stack geoespacial. Foi criado um diretório temporário isolado e nele foi instalado `requirements_desktop.txt`, sem alterar o Python global nem o ambiente de aplicação.
- Pacotes efetivamente usados: GeoPandas 1.2.0, Shapely 2.2.0, PyProj 3.8.0, Pyogrio 0.13.0, Rasterio 1.5.2, scikit-learn 1.8.0, NumPy 2.5.4 e Pandas 2.3.3. O teste live Sentinel-1 de MPC também concluiu leitura real de VV e VH.
- Os testes offline que ainda permitiam chamadas à contingência radar ou MapBiomas/PAM foram corrigidos para injetar respostas controladas nas rotas externas. Isso remove espera de rede acidental dos fixtures, sem substituir o teste live dedicado.

## Evidência executada

- `PYTHONPATH=/tmp/enform-geo-runtime python -m unittest discover -s tests -v`: 1.085 testes executados, todos aprovados, um skip.
- O skip único foi `test_application_shell_unchanged`, pois não havia servidor gráfico/display (`$DISPLAY`). Os outros três contratos visuais estáticos passaram.
- O teste `test_current_mpc_scene_decodes_real_vv_and_vh_pixels` passou, confirmando nesta execução consulta de cena MPC e leitura de pixels VV/VH reais na área de teste de Sinop. Isso não substitui o smoke visual do EXE no KML integral.
- `python -m compileall -q -x '(\\.git|build|dist)' .` e `git diff --check` passaram.

## Instalação reproduzível

Linux/macOS: criar um `venv`, ativá-lo e executar `python -m pip install -r requirements_desktop.txt`; depois executar `python -m unittest discover -s tests -v`. No Windows, usar `py -3.12 -m venv .venv`, ativar `.venv\\Scripts\\Activate.ps1` e executar os mesmos comandos `pip` e `unittest`. Em instalações Conda, preferir instalar GeoPandas e dependências geoespaciais do canal conda-forge de forma consistente, sem misturar canais.

## Estado das pendências

A falta de GeoPandas no runtime foi resolvida para esta validação e a suíte completa passou. Continuam pendentes gates diferentes: build/GUI Windows no SHA atual, smoke ponta a ponta no KML integral da Fazenda Maria Eduarda, leitura óptica nessa geometria e homologação científica. O único skip local é a captura visual Tk por ausência de display; a evidência visual deve vir de Windows CI ou de sessão gráfica com baseline.
