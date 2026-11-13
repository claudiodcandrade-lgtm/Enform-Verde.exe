# V88.36 — recuperação SAR por recorte da AOI (13/11/2026)

## Falha observada no build Windows

O workflow Windows da candidata `3.26.25-PRECAMPO-EXPERIMENTAL` falhou no teste do EXE porque o Sentinel-1 COG integral excedeu o limite local de transferência de 1 GiB. Esse resultado é uma falha técnica de leitura, não ausência de cenas SAR.

## Correção implementada

A rota HTTPS mantém a leitura local do COG quando o tamanho cabe no limite. Para COGs maiores, indisponibilidade de assinatura/token, interrupção de transporte, erro HTTP ou resposta que não seja TIFF, o leitor tenta o serviço oficial de recorte por geometria do Microsoft Planetary Computer. A requisição envia o item, a polarização VV/VH e a geometria AOI autorizada, solicita uma grade limitada a 1,8 milhão de células e rejeita respostas maiores que 128 MiB, respostas que não sejam TIFF e grades fora do limite. TLS permanece verificado. URLs assinadas não são gravadas em disco ou no relatório de auditoria.

O recorte é uma rota de recuperação de pixels, não uma prova de disponibilidade para qualquer AOI. Erros do serviço de recorte continuam registrados como erro técnico; não autorizam contingência como se a busca tivesse confirmado ausência de SAR.

## Verificação local e gates restantes

- A suíte completa local passou: 1.134 testes, com 1 teste ignorado por ausência de display. `py_compile` dos módulos modificados passou.
- Testes novos simulam COG maior que 1 GiB, falha de assinatura e interrupção de transporte; todos confirmam tentativa do recorte limitado.
- O teste Windows do EXE que falhou no COG de 2 GiB precisa ser repetido no commit final. O teste simulado não comprova a resposta real do serviço nem a leitura no Windows.
- A classificação e as estimativas permanecem experimentais, sem homologação científica independente. A execução do KML integral no aplicativo até a apresentação no dashboard continua pendente.

