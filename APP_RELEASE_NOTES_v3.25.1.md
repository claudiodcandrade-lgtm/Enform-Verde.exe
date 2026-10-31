# Enform Verde 3.25.1 — monitoramento agrícola com clima dinâmico

- Apresenta **“sem cultivos detectados”** quando a classificação cobre integralmente a propriedade e nenhuma classe de cultivo é identificada.
- Reconhece rótulos de classes específicas “Lavoura de …” como cultivo.
- Consulta automaticamente o clima dinâmico da propriedade após a análise, mesmo quando não há cultivo detectado; mantém botão para consulta/atualização manual.
- Exibe separadamente histórico em grade NASA POWER e previsão CPTEC/INPE, com fontes, períodos e avisos de disponibilidade.
- Não infere vigor, saúde fitossanitária ou rendimento apenas a partir do clima.
- Mantém intactas as rotas de carbono nativo; a build só poderá ser liberada após os gates de carbono e testes de empacotamento Windows passarem.

O pacote compilado deve conter `Enform Verde.exe`, runtime Python embarcado, dados de mapa offline e instruções. Este artefato fonte não é instalador Windows.
