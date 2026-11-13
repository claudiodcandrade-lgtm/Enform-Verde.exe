# Enform Verde v3.26.28-PRECAMPO-EXPERIMENTAL

## Auditoria SAR completa no painel agrícola

- A auditoria preserva ID da execução, estado da etapa e proveniência SAR recebida do core, incluindo data, cena, pixels e provedor. O painel de carbono deriva horário UTC−03:00 do timestamp de aquisição confirmado.
- A regressão `tests/test_core_to_dashboard_handoff.py` percorre a fila assíncrona, o caminho principal e os dois apresentadores reais. Confirma resultados de carbono e data/cena no painel, candidatos SAR e sua auditoria sem promovê-los a área agrícola validada, além da propagação de falhas e status parcial.
- O teste live compara MPC e INPE em oito AOIs distribuídas nos seis biomas, incluindo Sinop e Tapajós. Exige par VV/VH real, no mínimo 100 pixels por polarização e aquisição de até 30 dias em pelo menos uma rota por AOI; registra os estados de ambas. A amostra geográfica verifica acesso em pontos representativos; não certifica cobertura exaustiva em cada coordenada ou época do Brasil.
- As rotas de catálogo agora repetem falhas transitórias até três vezes; o leitor MPC usa timeouts maiores para redes lentas. A tentativa live neste ambiente ainda não leu pixels: MPC deu `ReadTimeout` em Manaus e o INPE retornou erro HTTP; por isso a integração live e o build do SHA final seguem pendentes.
- Verificação local atualizada: 1.145 testes aprovados, 1 ignorado por ausência de display; 168 módulos coletados. Regressão adicional impede que VV isolado seja reportado como par SAR concluído; o assinador permite até três tentativas transitórias. Isso não substitui acesso SAR live no SHA final, ensaio Windows do KML da Fazenda Maria Eduarda, CI/build ou validação científica independente.

**Status:** versão candidata pré-campo experimental; não homologada.
