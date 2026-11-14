# Enform Verde v3.26.25-PRECAMPO-EXPERIMENTAL

- Corrige uma falha recorrente de leitura Sentinel-1/MPC: após quatro tentativas GDAL, a rota MPC tenta renovar a SAS e transferir o COG por HTTPS verificado para arquivo temporário local, validando status HTTP, limite de tamanho e assinatura TIFF antes da leitura da janela da AOI. O arquivo temporário é removido após a operação; TLS continua habilitado.
- Se a aquisição continuar com erro técnico, o pipeline registra a falha SAR como etapa parcial com classes atuais N/D e deixa os diagnósticos independentes seguirem para o painel. Erros internos, AOI divergente e saída malformada continuam bloqueando publicação.
- O `--network-check` do EXE agora testa separadamente leitura real VV/VH via GDAL e via HTTPS→TIFF local; para MPC, exige ao menos 100 pixels válidos em cada polarização pelo novo leitor antes de aprovar a aceitação de rede.
- A auditoria da Fazenda Maria Eduarda apresentou 13 cenas candidatas, 12 selecionadas e 48 tentativas sem pixels VV/VH válidos, com erros de leitura/HTTPS e token; portanto, confirmou cenas disponíveis com falha técnica de leitura, não ausência de cenas.
- Testes locais dirigidos da rota HTTPS temporária e do contrato de publicação parcial passaram (3 testes). Esta candidata ainda depende dos workflows Windows completos e de nova execução no KML integral; até lá, não declarar leitura SAR ou versão operacional comprovadas.
- Candidata experimental, não homologada cientificamente. Resultados SAR e classes continuam condicionados à leitura real dos pixels e à validação correspondente.
