# V88.68 — handoff SAR até uso do solo, carbono e dashboard

Candidata 3.26.39-PRECAMPO-EXPERIMENTAL, commit-base 3172277b02dd59de24861c8dd8abfc8e5159d49a. A rota principal corrigida busca séries anuais Sentinel-1 RTC VV/VH em MPC+INPE. A prova live anterior processou 30 cenas, 12 meses e 1.692 pixels em caixa amostral próxima a Sinop, não no KML integral da Fazenda Maria Eduarda. O teste agora foi ampliado para executar a cadeia real nas duas AOIs públicas de aceitação: recorte amostral de Sinop e KML/KMZ do Tapajós.

Mudanças desta etapa:
- O payload SAR do dashboard agora transporta classes semânticas atuais, áreas, origem/taxonomia, modelo, safra, situação de validação local, analysis_run_id e hash da AOI.
- O runner live chama run_land_use sobre cada AOI, verifica fechamento de área, confirma máscaras SAR experimentais no vetor, entrega as classes nativas ao native_carbon_analysis, e confirma que os nomes dos estratos e as classes semânticas chegam ao payload do dashboard com o mesmo run_id/hash.
- O carbono usa o estimador de produção. Cada compartimento deve entregar valor sustentado ou N/D/ERRO_TECNICO com motivo/incerteza; nenhum valor de teste é inserido.
- A fixture de Tapajós é pública e já existe no repositório. O KML da Fazenda Maria Eduarda continua privado e não entra no CI nem em artefato público.
- O guard documental deixa de exigir alteração do prompt histórico V43, preservado como arquivo imutável; exige atualização do prompt corrente, especificação de solos e checkpoint corrente.

Aceite:
1. Dashboard, regressões completas e build Windows passam no mesmo SHA.
2. O workflow live de duas AOIs passa com classes SAR reais chegando a uso do solo, máscaras de carbono e payload do dashboard; run_id/hash e área fecham.
3. Se o estimador não encontrar dados de um compartimento, exibir N/D e motivo; falha técnica permanece ERRO_TECNICO; não transformar ausência em zero.
4. Para Tapajós e Sinop amostral, classificador continua experimental e sem validação de campo.
5. Aceite final da Fazenda Maria Eduarda exige executar localmente o KML integral privado, comparando área 1.459,91 ha, hash, cenas/pixels/classes, carbono por compartimento e painéis/relatório. A caixa de 1.084,73 ha não substitui essa AOI.
6. Smokes ópticos de cobertura nacional continuam amostrais. Em falta de cena/erro, preservar a última imagem óptica válida e exibir diagnóstico explícito; não substituir silenciosamente por raster IBGE ou tela preta.

Estado antes da CI deste commit: alterações preparadas; aceitação live ampliada e testes Windows/dashboard ainda pendentes. Manter estado experimental pré-campo e não homologado até os resultados serem verificados.




## Registro corretivo da integração e dos gates (15/11/2026)
A suíte integral no commit d95542c executou 1.164 testes e encontrou duas falhas de contrato, não falhas de processamento: o teste documental ainda exigia editar o arquivo histórico V43, embora o guard de produção considere V43 imutável; e o workflow de SAR não repetia a declaração explícita `scikit-learn==1.8.0` exigida pelo teste de pinagem, apesar de a dependência já constar em requirements_desktop.txt. Ambas as exigências foram corrigidas no commit 70e7460aa5d7e9a0e479f0a7e155c72443b5c24f. A suíte, o build e o fluxo live para Sinop e Tapajós precisam ser aprovados no SHA final. Não declarar versão funcional até isso ocorrer.