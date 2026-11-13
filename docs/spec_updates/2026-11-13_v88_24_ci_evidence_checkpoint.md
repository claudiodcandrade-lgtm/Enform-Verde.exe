# Histórico V88.24 — checkpoint de build anterior à candidata 3.26.24 (13/11/2026)

- No checkpoint anterior, PR #51 estava aberto em draft na branch patches-3.26.6. O HEAD consultado é 1072da53d5ccfbed939089c93883cb20f20852c1; o código declara APP_VERSION 3.26.23-PRECAMPO-EXPERIMENTAL.
- No mesmo SHA, os workflows de dashboard, contratos pré-campo e processamento semântico SAR em amostra de Sinop concluíram com sucesso. O job ESA BIOMASS FH também leu pixels reais em Sinop; essa evidência não confirma cobertura da fazenda Maria Eduarda integral nem uma estimativa de altura/estoque para toda a AOI.
- A suíte integral local executou 1.114 testes, com 1 skip da captura visual Tk por indisponibilidade de display Linux. A coleção validou 163 módulos; verificações dirigidas, sintaxe, YAML e diff-check passaram.
- A auditoria científica independente continua reprovada por evidência primária/validação independente insuficiente. Manter a versão experimental; não declarar calibração, homologação, IC defensável sem suporte nem liberação científica.
- Na consulta de 13/11, a build Windows do SHA 1072da5 ainda estava em execução nas verificações ópticas nacionais; não havia artefato Windows final confirmado. Não afirmar que o EXE está concluído ou disponível até o workflow terminar verde no SHA exato.
- O KML integral da Fazenda Maria Eduarda continua como gate: é preciso demonstrar do arquivo original até o dashboard pixels SAR válidos, classificação, resultados por módulo e trilha de auditoria. A leitura de FH em amostra de Sinop, assim como o smoke óptico em outras AOIs, não substitui essa execução integral.
- Correção incorporada neste ciclo: estado visual do mapa CBERS/Sentinel-2 isolado do status quantitativo; duplicação e truncamento do workflow Windows corrigidos, com regressões para impedir retorno. Confirmar a build antes de considerar encerrada a validação operacional.


Este registro é histórico. Para a candidata vigente, consultar o prompt e a especificação V88.29 / 3.26.24.
