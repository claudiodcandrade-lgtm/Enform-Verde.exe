# V88.04 — causas de falha TLS e contorno de KML 3D; evidência de pixels em Sinop (12/11/2026)

## Causas concretas corrigidas
- `tls_setup.merged_ca_bundle` filtrava qualquer caminho que contivesse a substring `certifi`. O caminho do certificado do sistema `/usr/local/share/ca-certificates/...` também contém essa sequência, descartando a CA confiável usada pelo proxy TLS e causando falha de leitura de COG SAR. A comparação agora exclui apenas o caminho exato do bundle do pacote `certifi`; a verificação TLS segue habilitada.
- CBERS-4A e NASA GIBS desempacotavam coordenadas de contornos em pares `(x, y)`. KML da fazenda contém `(longitude, latitude, altitude)`, gerando `ValueError: too many values to unpack` depois de a cena ter sido lida. O desenho agora usa somente longitude/latitude, sem alterar a geometria de análise ou os cálculos de área.
- MapBiomas: após erro específico de abertura `/vsicurl/`, o programa pode baixar o GeoTIFF publicado via HTTPS para cache, validar o arquivo e reaplicar o recorte de pixels da mesma AOI. Permanece uma referência histórica, condicionada ao esgotamento auditado das rotas SAR.

## Evidências e limites
- Suíte local completa: 1.082 testes aprovados, 1 ignorado. Coleta/importação: 157 módulos. Testes direcionados TLS, KML 3D e MapBiomas: 10 aprovados.
- Processamento direto do KML completo de Sinop pelo LEM+ leu 2.278 pixels válidos em 30 aquisições e retornou classificação sazonal experimental para 1.457,92 ha; 1,99 ha sem classe. É evidência de leitura e classificação sazonal nessa execução, não acurácia de campo nem prova de que a GUI tenha atualizado o painel.
- A correção do contorno óptico passou no teste geométrico 3D, porém a imagem óptica ao vivo do KML integral não foi confirmada após o patch. A visualização do aplicativo, altura de dossel, carbono e agricultura no painel completo seguem pendentes de teste no Windows.
- O classificador serializado informa scikit-learn 1.8.0; o ambiente integral usou 1.9.1 e emitiu aviso de incompatibilidade. A execução permanece experimental e não deve ser tratada como validação do modelo.
- A verificação visual GUI local não rodou por falta de display. Build Windows e EXE não foram gerados neste checkpoint. Não anunciar versão Windows concluída ou homologação científica.
