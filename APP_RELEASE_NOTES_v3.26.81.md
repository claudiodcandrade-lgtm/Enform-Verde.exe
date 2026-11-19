# Enform Verde v3.26.81-PRECAMPO-EXPERIMENTAL

## Correção do encadeamento entre upload KML/vetorial e execução

O carregamento KML/KMZ/SHP/GeoJSON/GPKG ocorre em segundo plano. Se o usuário acionava EXECUTAR ANÁLISE antes de o worker entregar a geometria à interface, o aplicativo ainda via a AOI como ausente e mostrava a instrução para carregar CAR ou arquivo vetorial. Além disso, a conclusão do worker limpava novamente o estado da análise e podia descartar a solicitação de execução.

Nesta versão, o clique durante a validação vetorial fica enfileirado. Após confirmar a geometria, o fluxo segue para o diagnóstico territorial e inicia a análise automaticamente; se a leitura falhar, a solicitação pendente é cancelada e o motivo é mostrado. A conclusão do upload não limpa novamente o estado que já foi reiniciado antes do worker.

## Estado de validação

Esta candidata deve passar a regressão do caso upload assíncrono → clique antecipado → confirmação da geometria → início automático antes da disponibilização do pacote Windows. Build, teste do EXE limpo e checksum ainda pendentes neste checkpoint. Manter caráter pré-campo experimental; homologação científica independente exige validação de campo.
