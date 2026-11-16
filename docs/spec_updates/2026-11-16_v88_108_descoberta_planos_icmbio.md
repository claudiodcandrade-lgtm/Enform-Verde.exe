# V88.108 — descoberta automatizada de planos de manejo de UCs
## Implementação
- A coleta hierárquica agora consulta, em modo somente leitura, a página oficial de planos de manejo do ICMBio e extrai links de páginas/documentos do domínio `www.gov.br/icmbio`. O coletor aplica limite de 500 leads, deduplicação por URL e identificadores estáveis por hash; saída sempre `catalog_lead`, `usable_for_estimation=false`.
- A coleta não baixa documentos nem presume que contenham inventário. A etapa posterior deve abrir cada plano/anexo, registrar UC, ato e versão, recuperar o inventário primário, confirmar fitofisionomia, método, unidades, período, licença e hash e deduplicar a campanha.
- O Portal de Dados Abertos é anunciado pela página oficial do ICMBio como rota dos planos, mas o endereço direto do conjunto consultado retornou 404. Atualizado o cadastro para preferir a página oficial do ICMBio e registrar a indisponibilidade do endereço direto; a rota permanece manual/descoberta, não fonte quantitativa.
## Verificação e estado
- Teste offline cobre extração de dois links ICMBio, rejeição de URL fora do domínio e bloqueio de uso quantitativo; passou. O teste geral de acesso a fontes também deve passar após esta mudança.
- Catálogo estático: 63 rotas/portais, 110 registros; referências agregadas permanecem 32 linhas e as 4 do Tapajós representam uma campanha. 3 conjuntos primários locais com microdados, um institucional harmonizado.
- Versão `3.26.57-PRECAMPO-EXPERIMENTAL`. Nenhuma medição de aceleração total foi feita; nenhum gate geral/Windows/EXE passou nesta mudança. Manter não homologada.
