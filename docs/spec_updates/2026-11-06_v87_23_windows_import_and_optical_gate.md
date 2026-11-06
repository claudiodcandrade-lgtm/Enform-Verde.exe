# Enform Verde V87.23 — Windows optical smoke import correction

Data: 2026-11-06 (UTC−3). Base auditada: `f8ebf74f2f7dd0d738e9e8fd4df1bd8e1d504796`.

## Falha reproduzida nos logs

Workflow Windows `42161877660`, job `127709222706`: `python tools/live_optical_coverage_brazil.py` terminou com `ModuleNotFoundError: No module named 'desktop_app'` porque Python inicia `sys.path` no diretório `tools/` ao executar script por caminho. O teste anterior de prévia real Sentinel-2 para Tapajós carregou pixels (`LIVE_SENTINEL2_PREVIEW_OK`), mas isso não comprova disponibilidade nacional.

## Correção material

Inserção explícita da raiz do repositório em `sys.path` antes de importar `desktop_app`. Nenhuma exceção de cobertura foi relaxada: dez AOIs, limiar 95% de cobertura real, relatório JSON e falha quando não houver pixels. A correção apenas elimina o erro de importação; indisponibilidade de catálogo ou pixels ainda pode bloquear o gate.

## Documentação e CI

Atualizados o prompt histórico v43 sem supressão de conteúdo, prompt v52, especificação solo 0–100 cm e workflow de sincronização Word apontando para este checkpoint. SHA final e CI devem ser verificados no commit resultante, inclusive bot Word; os testes Windows, regressões, smoke óptico e artefatos ainda **não estão confirmados** neste checkpoint. A ausência de DOCX atualizado deve bloquear release até o bot concluir e o SHA estabilizar.

## Pendências científicas

Solo: cinco horizontes oficiais brutos 0–100 cm, licença/proveniência, interseção espacial verdadeira AOI×fitofisionomia IBGE×pixels e incerteza. SAR: observações reais e classificação validada independentemente. IFN/SFB: inventários primários microrregionais por fitofisionomia antes de fallback estadual quantificado. Sem dados independentes, reportar N/D e manter homologação científica fail-closed. Nenhum resultado de acurácia ou IC95% foi inventado.
