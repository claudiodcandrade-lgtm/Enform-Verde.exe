# Enform Verde v3.26.64-PRECAMPO-EXPERIMENTAL

## Correções incluídas

- Mantém o modelo de previsão PAM + FAO-56/FAO-33 e condiciona a distribuição de rendimento por vigor SAR datado, quando disponível. A auditoria do relatório identifica probabilidades, classes residuais e se o vigor realmente entrou na distribuição; ausência de vigor fica explícita.
- Mantém os identificadores agrícolas existentes; não ativa candidatos de previsão novos.
- Seleciona referências IFN por localização, bioma e fitofisionomia IBGE e expõe frequência das dez espécies mais recorrentes entre unidades amostrais como indicador descritivo. Acrescenta comparação de AGB IFN quando houver UAs elegíveis no domínio publicado, separada do estoque ESA CCI.
- Retira o raster IBGE como fundo cartográfico substituto. Sem imagem óptica real, apresenta falha e diagnóstico. O gate de release requer pixels de CBERS, Sentinel‑2, NASA GIBS, Esri ou cache óptico visíveis no canvas real do Windows.
- Cacheia a validação integral do banco IFN durante a sessão, invalidando após mudança de tamanho ou `mtime_ns`; mantém os dados no pacote até existir distribuição externa sob demanda validada.
- Preserva modelos, fontes e critérios anteriores. A base expandida não é tratada como estimador de AGB/ha sem fatores de expansão e modelo validados; agregados institucionais são referências separadas e condicionadas à harmonização.

## Estado

Versão experimental. A publicação depende dos testes locais e do workflow Windows no SHA final. A geometria privada integral da Fazenda Maria Eduarda não está disponível neste checkout. Aprovação do build e do smoke óptico não equivale a homologação científica.
