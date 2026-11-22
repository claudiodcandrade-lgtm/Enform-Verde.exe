# Biblioteca científica — classificação agrícola SAR (24/10/2026)

Objetivo: selecionar algoritmos internacionais comprovados como CANDIDATOS para validação no Brasil; desempenho publicado em outro país não autoriza afirmar validação local. Não modificar estimativas de carbono ou substituir modelo operacional sem testes de regressão.

| Rota | Evidência | Aplicação inicial | Limitação |
|---|---|---|---|
| Índices fenológicos Sentinel-1 + Random Forest | Woźniak et al. 2022, DOI 10.1016/j.jag.2022.102683; 16 culturas na Polônia; acurácia regional 85,95–89,81%, F1 por cultura 0,73–0,99 | Baseline explicável para VV/VH e descritores temporais | Descritores polarimétricos avançados exigem produtos/observáveis compatíveis, não apenas GRD |
| TCN com atenção | Tsuchiya & Sonobe 2025, DOI 10.3390/rs17122095; 16 cenas S1, seis classes, acurácia global 85,7% | Modelo temporal candidato e ablação frente a RF | Testado no Japão, não inclui todas as culturas-alvo brasileiras |
| STMA atenção espaço-temporal | ISPRS JPRS 2023, DOI 10.1016/j.isprsjprs.2023.11.016; resultados publicados 96,54% Brandenburg, 86,77% PASTIS-R, 83,37% África do Sul | Candidato para séries SAR e parcelas | Resultados não transferíveis sem validação; verificar licença, pesos e dependências |
| Classificação hierárquica SAR | Zhou et al. 2024, DOI 10.1016/j.jenvman.2024.122251; ganhos de OA e F1 no estudo | Primeiro agrícola/não agrícola, depois grupos e cultura | Treinamento e validação locais necessários |
| Fusão S1+S2 com atenção temporal | Weilandt et al. 2023, DOI 10.3390/rs15030799 | Diagnóstico multimodal onde houver dados ópticos | Nuvens e defasagem temporal; requer avaliação incremental |
| BreizhCrops | Rußwurm et al. 2020, DOI 10.5194/isprs-archives-XLIII-B2-2020-1545-2020 | Benchmark de arquiteturas temporais | Benchmark SENTINEL-2, não SAR; não declarar modelo SAR validado |

## Protocolo de incorporação
1. Confirmar publicação, DOI, licença de código e pesos; registrar sensores, bandas, resolução, região, classes, safra e domínio.
2. Reproduzir métricas publicadas quando dados/código permitirem; nunca criar pesos fictícios.
3. Construir dataset brasileiro de referência com parcelas/talhões e safras independentes, inclusive soja, milho, sorgo, café, cana, arroz, feijão, citros, pastagem, vegetação nativa e classe incerta. Registrar fonte e licença.
4. Comparar RF + índices fenológicos, TCN, STMA/hierárquico e S1+S2 nas MESMAS partições por talhão, região e ano; evitar vazamento entre pixels do mesmo talhão.
5. Reportar F1, precisão, revocação, matriz de confusão, calibração, cobertura e abstenção por classe, por bioma e safra; só habilitar classe com evidência suficiente.
6. Escolher modelo pelo desempenho validado no domínio, não pela maior acurácia publicada no exterior; medir latência e custo computacional Windows.
7. Diagnóstico atual deve registrar data de aquisição efetiva, atraso, qualidade e versão do modelo; se imagens ou validação insuficientes, rotular não determinado.
8. Manter AGB via SAR e máscara nativa como rotas independentes, sem regressões.

## Estado
Registro bibliográfico e critérios científicos apenas. Nenhum algoritmo foi treinado, reproduzido, integrado ou validado por este documento.
