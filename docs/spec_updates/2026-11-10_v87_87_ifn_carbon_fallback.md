# V87.87 — Cenário condicional de carbono por inventário IFN sem pixels SAR (10/11/2026)

## Regra operacional
- Se houver pixels SAR quantitativos processados, não substituí-los por inventário. Se houver falha técnica de leitura, autenticação ou serviço, preservar `ERRO_TECNICO` e bloquear a transferência.
- Somente quando o pipeline confirma ausência operacional de observáveis SAR sem falha pendente, pode ser apresentado cenário secundário com dados de inventário abertos.
- A área base vem da interseção exata entre a AOI e a região fitoecológica potencial IBGE legenda_1. O cenário não converte essa classe potencial em cobertura nativa atual e não entra nos estoques SAR/nativos confirmados.

## Evidência disponível e limites
- Incluída uma extração rastreável com 37 unidades físicas IFN únicas para Amazônia/MT, classe de uso Floresta Natural e tipologia Floresta Estacional Sempre-verde, originada do Painel de Biomassa e Carbono do SFB. O recorte geográfico de até 250 km do centroide de Sinop seleciona 30 UAs; coordenadas do painel são aproximadas e não permitem pareamento pixel-parcela.
- AGB média regional: 138,29 Mg/ha; DP amostral entre UAs: 62,16 Mg/ha; faixa observada: 27,39–332,68 Mg/ha. Esses valores são descritivos, não são IC95% nem intervalo preditivo da propriedade. Equação `AGB_Chave` sem auditoria independente.
- A conversão de AGB para carbono usa a fração operacional 0,47, cuja incerteza não foi quantificada. O painel declara baixa confiança; não homologado; erro de transferência não quantificado.
- Quando a incerteza de transferência ou do fator não puder ser quantificada, o relatório usa literalmente “estimativa com incerteza não mensurada”; não mascara essa limitação com o DP amostral conhecido. Expõe trilha reproduzível: filtro e UAs selecionadas, soma/n da AGB, DP, AGB × 0,47, área potencial IBGE × densidade, e estoque tC × 44/12.
- Para Sinop, sobre os 1.459,91 ha de FESV potencial IBGE, isso representa apenas um cenário: 65,00 tC/ha e 94.888,01 tC (347.922,71 tCO2e) condicionais à área, não estimativa de estoque atual da fazenda. Não incluir no total confirmado.
- A rota está implementada apenas para essa combinação de bioma/fitofisionomia e proximidade regional. Outras áreas permanecem N/D até haver inventário compatível e incerteza documentada.

## Versão e validação
- Código/empacotamento: `d26a4f8` (`3.26.14-PRECAMPO-EXPERIMENTAL`). A receita Windows inclui o módulo e CSV IFN no PyInstaller. Testes específicos do gate de ausência SAR, bloqueio de falha técnica, restrição de domínio e trilha de cálculo passaram localmente.
- A regressão local foi executada, mas falhou por ambiente sem `requests`, `geopandas` e `shapely` (856 testes executados, 57 erros, 1 falha, 28 ignorados). `check_test_collection.py` também falhou pelos mesmos imports; o padrão visual não abriu por falta de `requests`. Build Windows, pixels reais na AOI completa Fazenda Maria Eduarda e homologação científica permanecem sem evidência no SHA. Não liberar EXE nem declarar operação nacional até CI e ensaio real passarem.
