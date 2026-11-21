# Enform Verde v3.26.27-PRECAMPO-EXPERIMENTAL

## Sentinel-1: integração de fallback público do INPE com leitura de pixels

- A rotina principal de evidência SAR tenta Microsoft Planetary Computer e, se não obtiver pixels reais VV/VH, consulta a coleção pública Sentinel-1 RTC do INPE e lê seus COGs diretamente.
- O painel/auditoria distingue descoberta de cenas da leitura real: somente pares VV/VH com pixels válidos dentro da AOI recebem `PROCESSADO`.
- A falha de uma fonte é registrada e não é confundida com ausência de cenas; a cadeia continua para as fontes subsequentes.
- O Sentinel-1 C-band fornece evidência SAR auxiliar. Não se converte retroespalhamento isolado em AGB sem equação compatível, calibração e validação independente.
- Novo teste de aceitação consulta o INPE e exige leitura real VV/VH em Sinop e no KMZ de aceitação do Tapajós; salva data de aquisição, cena, CRS e contagem de pixels sem armazenar URLs temporárias ou credenciais.

**Status:** candidata pré-campo experimental. A disponibilidade por provedor e a atualidade são verificadas por execução; nenhum SLA é presumido. Não homologado.
