# Prompt de continuidade — Enform Verde V88.80

Base: aplicação `3.26.42-PRECAMPO-EXPERIMENTAL`, commit `98b0a6795e8af7e3b7f24ac075ed2886a47a8634`. Os workflows de dashboard, SAR live, sincronização Word e build Windows deste SHA terminaram com sucesso. O ZIP foi conferido e substitui a versão anterior na Biblioteca.

## Fatos confirmados

- Dashboard: 1.173 testes passaram.
- Build Windows: compilou e passou em pasta limpa, incluindo UI smoke, paridade Python/EXE, leitura de rede/pixels e aceitação Tapajós.
- O smoke visual foi corrigido para aguardar a conclusão do worker. Resultado terminal do teste: `PASS_CBERS`; CBERS real foi desenhado como imagem RGB no canvas Tk (673×562, 1 item de imagem). Escopo: amostra pública próxima ao centroide de Sinop, não o KML privado Fazenda Maria Eduarda.
- O backend óptico carregou pixels CBERS em 11/11 AOIs de amostra; não tratar amostra como garantia para todas as datas e geometrias no Brasil.
- SAR live passou da leitura/processamento ao uso da terra, carbono parcial e payload do dashboard em amostra pública de Sinop e KMZ Tapajós.

## Limites que devem continuar explícitos

1. A classificação entregue é anual e experimental (safra 2025/2026); semântica SAR atual: N/D. Não apresentá-la como cobertura corrente.
2. O KML privado integral da Fazenda Maria Eduarda não foi testado. Não substituir por caixa/centroide público e declarar validação da fazenda.
3. Carbono: saída parcial/incompleta, compartimentos ausentes permanecem N/D. Serapilheira não foi estimada nas interseções live; não calcular IC total sem suporte. Informar “incerteza não mensurável” quando aplicável.
4. Homologação científica continua pendente de validação independente de campo, inclusive da área e classificação SAR.
5. Dados de disponibilidade óptica e SAR variam com fonte, autorização, cena, nuvem, data e geometria; não garantir operação universal sem teste correspondente.

## Próxima sequência obrigatória

- Executar o KML privado integral da Fazenda Maria Eduarda no Windows. Registrar hash da geometria, versão/commit, execução, número e datas das cenas, pixels lidos, tempo por etapa, tentativas de contingência e artefatos do relatório/exportação.
- Conferir visualmente que o canvas final apresenta imagem óptica ou fallback cartográfico IBGE; verificar o estado terminal do worker e pixels, nunca só um fundo provisório.
- Conferir os relatórios exportados e o dashboard para a mesma execução: mesmas áreas/status, subtotais, fontes, incertezas, avisos, tempos e N/D.
- Resolver a classificação semântica atual com dados/modelo publicados e evidência compatível; preservar distinção entre ausência de cenas, erro técnico e indisponibilidade/limite de domínio.
- Completar os compartimentos por inventários compatíveis e gravimetria de serapilheira; manter incerteza por parâmetro e declarar quando não mensurável.
- Medir gargalos antes de otimizar. Registrar duração total e por serviço, cena, processamento e renderização.
- Em qualquer alteração efetiva, sincronizar prompt, especificação técnica, especificação do solo/compartimentos, notas e Word no mesmo ciclo; executar todos os gates no SHA final.

Não declarar “resolvido definitivamente”, “homologado” ou “funciona em todo o Brasil” com base apenas nesta CI. A evidência desta rodada confirma que uma imagem chegou ao canvas em Sinop e que o payload SAR chegou ao dashboard nas AOIs amostrais.