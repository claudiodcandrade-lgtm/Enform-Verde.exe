# Enform Verde v3.26.85-PRECAMPO-EXPERIMENTAL

## Modelos de safra: evidência e limites

- O registro científico agora reúne, por cultura, rotas publicadas pela Embrapa, domínio observado, fontes e limitações (soja, milho, sorgo, feijão, arroz, cana, algodão, café e citros).
- Essa documentação não integra solvers novos nem amplia a área de validade do painel calibrado PAM/FAO. Somente soja e milho seguem no painel existente; vigor SAR só entra em produtividade quando a relação foi validada para a cultura, estágio e região.
- Rotas regionais específicas (por exemplo, SimulArroz no Sul, algodão no Cerrado e café arábica em domínios estudados) não são extrapoladas para o Brasil.

## Carbono: FH associado a inventários horizontais

- A rota numérica FH×AGB continua restrita às zonas e ao modelo estrutural local existente em Tapajós, com G (área basal) harmonizada em m²/ha e avaliação por blocos espaciais.
- Em outras regiões, as consultas espaciais IFN e referências horizontais publicadas são anexadas como evidência regional: fitofisionomia, UAs selecionadas, DAP/altura individuais agregados e referências de área basal/densidade publicadas.
- CCI, quando usado como segunda estimativa, recebe comparação regional de inventários no relatório; não é recalibrado numericamente sem pares AGB parcela–pixel CCI adequados. Essa limitação é explicitada na auditoria.
- Estatísticas brutas de árvores não são densidade por hectare. Sem expansão pelo desenho amostral e pareamento/calibração FH–AGB, o aplicativo agora registra `FH_DISPONIVEL_SEM_EQUACAO_REGIONAL_COMPATIVEL` e não usa essas métricas como preditores.
- A sequência de contingência mantém CCI como segunda rota independente e médias AGB de inventários pertinentes como última contingência; referências horizontais não são somadas ao estoque.

## Verificação e disponibilidade

Verificação local: 1.360 testes passaram e 1 foi ignorado; o coletor inspecionou 197 módulos sem falhas; compilação Python e diff passaram. Os testes sintéticos FH→dashboard e FH sem equação→rota CCI passaram. O teste visual Tk local não iniciou por falta de display. Ainda são necessários os gates Windows (`--module-check`, `--visual-check`, `--network-check`), build e autoteste do EXE em pasta limpa antes de disponibilizar pacote. Esta candidata continua experimental, sem homologação científica ou validação de campo.
