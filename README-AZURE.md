# Deploy da Aplicação SmartClip no Azure Functions

Este documento contém instruções detalhadas para realizar o deploy da aplicação SmartClip no Azure Functions.

## Pré-requisitos

- Conta ativa no [Azure](https://portal.azure.com)
- Azure CLI instalado ([instalar aqui](https://learn.microsoft.com/pt-br/cli/azure/install-azure-cli))
- Azure Functions Core Tools instalado ([instalar aqui](https://learn.microsoft.com/pt-br/azure/azure-functions/functions-run-local))
- Python 3.12 instalado (conforme configuração do projeto)

## Estrutura do Projeto para Azure Functions

O projeto SmartClip foi adaptado para funcionar com Azure Functions:

- `function_app.py`: Ponto de entrada para o Azure Functions, integra FastAPI com Azure Functions usando Mangum
- `function.json`: Configuração da função HTTP que processa todas as requisições
- `host.json`: Configurações do host do Azure Functions
- `requirements.txt`: Dependências do projeto, incluindo azure-functions e mangum
- `local.settings.json`: Configurações locais para desenvolvimento (não deve ser enviado para produção)

## Configuração Local para Desenvolvimento

1. Configure as variáveis de ambiente no arquivo `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "APPINSIGHTS_INSTRUMENTATIONKEY": "sua-chave-do-application-insights",
    "DATABASE_URL": "sua-connection-string-do-banco",
    "SECRET_KEY": "sua-chave-secreta",
    "AZURE_STORAGE_CONNECTION_STRING": "sua-connection-string-do-storage",
    ...
  }
}
```

2. Execute a aplicação localmente:

```bash
func start
```

## Deploy no Azure Functions

### Usando Azure CLI

1. Faça login no Azure:

```bash
az login
```

2. Crie os recursos necessários (se ainda não existirem):

```bash
# Criar grupo de recursos
az group create --name smartclip --location brazilsouth

# Criar plano de serviço
az functionapp plan create --resource-group smartclip --name smartclip-plan --sku B1 --is-linux

# Criar conta de armazenamento
az storage account create --name smartclipstorage --location brazilsouth --resource-group smartclip --sku Standard_LRS

# Criar Application Insights
az monitor app-insights component create --app smartclip-insights --location brazilsouth --resource-group smartclip
```

3. Crie a Function App:

```bash
az functionapp create --resource-group smartclip --plan smartclip-plan --name smartclip --storage-account smartclipstorage --runtime python --runtime-version 3.12 --functions-version 4 --app-insights smartclip-insights
```

4. Configure as variáveis de ambiente:

```bash
az functionapp config appsettings set --name smartclip --resource-group smartclip --settings "DATABASE_URL=sua-connection-string" "SECRET_KEY=sua-chave-secreta" "AZURE_STORAGE_CONNECTION_STRING=sua-connection-string-do-storage" "BACKEND_CORS_ORIGINS=https://seu-frontend.azurewebsites.net"
```

5. Publique a aplicação:

```bash
func azure functionapp publish smartclip
```

### Usando GitHub Actions

O projeto já inclui um workflow de GitHub Actions configurado no arquivo `.github/workflows/main_smartclip.yml`. Para utilizá-lo:

1. Configure os secrets necessários no seu repositório GitHub:
   - `AZUREAPPSERVICE_CLIENTID_31EBBC624F474C89A96B6E581F781A03`
   - `AZUREAPPSERVICE_TENANTID_EF7C8D2182104D628786BDD638F1C935`
   - `AZUREAPPSERVICE_SUBSCRIPTIONID_576E4F27674842098E7045F1B6B641C4`

2. Faça push para a branch main para acionar o workflow de deploy.

## Verificação de Logs

Após o deploy, você pode verificar os logs da aplicação:

```bash
az functionapp log tail --name smartclip --resource-group smartclip
```

Ou através do Portal do Azure, na seção de Application Insights, conforme detalhado no documento `docs/azure_logs.md`.

## Solução de Problemas Comuns

### Erro de Dependências

Se houver problemas com dependências durante o deploy:

1. Verifique se todas as dependências estão listadas no `requirements.txt`
2. Certifique-se de que as versões das dependências são compatíveis com o Azure Functions

### Erro de Conexão com o Banco de Dados

1. Verifique se a string de conexão está correta
2. Certifique-se de que o firewall do banco de dados permite conexões do Azure Functions

### Erro de CORS

1. Verifique se os domínios do frontend estão corretamente configurados na variável `BACKEND_CORS_ORIGINS`
2. Certifique-se de que a configuração de CORS no `host.json` está correta

## Melhores Práticas

1. Nunca armazene credenciais ou chaves secretas diretamente no código
2. Use o Application Insights para monitorar o desempenho e erros da aplicação
3. Configure alertas para ser notificado sobre problemas críticos
4. Revise regularmente os logs para identificar padrões de erro