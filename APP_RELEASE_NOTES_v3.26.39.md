# Enform Verde 3.26.39-PRECAMPO-EXPERIMENTAL

## Correções candidatas

- O classificador SAR anual consulta MPC e INPE. Para não misturar radiometrias, seleciona uma única fonte e órbita pela cobertura mensal; MPC é desempate. Assets RTC do INPE são lidos diretamente sem token SAS MPC.
- O classificador brasileiro ENFORM_SAR_BRASIL_RF_V2 (36 preditores mensais, 12 meses agrícolas) pode agora receber pares VV/VH do INPE quando o MPC não cobre a série.
- O fallback condicional de inventário reutiliza o resultado SAR da análise e não reinicia o pipeline.
- Falha ao atualizar o mapa mantém a última imagem óptica válida.

## Evidência atual

- Regressões locais de contrato incluem GeoTIFFs sintéticos para os doze meses e teste para o uso de INPE sem token MPC.
- Prova live com Sentinel-1 RTC real no recorte de 0,03 grau próximo a Sinop: 30 cenas, 12 meses de 2025/2026, 1.692 pixels e polígonos experimentais. O recorte tem 1.084,73 ha e não é o KML original da Fazenda Maria Eduarda.
- A prova não valida a fazenda inteira nem a acurácia local; estimativas permanecem experimentais e sem validação de campo.
- Build Windows e suíte completa no commit final ainda pendentes. Não homologado.
