# Checkpoint V88.55 — óptico e regressão Windows

Data: 14/11/2026

- Candidata: `3.26.35-PRECAMPO-EXPERIMENTAL`.
- Código: branch `patches-3.26.6`, SHA `417e93141ec035d5bb414abb620224d490580927`.
- CBERS-4A/WFI segue como fonte óptica prioritária; Sentinel-2 L2A é fallback. Retirada a apresentação de raster cartográfico offline como imagem orbital.
- CI de imagem: CBERS real em 11/11 janelas representativas; canvas Tk com CBERS real em janela de Sinop; Sentinel-2 real no Tapajós passou. O KML integral Maria Eduarda não foi avaliado.
- Dashboard: 1.156 testes terminaram OK; o job falhou somente no guard de documentação, motivo que esta atualização corrige.
- Build Windows #43633560279 concluído com sucesso; EXE 3.26.35 passou autoteste em pasta limpa. Artefato Actions 14129607134 (197.843.132 bytes), ZIP SHA-256 `3ff077bc0a002190028732a27c76de6a9332f1fd773df2d1d249fc22eda814`, EXE SHA-256 `ac9b68b0139f4a1694e5545d98bc3eb8902c17cee4aa771caf0b040330ad6f44`.
- Gate científico independente reprovado por falta de observações independentes. Não homologado.
- Pendência principal: execução integral KML Maria Eduarda → processamento → dashboard e validação de resultados em campo.
