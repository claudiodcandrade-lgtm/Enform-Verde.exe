# Enform Verde v3.26.36-PRECAMPO-EXPERIMENTAL

- Código-fonte: commit `7e999022759fcbb540acbc7340dcc0036385c58e` na branch `patches-3.26.6` (PR #51 em rascunho).
- Build Windows: aprovado no workflow [43642362176](https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/43642362176).
- Self-test do executável compilado em pasta limpa: aprovado.
- Artefato: `Enform-Verde-Windows-v3.26.36-PRECAMPO-EXPERIMENTAL`, 197.799.966 bytes. SHA-256 do ZIP do artefato: `8882966d84019db61862bb3de196026b591114cfb6cb9871a05ef013e08ea1d4`. [Baixar artefato no GitHub Actions](https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/43642362176/artifacts/14132194271).
- Regressão do dashboard: 1.158 testes aprovados no commit de sincronização; contratos pré-campo e máscaras semânticas SAR também aprovados no workflow associado ao commit.
- Smokes live do workflow Windows passaram para fundo óptico CBERS-4A/Sentinel-2 no Brasil e Sinop, processamento de pixels/catálogo Sentinel-1 RTC do INPE nos seis biomas, classificação IBGE no Tapajós e cobertura BIOMASS FH em AOIs com inventários. As evidências são específicas aos locais e consultas testados; não comprovam cobertura universal de cada AOI ou operação contínua de serviços externos.
- A prova de pixels reais ESA BIOMASS FH foi aprovada separadamente.
- Gate científico de homologação continua reprovado por falta de observações independentes de campo. A versão permanece experimental e pré-campo; não declarar homologação.
- O workflow valida build e cenários de integração identificados. A execução independente no computador do usuário, análise completa da Fazenda Maria Eduarda até o dashboard e aferição de campo ainda não foram realizadas nesta sessão.
