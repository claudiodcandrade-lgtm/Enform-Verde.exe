# Padrão visual aprovado — Enform Verde

Vale para todas as versões. Linha de base congelada em `validation/ui_visual_baseline.json` (gerada em 03/11/2026, versão 3.26.0-SOLO-SAFRA, a partir do layout já aprovado nas versões anteriores).

## Protegido
- **Paleta do programa:** ORANGE #EF9B06 · FOREST #0B3D2E · GREEN #155D43 · PALE #F4F6F5 · TEXT #34413E.
- **Paleta do Excel:** laranja F29A00 · verde 0B3D2E · branco FFFFFF · claro F4F6F5 · linha D5DDD9.
- **Cabeçalho:** imagem aprovada `enform_header.png` (2400×360, SHA-256 c2189e35…aaaf61), fundo #063D26, altura 210 px, proporção preservada, **sem texto sobreposto**.
- **Barra de ações:** “Análise de carbono” (Title: Segoe UI 20 bold, laranja) e botões, nesta ordem de criação: Salvar relatório · Exportar Excel · APAGAR PESQUISA · EXECUTAR ANÁLISE (Run: Segoe UI 10 bold).
- **Navegação lateral:** largura 288 px, fundo #F6F8F8, borda #D8E0E0; 13 itens com ícones e rótulos atuais; selecionado #08733F/branco/negrito; não selecionado #F6F8F8/#233B49.
- **Abas:** Propriedade (CAR) · Mapas e limites · Carregar produtos SAR / AGB · Carbono — formações nativas · Base Científica e Modelos · Monitoramento — áreas cultivadas.
- **Rodapé:** “v<versão>” · status · “Sistema de Estimativa de Estoques de Carbono em Vegetação Nativa”.
- **Tipografia:** Segoe UI 10 (base), 12 bold (subtítulos H), 20 bold (título).
- **Mapa:** contorno da AOI #FF8A00 / #E87500 com preenchimento #F8B44C.
- **Ícone:** fundo (22,92,58), monograma “EV”.

## Livre para evoluir
O conteúdo **dentro** de cada aba (novos painéis, tabelas, gráficos) pode crescer, desde que use a mesma paleta e tipografia.

## Como é garantido
- `tests/test_visual_standard.py` (CI): compara paleta, Excel, ícone, imagem do cabeçalho e o “casco” da janela construída com a linha de base.
- `Enform Verde.exe --visual-check` (build Windows, cópia limpa): repete a comparação no executável compilado, com a linha de base empacotada.
- Mudança visual deliberada: `python ui_visual_standard.py --update` + entrada na especificação técnica explicando a decisão. Sem isso o build falha.
