# Catálogo inicial verificável — fenologia, vigor, clima e safras

Pesquisa bibliográfica direcionada em 24/10/2026. Fontes são **candidatas**, não modelos implementados, treinados ou validados no Enform Verde. Antes de implementar, ler método completo, verificar acesso a dados/coeficientes/licenças, unidade, escala, cultura, cultivar, local, ano, manejo e validação independente. Ausência de fonte específica não autoriza generalização.

| Instituição | Cultura | Publicação | Dados/uso potencial | Nível | Restrição | Fonte |
|---|---|---|---|---|---|---|
| Embrapa | soja | Agrometeorologia ZARC soja | balanco hidrico, fase critica, ciclo cultivar | referencia_metodologica | verificar parametros por cultivar/solo | https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1153140/1/Com-Tec-106.pdf |
| Embrapa | milho | ZarcPro-Milho | riscos climaticos, disponibilidade hidrica | referencia_metodologica | nao extrapolar perda para todo cultivo | https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1159479/1/Metodologia-para-o-Zoneamento-Agricola-de-Risco-Climatico-da-produtividade-do-milho.pdf |
| Embrapa | feijao;milho;soja | Precipitacao diaria e produtividade GO DF | series historicas | dados_candidatos | verificar acesso a microdados | https://www.alice.cnptia.embrapa.br/alice/handle/doc/1176750 |
| UFV | soja | Sensoriamento remoto deficit hidrico e fenologia | estagios, deficit hidrico, sensoriamento remoto | estudo_experimental | verificar transferibilidade | https://locus.ufv.br/items/cce53f98-6d9c-49f1-bdb7-cce6945d03b9 |
| UFLA/UFRA | soja | Relacao espectro-temporal indices e produtividade | NDVI EVI e ciclo | estudo_experimental | nao equiparar indice a produtividade | https://ajaes.ufra.edu.br/index.php/ajaes/pt_BR/article/view/2928 |
| UFLA | milho | Correcao atmosferica e previsao por ML | correcao atmosferica, predicao | estudo_experimental | verificar dados e validação externa | https://repositorio.ufla.br/items/0896b959-7d9f-4540-80a2-acf54a3af7ca |
| INPE | multicultura | Brazil Data Cube publicacoes | series temporais e fenologia | infraestrutura_cientifica | avaliar algoritmos e codigos | https://data.inpe.br/bdc/publicacoes/ |
| INPE | arroz | IA e SAR-optico arroz irrigado SC | Sentinel-1/2, variabilidade fenologica | estudo_experimental | dominio restrito arroz irrigado SC | https://mtc-m12e.sid.inpe.br/col/sid.inpe.br/mtc-m12e/2025/06.27.14.15/doc/publicacao.pdf |
| ESALQ USP | cana | Sensoriamento e random forest produtividade | Sentinel-2 e RF | estudo_experimental | verificar modelo e dados abertos | https://teses.usp.br/teses/disponiveis/11/11152/tde-02102023-163947/pt-br.html |
| ESALQ USP | cana | SAFY assimilacao dados remotos | SAFY, LAI, NDVI | estudo_experimental | verificar coeficientes e validação | https://teses.usp.br/teses/disponiveis/11/11152/tde-01062026-154411/es.html |
| ESALQ USP | cana | ML nutrientes e produtividade 2026 | XGBoost, espectroscopia | estudo_experimental | R2 0.83 RMSE 18.7 t/ha para amostra de estudo | https://teses.usp.br/teses/disponiveis/11/11152/tde-21092026-095219/pt-br.html |
| ESALQ USP | cana | Hiperespectral fitossanidade | espectroscopia e pragas | estudo_experimental | sem diagnostico automático sem validação | https://teses.usp.br/teses/disponiveis/11/11152/tde-04012024-160259/pt-br.html |

Pendências de busca específica: UFPE, UFU, UFG e outras unidades Embrapa; identificar equações completas e dados primários por cultura e fitofisionomia agrícola. Para toda previsão, exigir validação fora da amostra por região/safra, RMSE/MAE/viés, intervalo preditivo e atualização meteorológica real.
