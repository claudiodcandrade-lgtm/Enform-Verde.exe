# V88.151 — seleção FH e calibração do ESA CCI

Data: 18/11/2026  
Base: Enform Verde v3.26.71, branch `patches-3.26.6`  
Commit de código: `9112bde95714a27ea1856a32ff76213d181582f6`

## Correção realizada

O gate de seleção do ESA CCI foi alterado para cumprir a precedência FH:

- qualquer pixel FH válido bloqueia a promoção do CCI;
- ausência real de FH deve estar certificada por auditorias completas, paginação e leitura de pixels sem erro em todas as rotas prioritárias;
- CCI exige calibração com inventário compatível, ≥30 pares parcela–pixel, ≥5 sítios independentes, domínio explícito, fonte, validação independente e RMSE positivo;
- sem calibração, não se usa o AGB bruto do CCI como estimativa final.

Foram adicionados testes que cobrem as novas condições. A bateria local de `tests/test_sar_height_absence.py` passou (9 testes).

## Estado de calibração e release

A base IFN expandida no pacote Windows contém observações DAP≥10 e associação espacial com legenda_1, mas não traz os pares co-registrados ESA CCI/FH–parcela nem AGB de referência auditada necessários à calibração microrregional. O painel AGB IFN-MT existente tem os marcadores de auditoria/validação desativados. O pipeline ainda não carrega registro de calibração CCI elegível. Assim, o CCI fica corretamente impedido de produzir resultado; a nova regra não é uma calibração e não torna a função científica operacional nacional.

A calibração FH + parâmetros horizontais é comprovada apenas nos domínios específicos existentes no código; não foi demonstrada para cada microrregião/fitofisionomia. A biomassa radicular continua com equação generalizada de Cairns et al. para florestas altas, sem seleção regional completa e sem incerteza total.

## Critérios de fechamento

1. Preparar inventários de fontes confiáveis com coordenadas, área/desenho amostral, data, identidade da parcela e AGB de referência auditada.
2. Extrair FH e CCI coincidentes por parcela; harmonizar resolução, épocas, máscara e unidade.
3. Ajustar modelos separados por bioma e IBGE `legenda_1`; validar por sítios que não participaram do ajuste.
4. Reportar viés, RMSE, MAE, R², erro de transferência e intervalos com cobertura verificada.
5. Implementar registro persistente e seleção de modelo no motor; testar pipeline completo e EXE.
6. Selecionar equações/razões de raízes por formação ecológica e propagar a incerteza ao estoque total.

**Classificação atual:** correção de regra de seleção submetida a CI; versão científica permanece experimental e não homologada. Não rotular a calibração ESA CCI/FH nacional como concluída.
