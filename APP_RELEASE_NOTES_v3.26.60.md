# Enform Verde v3.26.60-PRECAMPO-EXPERIMENTAL

- Mantém a previsão contingencial PAM×clima sem vigor, liberada somente mediante certificado de busca completa MPC+INPE sem cenas Sentinel-1 VV/VH adequadas. Preserva a rota SAR prioritária e as equações preexistentes; sem vigor, usa envelope de quantis sem inventar classe. Saída experimental.
- Organiza a consulta sob demanda ao catálogo local de inventários, com consultas limitadas e modo somente leitura. O catálogo separa IFN, parcelas harmonizadas, agregados SINAFLOR, equações publicadas, referências e leads administrativos.
- Base local inclui arquivos estaduais IFN DAP≥10 (841.387 registros; 8.951 UAs) e conjunto ORNL/Tapajós; IFN segue `model_eligible=0` até validação de chaves, desenho, variáveis, representatividade e transferência. Mexiana e Jalapão preservam limitações documentadas.
- Consultas climáticas repetidas são reutilizadas por ponto/período dentro da execução. Não há benchmark comparável de tempo; nenhum ganho de desempenho é alegado.
- Fertilidade do solo não entra como covariável de produtividade. MapBiomas não determina uso ou vigor atual; permanece apenas na contingência histórica estritamente autorizada, após certificado de ausência SAR.
- Validação local anterior à build: suíte integral 1.247 testes OK, 1 skip; coleta de 183 módulos aprovada; uma leitura live VV/VH de Sentinel-1 retornou 9 pixels por polarização. O teste live é pontual e não valida vigor, safra ou cobertura nacional.
- Estado pré-campo experimental, não homologado. Build Windows/EXE e gates `--module-check`, `--visual-check`, `--network-check`, handoff integral carbono→dashboard, execução do KML completo da Fazenda Maria Eduarda e validação de campo aguardam confirmação no SHA desta versão.
