# Enform Verde 3.26.2-PRECAMPO-EXPERIMENTAL

Esta versão candidata adiciona uma rota de visualização de satélite automática sem exigir token ou chave do usuário:

- Google Maps Static continua opcional quando há chave configurada.
- Google Maps Static só com chave oficial e faturamento; a API não oferece acesso oficial sem chave.\n- Sem chave: Sentinel-2 L2A via Planetary Computer (assinatura de dados automatizada, sem credencial do usuário) e rota direta Earth Search/AWS com COGs públicos; depois NASA GIBS / VIIRS True Color.
- Depois Esri e, se todos os serviços online falharem, mapa IBGE offline. A janela do entorno é óptica; radar fica reservado às análises.
- Sentinel-2 fornece a alternativa óptica pública de maior resolução; NASA VIIRS é contexto regional de resolução mais grossa, com provedor/data. Nenhuma imagem de visualização alimenta análises quantitativas.

Build e suíte de regressão para este SHA ainda devem concluir antes de distribuir pacote atualizado. Estado científico experimental pré-campo, sem alegação de homologação de campo.


- Para preview Sentinel-2, Earth Search/AWS é a primeira rota sem credenciais do usuário.
- COGs são lidos por janelas HTTP range e reamostrados ao viewport; bandas RGB são lidas com concorrência fixa de três workers.
- Sem quadrantes arbitrários para AOIs comuns; processamento multi-telha adaptativo só quando necessário. Sem alegações de ganho de velocidade sem benchmark.
