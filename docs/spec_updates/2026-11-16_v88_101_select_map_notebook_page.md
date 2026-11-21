# V88.101 — seleção da página do mapa no smoke Tk (16/11/2026)

## Causa confirmada do timeout V88.100
- A saída CBERS-4A/WFI carregou no widget (provedor carregado, um item de imagem e três itens no canvas), mas canvas_viewable=false: o smoke abria a aplicação na primeira página do Notebook e nunca selecionava Mapas e limites (aba 1).
- A captura ocorreu sobre a tela por trás do widget oculto; somente 7,8% dos pixels eram visíveis. A falha era do setup do smoke e ocultação real do canvas, não indisponibilidade de cenas ópticas.

## Correção
- Selecionar a página Mapas e limites antes de iniciar o worker e confirmar winfo_viewable() para considerar visível qualquer imagem ou fallback. Um item de imagem em uma página oculta não conta como sucesso.
- Manter os critérios próprios para fallback cartográfico claro e para imagens ópticas. A tela/canvas ocultos ou pretos continuam bloqueados.

## Reexecução obrigatória
- V88.100: dashboard suite passou, SAR integrado Sinop/Tapajós passou, pixels ESA BIOMASS FH e cobertura óptica nacional passaram. O build falhou no canvas porque a aba de mapa estava oculta.
- Repetir CI Windows completa com a página de mapa selecionada. Nenhum EXE liberável até a imagem estar visível e o pacote final ser testado. Pré-campo, carbono parcial e sem homologação de campo.
