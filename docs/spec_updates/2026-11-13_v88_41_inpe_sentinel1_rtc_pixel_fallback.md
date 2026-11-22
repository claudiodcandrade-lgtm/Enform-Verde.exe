# V88.41 — contingência INPE para Sentinel-1 recente

Versão do programa: 3.26.27-PRECAMPO-EXPERIMENTAL.
## Diagnóstico
O catálogo aberto do INPE já era descoberto em módulos de classificação/vigor, mas o pipeline principal SAR de biomassa não lia seus COGs como rota independente. Além disso, as consultas atuais do pipeline de carbono e a aceitação de rede tinham janela superior a 30 dias. O usuário exige SAR recente tanto para carbono quanto para monitoramento agrícola/previsão de safra.
## Correção de integração
Adicionar leitor real de pixels VV/VH da coleção INPE `sentinel-1-rtc-1` com TLS verificado, ativos restritos ao domínio oficial, recorte da AOI e diagnóstico de catálogo versus abertura versus pixels válidos. Consultar INPE mesmo se MPC tiver sucesso para comparar aquisição real; executar MPC/INPE/CDSE com janela instantânea de 30 dias. O monitoramento agrícola conserva série fenológica de até 150 dias, mas exige última aquisição com até 30 dias. Erro de transporte não se transforma em ausência.
## Aceite verificável
Teste local com GeoTIFF de fixture deve exigir par VV/VH real no recorte. Teste live obrigatório em CI exige pelo menos 100 pixels por polarização em mesma cena INPE para Sinop e Tapajós, registra IDs/datas/CRS/contagens sem credenciais e reprova o build se não houver pixel. `--network-check` exige Sentinel-1 VV/VH até 30 dias. CI no SHA final ainda pendente.
## Limite
A leitura recente de Sentinel-1 C-band é auxiliar e não produz AGB isoladamente. Estimativa quantitativa precisa de produto ou modelo compatível e evidência de inventário/calibração adequada. A disponibilidade e atualidade são atestadas por AOI e execução; esta mudança não homologa o produto.
