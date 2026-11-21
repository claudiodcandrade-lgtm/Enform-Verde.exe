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


## V88.70 — resultado final de CI e handoff (15/11/2026)
Código validado: SHA af64ae3b85188c5180192a92469fbe4313453025, candidata Enform Verde 3.26.39-PRECAMPO-EXPERIMENTAL.

- Suíte integral do dashboard: 1.164 testes aprovados, run 43672912037. Contrato pré-campo aprovado, run 43672912023.
- Handoff real Sentinel-1 → classificação de uso → máscaras de carbono → payload do dashboard aprovado em amostra de Sinop e AOI/KMZ público do Tapajós, run 43672912011. Sinop amostral: 1.084,73 ha; 30 cenas, 12 meses, 1.692 pixels. Tapajós: 1.290,69 ha; 29 cenas, 12 meses, 2.016 pixels. O mesmo analysis_run_id e hash da AOI foi preservado no payload.
- Build Windows e autoteste do executável em cópia limpa aprovados, run 43672912029. Artefato Enform-Verde-Windows-v3.26.39-PRECAMPO-EXPERIMENTAL, 197.812.692 bytes, SHA-256 0180af23e8ca4a4bf2b7a5ed2056eb7f5f7725d5687e98a8c823ba5dcde13c4c.
- Smokes do fundo óptico, cobertura amostral em biomas/extremos e envio ao canvas Windows em Sinop aprovados. Leitura Sentinel-1 RTC em sítios representativos dos seis biomas aprovada. Essas amostras não demonstram toda coordenada/data do Brasil.
- A causa confirmada foi o uso de catálogos diferentes: a classificação anual buscava MPC, enquanto a triagem Sentinel-1 recente também consultava INPE. A atualização usa MPC+INPE e propaga as máscaras e a identidade da análise até o painel.
- O KML integral privado da Fazenda Maria Eduarda (1.459,91 ha) NÃO foi usado: Sinop foi testada em uma AOI pública de 1.084,73 ha. Fazer o teste integral da fazenda em ambiente controlado e manter o arquivo fora de repositórios, logs e artefatos públicos.
- O carbono chegou ao painel, mas está incompleto (complete=false): em ambos os AOIs, necromassa e serapilheira ficaram não estimadas; erros de transferência alométrica, erro de mapa e covariâncias não foram quantificados; não há IC95% do total. Valores parciais não são estoque total. As classes SAR são experimentais e sem validação local independente; o gate científico continua reprovado e a versão não é homologada.

Status: candidata experimental operacionalmente validada para os cenários e AOIs de teste descritos; pendem execução do KML integral de Maria Eduarda, completar suporte de dados e incertezas de todos os compartimentos e validação de campo antes de homologação.
