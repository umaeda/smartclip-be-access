# Verificação de Logs na Nuvem do Azure

Este documento explica como verificar os logs da aplicação após o deploy no Azure Functions.

## Configuração do Application Insights

O sistema foi configurado para enviar logs detalhados para o Azure Application Insights, permitindo monitoramento em tempo real e análise de problemas.

### Pré-requisitos

1. Certifique-se de que as dependências necessárias estão instaladas:
   ```
   pip install -r requirements.txt
   ```

2. Configure a chave de instrumentação do Application Insights:
   - No portal do Azure, acesse seu recurso de Application Insights
   - Copie a chave de instrumentação (Instrumentation Key)
   - Configure como variável de ambiente `APPINSIGHTS_INSTRUMENTATIONKEY` na sua Function App

## Acessando os Logs no Azure

### Portal do Azure

1. Acesse o [Portal do Azure](https://portal.azure.com)
2. Navegue até sua Function App
3. No menu lateral, selecione "Application Insights"
4. Na página do Application Insights, você pode acessar:
   - **Live Metrics**: Para monitoramento em tempo real
   - **Logs**: Para consultas detalhadas usando Kusto Query Language (KQL)
   - **Failures**: Para visualizar erros e exceções
   - **Performance**: Para analisar o desempenho das requisições

### Consultas Úteis de Log

Aqui estão algumas consultas KQL úteis para depuração:

#### Visualizar todos os logs recentes

```kql
traces
| where timestamp > ago(1h)
| order by timestamp desc
```

#### Visualizar erros e exceções

```kql
exceptions
| where timestamp > ago(1h)
| order by timestamp desc
```

#### Analisar desempenho das requisições

```kql
requests
| where timestamp > ago(1h)
| order by timestamp desc
```

#### Filtrar logs por rota específica

```kql
traces
| where timestamp > ago(1h)
| where message has "[rota_desejada]"
| order by timestamp desc
```

## Estrutura dos Logs

Os logs foram aprimorados para incluir informações detalhadas:

1. **ID de Requisição**: Cada requisição recebe um ID único para rastreamento
2. **Tempo de Processamento**: O tempo que cada requisição levou para ser processada
3. **Detalhes da Requisição**: Headers, parâmetros e corpo da requisição
4. **Detalhes da Resposta**: Status code e headers da resposta
5. **Informações do Ambiente**: Variáveis de ambiente do Azure relevantes

## Solução de Problemas Comuns

### Logs não aparecem no Application Insights

1. Verifique se a chave de instrumentação está configurada corretamente
2. Confirme que as dependências do OpenCensus estão instaladas
3. Verifique se há erros de configuração nos logs da Function App

### Erros de conexão

1. Verifique as configurações de rede e firewall
2. Confirme que a Function App tem permissão para acessar o Application Insights

### Logs incompletos

1. Verifique o nível de log configurado (deve ser DEBUG para logs detalhados)
2. Confirme que o sampling do Application Insights não está filtrando logs importantes

## Melhores Práticas

1. Use IDs de correlação para rastrear requisições através de diferentes componentes
2. Adicione contexto suficiente aos logs para facilitar a depuração
3. Configure alertas para ser notificado sobre problemas críticos
4. Revise regularmente os logs para identificar padrões de erro