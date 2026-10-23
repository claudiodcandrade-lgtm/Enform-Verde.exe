# Registro de modelos agrícolas internacionais — checkpoint v20

## Implementado na branch

- `crop_model_registry.py`: catálogo local de modelos para Milho, Soja, Sorgo, Café, Cana-de-açúcar, Arroz, Feijão e Citros; verificação fail-closed de pesos/hash, licença, modalidade SAR-only ou SAR+óptico, sensor, pré-processamento, período, domínio, esquema de atributos e evidência documental de validação independente.
- `tests/test_crop_model_registry.py`: seis testes unitários com **metadados sintéticos**, não validação agronômica. Testam ausência de pesos, amostragem, precisão, incompatibilidade de processamento, procedência e status de inferência não executada.
- Nenhum peso de artigo foi baixado ou incorporado; não há inferência realizada pelo novo módulo nem novos classificadores de culturas prontos. O resultado `eligible` avalia preenchimento de **contrato documental**, não autentica evidências nem prova acurácia brasileira; revisão independente e validação em campo seguem obrigatórias.
- A ausência de modelo não converte vegetação nativa, água ou ausência de dados em `Áreas cultivadas`. A classificação cartográfica/Random Forest anterior permanece inalterada.

## Operação

```python
from crop_model_registry import audit_registry
audit = audit_registry("models_agricolas.json")
print(audit["models"], audit["inference_status"])
```

O arquivo JSON deve conter `{"models":[...]}` e cada entrada deve especificar `crop, model_id, model_version, repository_url, license, sensor, processing, period, domain, feature_schema, modality, sar_features, weights, validation`; para `SAR+óptico` também `optical_features`. Pesos são arquivos locais referenciados relativamente ao manifesto, com SHA-256. A validação inclui URL, checksum, protocolo e domínio espacial/temporal, matriz de confusão, calibração, independência/representatividade declaradas, unidades aceitas, acertos e limiar calibrado. Sem esses elementos o registro é rejeitado.

## Falta para classificador real

1. Selecionar e obter modelos legitimamente executáveis por cultura, verificar licença/pesos e conectar adaptador de inferência às séries Sentinel-1 alinhadas com o contrato.
2. Adquirir observações independentes brasileiras por cultura e safra; testar transferência e calibrar separadamente; evitar a confusão entre classes, épocas, habitats e sensores.
3. Incorporar os resultados aceitos ao `run_land_use` e às exportações, sempre com fonte e validação; fallback preservado.
4. Confirmar CI, Windows EXE em cópia limpa e artifact de nova versão **antes** de declarar a versão operacional concluída.

Não confundir o catálogo com classificadores validados. Preservar PR #48 aberto, sem merge e todos os artifacts anteriores.
