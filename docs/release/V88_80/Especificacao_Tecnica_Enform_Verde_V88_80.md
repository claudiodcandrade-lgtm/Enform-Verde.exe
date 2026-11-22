# Especificação técnica — Enform Verde V88.80

## Identificação do build

- Versão: `3.26.42-PRECAMPO-EXPERIMENTAL`
- SHA do código testado: `98b0a6795e8af7e3b7f24ac075ed2886a47a8634`
- SHA-256 do EXE: `b5db289882b9143e51f0c06080f7a85979ddbaa01fb2245db8fe1d1dd434947c`
- SHA-256 do ZIP: `56bcd4e367cde2d0378cea01164f00a840f563750532cae21cc37553197c264c`
- Build Windows: workflow 43733571725 — sucesso.
- Dashboard: workflow 43733571768 — 1.173 testes aprovados.
- SAR live: workflow 43733571694 — sucesso nas AOIs amostrais.
- Evidência de imagem na interface: artefato `optical-gui-sinop-live-2899`, status `PASS_CBERS`.

## Mapa de fundo e entrega à interface

O worker deve buscar CBERS-4A/WFI e fontes ópticas de contingência conforme disponibilidade; quando a busca terminar, o estado terminal e a imagem final devem chegar à thread Tk. O fundo local provisório não conta como sucesso de imagem. O smoke só passa depois de observar o término do worker e verificar pixels visíveis no canvas.

Na execução final, o smoke de Sinop observou resposta terminal CBERS, criou um item de imagem no canvas (673×562) e mediu pixels RGB não pretos. O fundo foi apenas visual, não alimentou classificações ou cálculos. O teste usa amostra pública na vizinhança do centroide de Sinop, não o KML privado da fazenda.

O smoke de backend reportou leitura CBERS em 11/11 locais amostrados. A amostragem não prova disponibilidade contínua para todo o território brasileiro nem ausência de nuvens em qualquer data.

## SAR e transmissão de resultados

- Rota auditada: descoberta/leitura Sentinel-1 RTC VV/VH → classificação anual experimental → uso da terra → carbono nativo parcial → payload do dashboard.
- Resultado live: `BOTH_AOIS_END_TO_END_HANDOFF_PASSED`.
- Sinop: amostra pública fixa, 1.084,73 ha, execução `8E8914DCCBA6`.
- Tapajós: KMZ de teste, 1.290,69 ha, execução `4A70B18FD942`.
- A entrega ao dashboard passou; classe semântica atual continuou N/D. A classificação aplicada é anual, safra 2025/2026, experimental e não representa a cobertura atual.
- Tentativa de radar alternativo: `ACESSO_RESTRITO` quando a semântica atual não estava disponível.
- Os AOIs e máscaras do teste não substituem validação local de campo.

## Carbono, cobertura e incerteza

Apresentar apenas os compartimentos/estratos quantificados e sua cobertura; não extrapolar e não transformar falta de dado em zero. Neste teste o carbono foi explicitamente marcado incompleto. Alguns componentes, incluindo serapilheira, não tiveram fonte compatível nas interseções testadas; biomassa alométrica e mapas não trouxeram incerteza quantificada. Não existe IC total sustentado nessa saída.

Diretriz fixa para versões seguintes: priorizar inventários publicados por instituições reconhecidas na mesma fitofisionomia e microrregião/região; dentro deles, priorizar dados primários de parcelas abertas. O IFN é uma fonte válida, não exclusiva. Incluir serapilheira com estudos gravimétricos e inventários compatíveis. Declarar a incerteza de cada estimativa; quando não mensurável, escrever “incerteza não mensurável”. Não apresentar total completo ou IC sem suporte por compartimento e propagação de covariância/erros.

## Evidências da CI final

- 1.173 testes do dashboard passaram.
- Build Windows passou: testes de UI, módulos, paridade Python/EXE, rede/pixels reais e aceitação Tapajós em cópia limpa.
- ESA BIOMASS FH real no local de teste passou.
- Pixels ópticos CBERS chegaram ao canvas Tk no smoke de Sinop.
- Sentinel-1 percorreu a rota até o dashboard nas amostras de Sinop e Tapajós.
- O ZIP foi validado com teste de integridade; hash local confere com o digest do artefato.

## Estado e limitações

**Pré-campo/experimental; não homologado cientificamente.** O teste ponta a ponta não usou o KML privado da Fazenda Maria Eduarda. A classificação atual validada ainda está indisponível, o carbono não está completo e a amostra de cobertura óptica não é exaustiva nacional.