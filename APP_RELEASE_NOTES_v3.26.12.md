# Enform Verde 3.26.12 — piloto experimental de recuperação Windows (10/11/2026)

## Falhas reais reportadas — Sinop Fazenda Maria Eduarda
- A versão 3.26.11 carregou o KML de 1.459,91 ha, mas não apresentou fundo óptico; 12 cenas Sentinel-1 disponíveis, 24 leituras VV/VH tentadas, todas falhas por UnicodeDecodeError; sem máscaras semânticas SAR, relatórios nativos e agrícolas mostraram N/D.
- Esta versão não pode ser rotulada "homologada": precisa de validação real no KML da propriedade depois do build.

## Correções do código
- Leitura de COGs Sentinel-1: tentativa extra usando transportes HTTP/1.1 sem HEAD e sem requisições multipart, assinatura por ativo, diagnósticos de origem técnica.
- Imagens CBERS-4A/WFI e Sentinel-2: estratégia de range simples para contornar gateways incompatíveis no Windows.
- Interface do mapa: impedir loop de atualização por dimensões diferentes entre canvas e imagem; salvar causas por provedor (redigindo URLs assinadas) em ~/.enform_verde/ultimo_diagnostico_imagem_otica.json.
- Quadro IBGE: manter fitofisionomia potencial visível, explicitamente não verificada como cobertura atual.
- Regressões específicas em tests/test_sinop_windows_recurring_failures.py.
- Renovação do ESA MAAP continua implementada: token emitido 08/11/2026, aviso 22/01/2027, vencimento estimado 06/02/2027.

## Critérios para liberação
- EXE em pasta limpa, paridade Python/Windows, aquisição SAR e óptica reais, rastreabilidade de cenas e checksum da versão atual.
- SAR nativo e agricultura podem apresentar análises experimentais somente com pixels realmente lidos; classes históricas do IBGE/MapBiomas nunca substituem classificação atual e incertezas não são simuladas.
- Não declarar resolução definitiva antes de abrir fundo óptico e ler os pixels VV/VH no PC do proprietário usando o KML completo.
