# REVISÃO V67 — CLAREZA DA COBERTURA NÃO CONFIRMADA E REGRESSÃO APROVADA

## Resultado técnico
- O último ciclo de testes encontrou uma falha exclusivamente textual no test_carbon_presentation_regression.test_unknown_cover_never_claims_zero_natural_cover: relatório deveria preservar literalmente "não equivale a zero de vegetação nativa".
- Commit 360b8eb68a6a7213b14aa600dfc2aace2436cb7d corrige executivo de carbono: "Cobertura não confirmada: X ha — não equivale a zero de vegetação nativa; pode conter vegetação não mapeada".
- A outra exigência foi preservada: "Cobertura nativa: N/D — cobertura não integralmente verificada" quando existe qualquer área sem classe. Área nativa cartografada nunca se confunde com porcentagem definitivamente confirmada da AOI.
- Run de regressão 41906378666 concluiu com sucesso no mesmo commit 360b8eb6, enquanto outro run paralelo 41906388137 reprovou apenas o controle que exige atualização simultânea de prompt e Word canônico, resolvido por este adendo documental e workflow.
## Compromissos de versão
- O painel executivo de Sinop preserva a área 1.500,33 ha, das quais 72,92 ha nativas e 1.241,75 ha de soja em mapa anual 2025. Mantém o estado cartográfico FALLBACK_CARTOGRAFICO, sem afirmar classificação SAR ou plantio atual.
- O módulo de serrapilheira possui referencia FESV norte MT, inventários publicados de classes específicas e controles IFN/SFB; cenários transferidos e sensibilidade de fração de carbono sem erro de domínio quantificado ficam fora do estoque conhecido.
- O modelo de safra PAM/FAO com vigor SAR respeita observações orbitais reais, máscaras específicas e propagação da incerteza; não contaminar projeção com SAR N/D.
- Liberar novo ZIP Windows somente após build + autoteste do EXE em pasta limpa + verificação SHA coincidente + publicação do artefato do commit documental. Gate científico independente permanece pendente em evidências observacionais ainda indisponíveis.
