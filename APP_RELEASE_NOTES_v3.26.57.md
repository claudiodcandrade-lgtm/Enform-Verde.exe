# Enform Verde v3.26.57-PRECAMPO-EXPERIMENTAL

- Acrescenta descoberta automatizada, somente de leitura, de links na página oficial de planos de manejo do ICMBio e em páginas oficiais de UCs vinculadas.
- Os links descobertos entram como leads não quantitativos; o programa não presume que cada plano inclua inventário nem extrai valores como microdados sem validação do documento.
- O endpoint do conjunto de dados do Portal de Dados Abertos citado pela página do ICMBio retornou HTTP 404; a página oficial do ICMBio passa a ser a rota primária, e a indisponibilidade do endpoint é registrada.
- O teste offline confirma filtro de domínio oficial e mantém todos os registros descobertos fora do uso quantitativo.
- Validação local atualizada em 16/11/2026: suíte completa 1.239 testes OK (1 skip headless); checker inspecionou 183 módulos sem falha; contratos de handoff core→dashboard 4/4 e pipeline 6/6; gate visual executado em desktop gráfico com `PADRAO_VISUAL_OK`.
- Aceitação SAR live do AOI público Tapajós: `SAR_PROCESSADO`, 259.688 pixels, 1.290,69 ha, origem `SAR_DERIVED_CCI`; resumo em `validation/acceptance_tapajos_live_v88_109.json`. É uma prova de processamento nessa amostra, não de todos os compartimentos nem de entrega integral ao dashboard.
- CI/build do EXE Windows e execução do KML integral privado da Fazenda Maria Eduarda continuam pendentes; versão permanece experimental, sem homologação científica ou validação independente de campo.
