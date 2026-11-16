# V88.100 — diagnóstico de visibilidade do canvas Windows (16/11/2026)

## Resultado V88.99
- A regra de contraste ficou separada entre imagem óptica e fallback, mas o runner Windows ainda encerrou o smoke com timeout. Isso confirma que o limiar de contraste não era a única causa: o artefato anterior não registrava dimensões/visibilidade do Tk nem qualidade de pixels para diagnosticar a captura.

## Ação
- O teste agora traz a janela Tk ao primeiro plano, solicita estado visível e registra em caso de timeout: provedor/status do mapa, estado da janela/canvas, dimensões, cor de fundo, itens desenhados e métricas reais dos pixels capturados.
- Esses campos permitem distinguir falha do provedor, widget não mapeado, canvas sem desenho e captura oculta/escura. Não classificar o fundo como funcional até o smoke gerar pixels legíveis no runner.

## Liberação
- Dashboard, suite completa, contrato de safra, handoff SAR integrado Sinop/Tapajós, pixels ESA BIOMASS FH e fontes ópticas nacionais passaram na V88.99; o build parou no smoke Tk.
- Não há EXE liberável. Repetir CI completa no SHA seguinte e corrigir conforme o diagnóstico detalhado. Candidata continua pré-campo; carbono parcial e máscara agrícola anual experimental.
