# Checkpoint V88.43 — Enform Verde

Data: 13/11/2026  
Versão candidata: `3.26.29-PRECAMPO-EXPERIMENTAL`  
Branch pretendida: `patches-3.26.6` (PR draft #51; não mesclar)

## Feito nesta etapa

- Corrigido o contrato de pixels MPC: processamento completo requer VV e VH da mesma aquisição. Polarização única permanece em diagnóstico parcial e não alimenta o handoff como par SAR processado.
- Limitador de tentativas transitórias MPC atualizado e coberto por teste: até três chamadas, respeito a `Retry-After`, TLS ativo.
- Regressão do fluxo core → fila → apresentadores reais e auditoria agrícola preservada; data de aquisição aparece no painel de carbono.
- Prompt v43/v52, especificação de solo, especificação técnica Word, atualização V88.43 e notas 3.26.29 atualizados.
- Testes locais: `python -m unittest discover -s tests` — 1.145 aprovados, 1 ignorado por ausência de display. `python tools/check_test_collection.py` — 168 módulos. Compilação dos módulos alterados passou.

## Pendências que bloqueiam declarar funcionamento comprovado

- A consulta live desta sessão não conseguiu decodificar pixels; MPC apresentou timeout e INPE falhou com erro HTTP transitório. Catálogo com cenas não equivale a leitura de pixels.
- A checagem visual Tk precisa do runner com display/Windows.
- Build, teste live multiprovedor nas 8 AOIs dos seis biomas e execução do KML integral da Fazenda Maria Eduarda até o dashboard aguardam CI/Windows no SHA final.
- Amostras nos seis biomas não garantem cobertura em qualquer coordenada ou data do Brasil; cada AOI exige auditoria própria e N/D/ERRO explícito.
- Homologação científica continua reprovada até validação observacional independente. Não anunciar o programa como homologado nem conexão SAR como resolvida antes dos gates.

## Próxima ação

Publicar a candidata no branch draft, acompanhar os workflows no SHA produzido, corrigir falhas dos gates e só então atualizar este checkpoint com IDs/artefatos reais. Não mesclar PR sem autorização explícita.
