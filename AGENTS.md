# Regras para agentes de código (Codex/ChatGPT, Claude e outros)

Leia antes de qualquer alteração: `docs/ROTEIRO_CORRECOES_ENFORM_VERDE_2026-11-08.md`, o prompt canônico `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md` (fim do arquivo) e `docs/PADRAO_VISUAL_ENFORM_VERDE.md`.

1. **Um agente por branch.** Não envie commits se outro agente estiver trabalhando na mesma branch.
2. **Código e testes no mesmo commit.** Mudou comportamento → atualize os testes. Antes de cada push rode e passe: `python -m unittest discover -s tests` e `python tools/check_test_collection.py`.
3. **Documentação a cada passo efetivo:** entrada em `docs/spec_updates/` aplicada com `python tools/update_spec_docx.py`, checkpoint no prompt v52, no v43 e na especificação de solo (o CI cobra).
4. **Nunca** usar MapBiomas para classe atual, cultura, vigor, carbono, máscara, rótulo de treino ou validação (apenas referência histórica isolada). Exceção estreita aprovada pelo proprietário em 08/11/2026: rótulos cartográficos oficiais PRODES/TerraClass podem alimentar somente experimento de treinamento, com saída explicitamente `map_agreement`, nunca validação de campo; fora do domínio/período da referência, abster-se.
5. **Nunca** inventar dados, coeficientes, métricas ou validação; ausência → N/D com motivo. N/D nunca vira 0 ha.
6. **Não alterar limiares científicos** sem decisão do proprietário registrada no prompt.
7. **Não desligar a verificação TLS**; usar `tls_setup`.
8. **Padrão visual congelado:** `python ui_visual_standard.py` deve imprimir PADRAO_VISUAL_OK.
9. **Nova versão:** incrementar `APP_VERSION`, criar `APP_RELEASE_NOTES_vX.Y.Z.md`; EXE só é citado após build Windows verde com `--module-check`, `--visual-check` e `--network-check`.
10. Não fazer merge em `main` sem pedido explícito do proprietário.

## Decisões do proprietário (08/11/2026) — não alterar sem nova decisão
1A modelo de safra calibrado (painel); 2B qualquer acurácia medida aceita como experimental com n e IC95% obrigatórios; 3C PAM 2015–2024; 4B altura SAR de modelo publicado como experimental com erro propagado; 5B previsão sem vigor rotulada; 6A serapilheira hierárquica para todas as florestais com ≥1 estudo; 7B incerteza total com correlação declarada (biomassa ρ=1; serapilheira e solo independentes); 8A unidades radar sem nome só no mapa/painel — e sempre buscar um classificador SAR.

## Decisões do proprietário (08/11/2026)
9. PRODES/TerraClass autorizados como rótulos cartográficos para treino experimental e avaliação em blocos espaciais. Informar concordância com mapa, nunca acurácia de campo. TerraClass mapeia Amazônia e Cerrado (cerca de 73% do Brasil); não extrapolar aos demais biomas. Suas classes agregadas não distinguem soja de milho. PRODES registra supressão primária e não identifica uso atual após a supressão.
10. Prioridade operacional: primeiro modelos/dados testados e homologados para o domínio; modelos experimentais são contingência explicitamente rotulada, com incerteza e avaliação disponíveis. Se nenhum for aplicável, retornar N/D com o motivo, sem esconder a lacuna nem promover o experimento a validado.
