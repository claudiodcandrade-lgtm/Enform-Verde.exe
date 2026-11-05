# Enform Verde 3.26.2-PRECAMPO-EXPERIMENTAL

Esta versão candidata adiciona uma rota de visualização de satélite automática sem exigir token ou chave do usuário:

- Google Maps Static continua opcional quando há chave configurada.
- Sem chave ou se Google falhar: Sentinel-2 L2A público; depois NASA GIBS / VIIRS True Color, sem autenticação do usuário.
- Se serviços online falharem, Esri e por fim mapa IBGE offline.
- A cena NASA VIIRS é visualização regional de resolução mais grossa, identificada com provedor e data; não é usada em análises quantitativas.

Build e suíte de regressão para este SHA ainda devem concluir antes de distribuir pacote atualizado. Estado científico experimental pré-campo, sem alegação de homologação de campo.
