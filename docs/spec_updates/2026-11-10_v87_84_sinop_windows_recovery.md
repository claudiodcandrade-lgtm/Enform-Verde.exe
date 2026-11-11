# V87.84 — Diagnóstico e correções específicas para Sinop Fazenda Maria Eduarda — 10/11/2026

## Evidência do relatório real enviado pelo proprietário
- KML: Sinop FAZENDA_MARIA_EDUARDA.kml. Área EPSG:6933: 1.459,91 ha; centroide -11,872667, -55,190498.
- Sentinel-1 RTC: 12 cenas MPC selecionadas; 24 tentativas VV/VH; nenhuma leitura concluída; erros `UnicodeDecodeError` com byte `0xe3`. **Erro técnico de acesso/decodificação no Windows**, não ausência demonstrada de cenas, não 0 ha de floresta.
- Imagem CBERS-4A/Sentinel-2 não apareceu no mapa do usuário, embora teste automatizado de uma caixa pequena perto de Sinop tenha sido aprovado; não há aceite no KML completo.
- Classificação SAR atual, carbono nativo por área, vigor e safra ficaram N/D. Isso é consequência direta da ausência de máscara pixelar contemporânea, não evidência de que todos os compartimentos não existam.
- Solo e dados de fertilidade independentes foram apresentados, o que confirma funcionamento parcial dos acessos espaciais e não prova estoque de carbono nativo.

## Correções implementadas no código
- `recent_sar_landcover.py` e `sar_landcover_lemplus.py`: a terceira tentativa de leitura de cada cena usa assinatura por ativo e transporte HTTP/1.1 com `CPL_VSIL_CURL_USE_HEAD=NO`, `GDAL_HTTP_MULTIRANGE=NO` (configuração inválida; substituída por `SERIAL` no V87.92), `GDAL_HTTP_MERGE_CONSECUTIVE_RANGES=NO`. Quando o GDAL Windows emite erro nativo não UTF-8, reter diagnóstico `GDAL_NATIVE_ERROR_NON_UTF8`; não chamar ausência de cenas.
- `desktop_app.py`: CBERS-4A/WFI, Sentinel-2 Earth Search e Sentinel-2 Planetary Computer utilizam configurações COG de requisições simples, sem multipartes. Não ignorar exceções de leitura nem declarar imagem pronta sem pixels.
- `desktop_app.py`: eliminar ciclo de carregamento por comparação equivocada entre tamanho da imagem (requisição) e tamanho do canvas (área visível). Uma atualização obsoleta não deve se sobrepor à imagem já carregada.
- A cada busca de imagem, registrar `~/.enform_verde/ultimo_diagnostico_imagem_otica.json` com o provedor exibido e causas por fonte, com URLs e parâmetros assinados redigidos. Isso permite localizar falha no Windows do proprietário sem expor segredos.
- No quadro IBGE, distinguir textualmente **fitofisionomia potencial IBGE** (Floresta Estacional Sempre-Verde) da **presença de vegetação nativa atual**, que ainda depende de máscara SAR. Não reportar 100% nativa com base apenas em legenda potencial.
- `tests/test_sinop_windows_recurring_failures.py`: regressão de transporte SAR, ordem/diagnóstico óptico, prevenção de recarga circular e distinção fitofisionomia potencial. Testes unitários de arquitetura não substituem provas de aquisição no KML real.

## Pendências e decisão de liberação
- As configurações alternativas são uma hipótese técnica de recuperação, NÃO confirmação de que o `UnicodeDecodeError` de 0xe3 foi superado no PC do usuário.
- Para considerar corrigido: Windows EXE, KML completo Fazenda Maria Eduarda, imagem óptica exibida com provedor identificado; pelo menos três aquisições Sentinel-1 VV/VH legíveis e máscara semântica experimental explícita (requisitos temporais próprios do classificador), distinção de nativa/cultivada e relatórios carbono/safra com N/D justificado quando sem medição independente.
- Carbono nativo total deve permanecer N/D se a área nativa atual ou parâmetros por compartimento forem desconhecidos; exibir resultados experimentais e referências sem apresentá-los como estimativas observadas ou IC95%.
- Não considerar release funcional nacional apenas porque uma amostra próxima a Sinop e a CI Windows passaram; registrar status de avaliação real da propriedade como **PENDENTE**.
