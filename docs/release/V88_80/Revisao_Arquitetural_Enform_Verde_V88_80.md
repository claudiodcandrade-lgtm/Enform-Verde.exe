# Revisão arquitetural — Enform Verde V88.80

Data: 15/11/2026  
Aplicação: `3.26.42-PRECAMPO-EXPERIMENTAL`  
Código validado: `98b0a6795e8af7e3b7f24ac075ed2886a47a8634`

## Resultado da rodada

Os workflows do commit final concluíram com sucesso:

- Build Windows: execução 43733571725.
- Dashboard: 1.173 testes aprovados; execução 43733571768.
- SAR live: execução 43733571694; caminho processamento → uso da terra → carbono → payload do dashboard passou para a amostra pública de Sinop e o KMZ do Tapajós.
- Sync da especificação Word: execução 43733567007.

O EXE foi compilado, testado em pasta limpa e passou UI smoke, verificação dos módulos, paridade Python/Windows dos contratos, leitura de rede e aceitação Tapajós. O ZIP foi baixado e a integridade foi verificada; o SHA-256 calculado localmente corresponde ao digest do artefato no GitHub.

## Causa do falso positivo no teste visual

O smoke anterior aprovava o fundo AOI local desenhado imediatamente ao abrir a tela, antes de o worker concluir a consulta CBERS/Sentinel-2/IBGE. Isso permitia registrar “não preto” sem provar que a imagem final fora entregue ao canvas.

O teste foi corrigido para aguardar o estado terminal do worker. Na nova rodada, o artefato `optical-gui-sinop-live-2899` registrou `PASS_CBERS`, fornecedor CBERS-4A/WFI L4-SR / INPE STAC, estado terminal observado, um item de imagem no canvas Tk e pixels RGB visíveis (673×562). Esta execução comprova que a rota de imagem chega à interface no recorte amostral de Sinop. O teste usa a vizinhança do centroide, não o KML privado da Fazenda Maria Eduarda.

## SAR e carbono: transmissão comprovada, conteúdo ainda experimental

O teste live comprovou entrega do payload SAR e dos subtotais de carbono ao dashboard nas duas AOIs de teste. Isso fecha uma falha de integração/transmissão que os testes anteriores não observavam.

A saída SAR é do último ano agrícola completo 2025/2026, não do mês atual. A classificação semântica atual permaneceu `N/D_SEM_MODELO_EXECUTAVEL_VALIDADO`; a rota alternativa registrou `ACESSO_RESTRITO`. O modelo anual é experimental e não foi validado no campo. A AOI de Sinop é uma amostra pública fixa; não é o KML da Fazenda Maria Eduarda.

O carbono é incompleto: o próprio payload marca `complete=false`; faltam componentes por estrato, incluindo serapilheira nas amostras reportadas, e as incertezas/covariâncias não permitem um IC total. As lacunas são preservadas como não estimadas, nunca convertidas em zero.

## Alcance visual e territorial

CBERS-4A/WFI carregou pixels nos 11 locais brasileiros amostrados no smoke do backend, com cobertura integral dos recortes amostrados. O canvas Windows também recebeu pixels reais CBERS no recorte de Sinop. Isso é evidência amostral, não garantia exaustiva para toda coordenada, data, geometria ou condição de nuvens do Brasil. O mapa IBGE permanece referência cartográfica potencial, não classificação atual.

## Pendências para fechar homologação

1. Testar o KML privado integral da Fazenda Maria Eduarda em Windows e conferir geometria, tempo de cada etapa, relatório e exportação.
2. Validar com dados de campo independentes as classes SAR atuais e safras/culturas.
3. Completar os compartimentos de carbono com inventários reconhecidos, priorizando fitofisionomia e microrregião/região, dados primários de parcelas abertas quando disponíveis, e serapilheira baseada em gravimetria/inventários. Declarar incerteza para cada estimativa; se não mensurável, usar literalmente “incerteza não mensurável”.
4. Só publicar total/IC quando cobertura, covariâncias e erro de classificação forem sustentados.

**Conclusão:** candidata operacionalmente testada; o worker de mapa entregou CBERS ao canvas no smoke corrigido e a rota SAR entregou dados ao payload do dashboard nas AOIs amostrais. Ainda não é homologada cientificamente e não foi validada no KML privado da Fazenda Maria Eduarda.