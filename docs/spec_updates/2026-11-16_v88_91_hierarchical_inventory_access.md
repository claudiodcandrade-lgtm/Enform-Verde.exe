# V88.91 — acesso ativo e seleção hierarquizada de inventários (16/11/2026)

## Problema que esta alteração resolve

O catálogo anterior já listava 53 rotas, mas a coleta da interface baixava dados apenas do REDAPE e Sinaflor e abria o PNLA como rota manual. IFN/SFB, repositórios acadêmicos e bases de dados adicionais não percorriam um fluxo único de descoberta, registro e acesso.

## Acesso operacional às fontes

`inventory_source_access.py` consulta CKAN (SFB/IFN e IBAMA/Sinaflor), Dataverse (Embrapa REDAPE), OAI-PMH (Alice, Infoteca e repositórios configurados), REST público DSpace quando o endpoint existir e API do Zenodo. O fluxo coleta metadados e links, mantém a fonte/rota de cada resultado e escreve:

- `manifest_fontes_hierarquizadas.json` com execução/status por endpoint, leads, política de seleção e limites;
- `fontes_hierarquizadas.csv` para triagem e importação;
- `acesso_fontes_hierarquizadas.html` com links clicáveis agrupados por nível;
- `catalogo_inventarios_fontes_hierarquizadas.sqlite` com metadados descobertos persistidos como leads não elegíveis.

A aba **Base Científica → Ampliar Biblioteca — Fontes Hierarquizadas** executa a coleta em worker e abre o índice. Continua baixando recursos públicos já suportados no REDAPE e Sinaflor. PNLA, PAMGIA autenticado, ForestPlots e portais sem API confirmada permanecem rotas clicáveis de consulta manual. Falha, paginação limitada ou endpoint indisponível é registrada por fonte; não é declarada busca nacional concluída.

## Regra efetiva de seleção

1. Exigir correspondência estrita de bioma e fitofisionomia.
2. Se há AOI e candidato compatível na microrregião, restringir primeiro ao nível microrregional; só ampliar à região/bioma compatível se não houver candidato local. A distância é desempate entre candidatos no mesmo nível.
3. Dentro do escopo selecionado, dar prioridade a parcela aberta/primária de instituição reconhecida, georreferenciada e com licença; em seguida a estatística publicada totalizada por fonte idônea; por último, inventário de licenciamento/plano cujo próprio anexo tenha aceite expresso demonstrável por parecer/decisão.
4. Processo, licença, ASV, PMFS, camada de vistoria, registro de exploração, ocorrência taxonômica e metadado são somente localizadores quando não contêm unidade de inventário adequada. Aprovar o processo não significa aprovar o anexo.
5. Inventários fitossociológicos entram na mesma avaliação. Registros primários compatíveis podem apoiar área basal, DAP, distribuição diamétrica, abundância/frequência, estrutura vertical de campo e top 10 qualitativo por dominância. Para cada espécie, preservar nome vulgar informado e nome científico; lista é “espécies de ocorrência mais provável”, agregada por microrregião e fitofisionomia, não afirma presença na AOI.
6. Preservar fonte, URL/DOI, hash do arquivo, licença, período, região, desenho, unidade amostral, n, métrica, limiar de DAP e erro. Estatística ausente permanece ausente; reportar “incerteza não mensurável”, sem fabricar dispersão ou parcelas.
7. Todos os leads novos ficam `model_eligible=0`. Só dados inspecionados, licenciados e harmonizados podem ser promovidos; dados publicados agregados só podem ser usados na escala/métrica efetivamente publicada. Calibração SAR ainda exige pares parcela–pixel e validação espacial/temporal independente.

## O que foi e o que não foi concluído

Esta mudança adiciona rotas executáveis, ordenação geográfica/científica, arquivo local pesquisável e índice HTML. Não cria instantaneamente uma coleção nacional completa: conectores retornam apenas o que cada API permite; anexos e suplementos exigem verificação; endpoints OAI/DSpace podem estar indisponíveis; áreas de login e LAI requerem acesso legítimo. Os totais antigos — 27 referências agregadas e um arquivo Tapajós com 30 resumos de parcelas — continuam sendo o conteúdo harmonizado/curado conhecido até aqui; não devem ser apresentados como cobertura nacional. Nenhuma nova referência foi promovida a estimativa ou calibração nesta implementação.

## Verificação

Não executar testes automatizados nesta etapa. A primeira coleta real deve guardar o manifesto com o status individual dos endpoints, validar a recuperação de resultados de cada fonte ativa e auditar amostras de anexos antes de atualizar qualquer contagem de inventários elegíveis. Build Windows e CI ainda são necessários antes de distribuição executável.
