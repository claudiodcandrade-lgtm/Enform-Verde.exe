# Enform Verde 3.26.11-PRECAMPO-EXPERIMENTAL — 10/11/2026

## Escopo técnico

Esta revisão corrige regressões relatadas no Windows para a Fazenda Maria Eduarda (Sinop/MT, 1.459,91 ha), sem declarar resultados quantitativos para a fazenda ainda não observados. A versão 3.26.10 passou pela CI, mas o teste real do proprietário mostrou que a interface óptica, a aquisição SAR e as estimativas dependentes de máscaras não estavam operacionais nesse ambiente.

## Correções de código
- `sentinel1_mpc.sign_asset_href`: rota autenticadora independente por ativo, que não depende exclusivamente de SAS global da coleção; valida HTTPS e host autorizado.
- `recent_sar_landcover`: a falha do token da coleção não elimina automaticamente todas as cenas; no retry de erro de COG utiliza assinatura individual.
- `sar_landcover_lemplus`: a mesma contingência aplicada à aquisição de VV/VH dos 12 meses para o classificador RF experimental, sem atribuir a safra anterior ao mês atual.
- `desktop_app`: alternativa óptica Esri World Imagery depois de CBERS-4A, Sentinel-2 e NASA VIIRS; informa que o mosaico Esri tem data e sensor N/D e não fornece observação analítica SAR.
- `desktop_app`: cabeçalho em plural «Fitofisionomias presentes na propriedade» e remoção da linha duplicada «Outros usos = 0,00 ha» quando a cobertura não está classificada.
- Testes de contrato de assinatura por ativo com checagem de host/URL; smoke test real SAR de Sinop rodou em área de referência fora do KML completo da fazenda.

## Critérios objetivos de aceite

A compilação Windows e a regressão devem passar **no mesmo SHA desta versão**, com artefato ZIP, checksum e autoteste EXE. O operador deve confirmar no KML integral a apresentação da imagem óptica no canvas e o processamento contemporâneo Sentinel-1 VV/VH. O modelo anual 2025/26 é experimental retrospectivo; cultura, vigor, carbono e safra atuais só podem ser estimados quando houver bases compatíveis. Ausência técnica ≠ ausência de vegetação/cultura. Carbono de solo 0–100 cm não pode ser substituído por 0–30 cm.

## Limites científicos

O processamento real de SAR em pequena caixa de Sinop e o FH ESA BIOMASS não estabelecem classificação da propriedade nem validam AGB local. Sem máscara atual, os compartimentos dependentes dela permanecem N/D. A validação independente e a calibração agronômica nacional são futuras, sem inventar IC95% nem evidências de campo. Verificar licenciamento de fontes cartográficas antes de exploração comercial.
