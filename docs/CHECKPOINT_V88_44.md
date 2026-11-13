# Checkpoint V88.44 — Enform Verde

Data: 13/11/2026  
Versão candidata: `3.26.30-PRECAMPO-EXPERIMENTAL`  
Base remota verificada: V88.43, SHA `431833f1cec7693d8892d5a615cdaac02eb8a879`  
Branch: `patches-3.26.6` / PR draft #51; não mesclar.

## Resultado remoto confirmado em V88.43

- Dashboard completo: aprovado.
- Contratos pré-campo: aprovados.
- Máscara SAR experimental de Sinop: aprovada.
- ESA BIOMASS FH: leitura real aprovada no recorte de Sinop.
- Build Windows: bloqueado no teste nacional de SAR. Em Petrolina, o assinador MPC respondeu HTTP 429 e o catálogo INPE RTC não encontrou cena recente. O teste parou sem salvar relatório completo.
- Gate científico: reprovado, pois faltam evidências observacionais independentes e artefato final para auditoria.

## Correções em preparação para V88.44

- Interromper chamadas MPC por AOI quando o signer indicar 429.
- Percorrer os oito AOIs e persistir resultados/diagnósticos por local mesmo com falhas.
- Permitir a construção do pacote pré-campo com o gate nacional reprovado, incorporando `DIAGNOSTICO_SAR_NACIONAL.json` e `STATUS_GATE_SAR_NACIONAL.txt` ao ZIP e declarando a limitação no LEIA-ME.
- Regressões mantêm VV e VH da mesma cena como requisito para `PROCESSADO`.

## Critérios para fechar V88.44

Rodar a suíte completa, coleção, compilação, visualização Windows, leitura de pixels SAR e pipeline/dashboard no mesmo SHA. O artefato pode ser distribuído somente como experimental/pré-campo e deve conter diagnóstico por AOI. Não declarar atendimento a todas as coordenadas/datas do Brasil nem homologação científica sem gates correspondentes.
