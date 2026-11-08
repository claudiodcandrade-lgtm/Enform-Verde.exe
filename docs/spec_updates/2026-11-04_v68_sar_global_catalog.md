# REVISÃO V68 — PRIORIDADE SAR RECENTE, CATÁLOGO INTERNACIONAL E DIAGNÓSTICO AGRÍCOLA (04/11/2026)

## Alterações efetivamente incorporadas
1. `sar_crop_live_probe.py` realiza sondagem limitada e auditável dos pixels Sentinel-1 RTC VV/VH recentes em ponto interior de geometria agrícola cartográfica. Evidência exige data, cena e leituras reais de pixels; resultados N/D se inacessíveis. Um ponto não é classificador, não comprova cobertura integral nem o nome da cultura.
2. `crop_monitoring_forecast.py` mostra o resultado dessa sondagem junto à identificação histórica/experimental e preserva auditoria, evitando afirmar vigência da área plantada quando a fonte é MapBiomas 2025.
3. `crop_vigor_auto.py` recebe reforço para tentar TIFF local validado, ler assinaturas binárias TIFF corretas (incluindo UnicodeDecodeError), preservar N/D quando referência falha. Não confundir indicador SAR amostral com diagnóstico fitossanitário.
4. `desktop_app.py` alerta quando a classe urbana MapBiomas 24 é >=50% da AOI, sem corrigir a classificação pela nomenclatura do KMZ.
5. `international_crop_model_sources.py` inventaria recursos globais: ESA WorldCereal / VITO (Sentinel-1+2, openEO/CDSE), agroimpacts CropTypeMapper (arquiteturas CNN/LSTM), WorldCereal Reference Data, Radiant Earth MLHub e EuroCropsML (apenas óptico Sentinel-2). Hierarquia científica: classificador SAR recente calibrado e validado por região+cultura > observações SAR recentes sem inferência nominal > MapBiomas anual histórico.
6. `land_use_sar.py` passa a reportar explicitamente N/D por falta de modelo SAR executável validado, quando aplicável. Não se pode chamar mapa anual de cobertura atual. `tests/test_international_crop_model_sources.py` adiciona contratos de fonte/modalidade/licença, e de proibição de classificador fictício.

## Critérios científicos
- Existência de referência internacional não é prova de pesos treinados/licença comercial, compatibilidade de banda, disponibilidade temporal ou acurácia em Sinop. Nenhum classificador por cultura calibrado foi instalado nesta revisão; não anunciar que soja/milho são classificados por SAR na safra corrente.
- Modelo executável requer pipeline reproduzível, amostras independentes reais, classes explicitadas, validação espacial/temporal sem vazamento, precisão/recall/erros, incerteza por classe e domínio, correção geométrica e período de aquisição.
- Preferir dados brasileiros e tropicais para adaptação; aceitar fontes de qualquer país reconhecido com licenças e documentações válidas, quantificando mudança de domínio antes de homologação.
- A previsão PAM-FAO deve seguir CENÁRIO EXPERIMENTAL CONDICIONAL quando área de plantio atual não comprovada; incerteza do rendimento não cobre erro de área.
- Carbono nativo e solo 0–100 cm não devem regredir; resíduos/serrapilheira IFN em cm não viram toneladas sem calibração de massa seca.
- Nova versão Windows só deve ser liberada com suíte integral aprovada, autoteste do EXE em pasta limpa, SHA exato e artefato ZIP no mesmo commit. Homologação científica independente permanece separada e pendente até evidências independentes.

## Próximos gates mensuráveis
- Disponibilizar pipeline global com modelo real e licença verificável, aquisição Sentinel-1 real para várias datas e treinamento/recalibração brasileira por cultura.
- Validar em AOIs independentes brasileiras (inclusive Sinop) e apresentar matriz de confusão, amostra por classe, IC95% da precisão estimável e generalização espacial/temporal.
- Jamais registrar ganho de acurácia de modelo hipotético ou tratar pixels recentes como identificação de cultura.
