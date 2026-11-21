# V88.95 — aplica o bloqueio de cultura fora do domínio SAR (16/11/2026)

## Evidência ponta a ponta

A execução live `43792734694` passou com estado `BOTH_AOIS_END_TO_END_HANDOFF_PASSED`: Sentinel-1 RTC VV/VH foi lido, classificado experimentalmente, convertido em mapa anual/relatório de uso, processado nos relatórios de carbono e entregue ao payload do dashboard para uma amostra pública de Sinop e para o KML de teste do Tapajós. Esse resultado demonstra a passagem técnica do dado entre etapas, não validação de campo. A amostra de Sinop não é a Fazenda Maria Eduarda; o KML privado integral não estava no repositório nem na Biblioteca.

A mesma execução encontrou regressão semântica: no Tapajós (fora do envelope espacial de treinamento), o auditor dizia `SPECIFIC_CROP_SUPPRESSED_OUTSIDE_TRAINING_ENVELOPE`, mas as listas de classes e polígonos ainda carregavam 0,64 ha de soja e 2,56 ha de café. A regra existia como helper, mas não era aplicada às previsões por pixel.

## Correção e gate

`classify_aoi` agora aplica o bloqueio aos rótulos de cada pixel antes de formar tanto as classes quanto os polígonos; fora do envelope, mantém a área cultivada experimental e elimina os nomes específicos. O teste integrado `test_classifier_applies_crop_name_guard_to_classes_and_polygons` reproduz um AOI do Tapajós com classificadores simulados e exige apenas a classe genérica em ambas as saídas. Esse teste foi acrescentado ao gate Windows que instala GeoPandas. O ambiente local não dispõe de GeoPandas; ali passaram os demais testes de política (5) e o novo teste foi skipado por dependência ausente. Reexecução Windows no SHA desta revisão é obrigatória.

## Limites operacionais

A rodada Windows V88.94 não é distribuível: falhou porque o teste PAM fixava 133.920 linhas embora a materialização live válida retornasse 150.660. A correção dessa cardinalidade está em V88.94, e esta nova mudança semântica exige nova CI/build. A integração SAR observada está restrita aos dois AOIs de teste e safra anual 2025/2026; não provou classificação atual, acurácia na propriedade, estimativa de safra validada, nem execução do KML privado Maria Eduarda. Carbono chegou ao dashboard como estoque parcial; faltaram compartimentos/estimativas e incertezas mensuráveis, então não declarar total completo nem IC95%. O gate científico continua bloqueado sem dados independentes de campo.
