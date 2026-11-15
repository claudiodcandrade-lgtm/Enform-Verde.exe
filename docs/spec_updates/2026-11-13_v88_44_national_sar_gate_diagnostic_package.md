# V88.44 — diagnóstico nacional SAR e pacote pré-campo auditável (13/11/2026)

## Resultado confirmado no SHA V88.43

No commit `431833f1cec7693d8892d5a615cdaac02eb8a879`, os testes do dashboard, contratos pré-campo e máscara semântica SAR experimental Sinop passaram. A leitura ESA BIOMASS FH real em Sinop também passou. O build Windows chegou à sondagem nacional de pixels e reprovou em Petrolina: havia cenas recentes no catálogo MPC, mas o assinador devolveu HTTP 429 em VV/VH; a coleção RTC do INPE retornou zero cenas nesse recorte. O relatório de oito áreas não foi salvo porque a sondagem parou no primeiro ponto sem par legível. O gate de homologação científica reprovou por falta de evidência independente e artefato final.

## Ajustes na candidata 3.26.30

- Ao receber HTTP 429 do assinador MPC, interromper a busca por cenas antigas no mesmo provedor/AOI e registrar `rate_limited`; não ampliar a carga no serviço enquanto a limitação estiver ativa.
- A sondagem distribuída executa todos os oito AOIs (seis biomas), salva o resultado incrementalmente, sanitiza URLs e devolve código de saída reprovado se qualquer área não tiver par VV/VH recente com pixels válidos. A falha gera relatório por AOI/provedor, não desaparece nem vira sucesso.
- O gate SAR distribuído não bloqueia a compilação do pacote pré-campo. O relatório `DIAGNOSTICO_SAR_NACIONAL.json` e `STATUS_GATE_SAR_NACIONAL.txt` seguem dentro do ZIP portátil, e o LEIA-ME declara que não há garantia de cobertura em toda coordenada/data do Brasil.
- A regressão automatizada verifica que uma resposta 429 interrompe o fan-out por cenas e que uma polarização isolada continua parcial, nunca `PROCESSADO`.

## Limites e aceitação

Permitir a compilação experimental após o gate SAR reprovado não significa que o acesso nacional foi solucionado. Os resultados por AOI precisam ser lidos no diagnóstico do pacote; cada área sem par VV/VH recente mantém N/D/ERRO. A passagem em amostras de Sinop, Tapajós ou outro ponto não prova cobertura em qualquer local do Brasil. O monitoramento de lavouras e a estimativa de carbono devem manter seus limites científicos e não converter banda C isolada em AGB. A versão continua pré-campo experimental, sem homologação. Build, dashboard, sondagem e gate científico serão novamente avaliados no SHA 3.26.30.
