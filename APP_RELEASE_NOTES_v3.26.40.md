# Enform Verde v3.26.40-PRECAMPO-EXPERIMENTAL

## Correções da candidata

- A leitura anual do Sentinel-1 MPC ganha uma quinta rota de transporte: descarga binária HTTPS limitada e recorte da AOI em GeoTIFF. Ela contorna respostas de erro do GDAL/Windows que chegavam como `UnicodeDecodeError` em `open_cog`, sem desligar TLS nem converter erro em ausência de dados.
- A contingência radar L/X/NISAR agora é chamada quando a classificação semântica principal não foi aplicada, mesmo que a triagem tenha lido pixels Sentinel-1. Pixel disponível não é mais confundido com classe semântica disponível. O relatório registra o motivo do gatilho; a contingência continua sem autorizar classe nativa/cultivo sem validação.
- O fundo óptico só é armazenado, desenhado ou reutilizado do cache se os pixels têm brilho e contraste mínimos. Imagens pretas/brancas são rejeitadas e levam ao próximo provedor; entradas antigas inválidas são descartadas. Se todos falharem, o mapa mostra o perímetro em fundo claro e o motivo.

## Escopo e validação

- O modelo LEM+ continua experimental; pixels de triagem e a execução do classificador são etapas distintas. Sem os pares mensais necessários, o sistema mantém N/D com os meses/provedor e erro, sem inventar máscara ou hectare.
- A primeira suíte integral identificou e corrigiu um contrato de teste legado que ainda fixava quatro tentativas SAR; a nova execução precisa passar. A candidata também precisa passar o contrato de coleta, CI, build Windows e testes live de imagem real no canvas e de SAR MPC/INPE. A aprovação local de regressões não comprova o KML integral privado da Fazenda Maria Eduarda, nem validação de campo.
- Status pré-campo experimental; não homologada até a evidência operacional e científica requerida.

## Ajuste do smoke Windows

A primeira execução do smoke gráfico rejeitou uma fixture antiga uniforme, conforme o controle de imagem sem textura. O fixture foi substituído por RGB com variação espacial e uma regressão impede retorno à cor sólida. A suíte local da regressão passou; build Windows, teste live do canvas e handoff SAR devem ser aprovados no SHA atualizado.
