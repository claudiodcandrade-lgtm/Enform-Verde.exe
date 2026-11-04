# Prompt de continuidade — Enform Verde 3.26.0-SOLO-SAFRA
Atualizado: 2026-11-04

Repositório: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe
PR: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/pull/50
Branch: feature/agricultural-identification-native-carbon

## Instrucoes de prioridade
1. Aplicar patches fornecidos 0001–0017, dando preferencia aos caminhos e trechos dos patches quando divergirem da branch; nao sobrescrever deliberadamente correcoes posteriores validadas sem reavaliar seus testes.
2. Preservar MapBiomas Colecao 11 se o acesso for funcional; nos erros registrar fonte, versao, data e diagnostico; nao inventar classe.
3. Solo: somar exclusivamente 0–5, 5–15, 15–30, 30–60 e 60–100 cm da mesma fonte e mesmo ponto/pixel. Preferir intersecao exata de poligono com pixels originais e area equivalente; raster de mapa renderizado nao e dado fisico.
4. Carbono: estimar por fitofisionomia IBGE e area nativa atual, separar AGB/raizes/necromassa/serrapilheira/solo 0–100 cm; nao confundir cenarios, IC amostral e intervalos calibrados.
5. Safra: identificar area cultivada, cultura, vigor, indicios fitossanitarios remotos, clima dinamico e produtividade com intervalo mensuravel, nessa ordem. Modelos FAO 56/33/66 + PAM so sao experimentais sem holdout independente adequado.
6. Todos os resultados experimentais numericos devem exibir "ESTIMATIVA EXPERIMENTAL (nao homologada)", fonte, formula, parametros, dominio, incertezas conhecidas e faltantes, e rastro SHA-256.
7. Nunca declarar o gate de homologacao independente aprovado sem `validation/release_evidence.template.json` preenchido com fontes primarias e validacao espacial/temporal independente verificavel. N/D nao vira zero.
8. Publicar commit no HEAD exato, executar CI e build Windows a partir do mesmo SHA e conferir artefato real 3.26.0 antes de anunciar sua disponibilidade.

## Atualizacao efetiva nesta etapa
Commit a16be037abadb5d46af81111659aa56531f614f6: criado `experimental_audit.py`, testes e documentacao; `desktop_app.py` registra rastro de cada componente de carbono, e relatorios agricolas incluem trilha de previsao. A display experimental so aceita modelo com evidencia e intervalo declarado.

## Pendencias verificadas sem falsa aprovacao
- CI `scientific-release-gate` reprova por ausencia de manifesto de dados independentes, e cobertura dos 5 biomas / 6 compartimentos e registros SAR/culturas/vigor/safra.
- Patch 0003 aplicado no commit 521b0fd488bf18273ea29c22e45cd470cb641c66: amostragem adaptativa em estratos finos/fragmentados, testes regressivos e diagnostico de servicos misturados. Os outros patches ainda precisam integracao completa, testes e compilacao 3.26.0 (ultimo artefato confirmado antes desta etapa era 3.25.1).
- Cada publicacao subsequente deve manter este prompt e a especificacao cientifica atualizados, anexar SHA e distinguir status "validado", "experimental" e "N/D".
