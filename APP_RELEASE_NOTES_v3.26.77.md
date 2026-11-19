# Enform Verde v3.26.77-PRECAMPO-EXPERIMENTAL

## Correções desta candidata

- Evita buscas ópticas duplicadas durante redimensionamentos da janela sem reduzir a busca completa de cenas e fontes.
- Carrega e mede arquivos vetoriais grandes fora da interface gráfica.
- Reduz duplicação de memória ao iniciar análises, preservando todas as evidências de inventário e a camada IBGE em resolução original.
- Lê os arquivos de evidências de carbono e fitossociologia em segundo plano e mantém o conjunto anterior se um arquivo novo for inválido.
- Entrega vigor assim que o processamento SAR termina, independente da meteorologia, com resultados apresentados na thread da interface.
- Expõe um quadro de estoques por compartimento e incertezas, tC/tCO₂e, áreas quantificadas e estados N/D.
- Habilita cópia dos relatórios e auditorias.
- Coloca o painel executivo como primeira aba do Excel e mantém gráficos próprios; melhora dimensões e quebras de texto e evita densidades totais enganosas em cobertura parcial.

## Banco de inventários sob demanda

- O SQLite IFN (488.456.192 bytes) acompanha a pasta `data/` ao lado do EXE, fora do runtime interno do PyInstaller.
- O build confere manifesto, tamanho e SHA-256. A aplicação valida esquema/metadados sem varrer os 841 mil registros ou fazer contagens integrais a cada análise.
- A seleção combina filtros indexados de bioma/fitofisionomia com caixa espacial e distância geodésica exata; resumos usam agregação SQL apenas nas unidades selecionadas. A leitura de árvores individualizadas ocorre somente quando pedida.

## Performance e qualidade

As alterações visam responsividade e reduzem cópias e chamadas duplicadas. Não foi reduzida a resolução, a extensão da busca de cenas, a paginação dos catálogos nem a exigência estatística. Não há benchmark numérico comparável desta revisão; o tempo por etapa deve ser medido no teste Windows em AOI equivalente.

## Estado

Candidata pré-campo experimental. `py_compile` passou. 39 testes locais focados passaram e `py_compile` passou; a regressão completa e os testes integrados de imagem óptica, SAR/FH, vigor, exportação Excel e aceite em diretório limpo permanecem pendentes no SHA final. Não homologada cientificamente; validação de campo independente permanece necessária.
