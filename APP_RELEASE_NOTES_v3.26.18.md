# Enform Verde 3.26.18-PRECAMPO-EXPERIMENTAL

## Integração do classificador sazonal SAR ao diagnóstico do aplicativo

- O classificador Sentinel-1 LEM+ executado pelo aplicativo registra se foi chamado para a AOI integral, se as classes foram incorporadas, além de safra, cenas/pixels, área/hash da geometria e diagnóstico de aquisição.
- O relatório de uso do solo e o painel executivo mostram o estado do LEM+ separadamente da triagem SAR recente. Falhas de aquisição deixam motivo e erros por cena visíveis.
- Quando um classificador anterior já fornece classes, o LEM+ fica explicitamente como `NOT_EXECUTED` e com escopo não executado. Esse estado não conta como esgotamento SAR.
- A contingência MapBiomas + PAM fica bloqueada se qualquer rota estiver ausente, não executada ou sem um estado terminal conhecido.
- O artefato de CI em caixa de teste permanece separado do aplicativo; não é importado como resultado da fazenda. O runtime realiza sua própria execução na AOI carregada.

## Evidência e limites

- Compilação sintática passou. A suíte completa executou 1.071 testes: todos passaram e 1 foi ignorado. Inclui a regressão que prova `NOT_EXECUTED` quando o classificador prévio já fornece classes SAR.
- `python tools/check_test_collection.py` aprovou 156 módulos; o contrato documental passou após sincronizar a versão Word. `ui_visual_standard.py` não pôde iniciar por ausência de `DISPLAY`.
- Não houve execução do KML integral da Fazenda Maria Eduarda no Windows nesta revisão. A integração do diagnóstico não comprova acesso a provedores, leitura COG, classificação da fazenda nem geração de carbono. Não declarar versão operacional antes da prova de pixels reais na AOI integral e do build Windows.


## Resultado do build Windows e dos testes em AOIs de aceitação

- Build Windows concluído para o commit de código `b8ef8f04221f92fefad74021f0f831d4555706a7`; compilação e autoteste do EXE em cópia limpa passaram.
- SHA-256 do EXE: `497ad17b2a2e310def6f995b76c42dc94bbcb7df1a23e4f3ede30fed01c8b7a2`. Baixar o ZIP de 533.413.242 bytes pelo artefato Actions ID `13893354363`; digest do ZIP `afdcd2a2dc37b9d371b9a9716dcecf3e7b1c0d6be55ab205f2211c53148b4e6e`.
- O smoke do EXE leu CBERS-4A e Sentinel-1 em AOI de teste; a aceitação SAR do KMZ Tapajós processou 1.290,688 ha, 302.348 pixels e 5 cenas, sem AGB fallback. Isso não comprova estoque de carbono nem valida o KML integral da Fazenda Maria Eduarda.
- Dashboard: 1.071 testes aprovados, 1 ignorado. Homologação científica continua reprovada por ausência de evidência independente suficiente.

## Correção do contrato de smoke óptico (11/11/2026)

- O smoke de interface agora aceita a alternativa Sentinel-2 quando CBERS-4A não está disponível, desde que a imagem esteja visível e desenhada no canvas; cartografia e outros provedores não satisfazem o teste.
- Alteração limitada ao CI e à documentação. Não modifica o executável 3.26.18 nem comprova processamento do KML integral da Fazenda Maria Eduarda. Um artefato atualizado exige novo build Windows aprovado.
