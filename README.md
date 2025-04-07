# 🚀 Deploy de Azure Functions em Python com Azure CLI

Este guia apresenta o passo a passo para publicar uma Azure Function escrita em Python, utilizando apenas o Azure CLI.

## ✅ Pré-requisitos

- Conta ativa no [Azure](https://portal.azure.com)
- Azure CLI instalado ([instalar aqui](https://learn.microsoft.com/pt-br/cli/azure/install-azure-cli))
- Azure Functions Core Tools instalado ([instalar aqui](https://learn.microsoft.com/pt-br/azure/azure-functions/functions-run-local))
- Python 3.12 instalado (conforme configuração do projeto)
- Estrutura da Azure Function pronta (com `host.json`, `requirements.txt`, `function.json`, etc.)

## 📦 Estrutura do Projeto SmartClip

O projeto SmartClip segue uma arquitetura baseada em FastAPI integrada com Azure Functions:

```
smartclip-be/
│
├── .github/workflows/         # Configurações de CI/CD para Azure
│   └── main_smartclip.yml     # Pipeline de deploy para Azure Functions
│
├── alembic/                   # Migrações de banco de dados
│   └── versions/              # Versões das migrações
│
├── app/                       # Código principal da aplicação
│   ├── api/                   # Endpoints da API
│   │   ├── deps.py           # Dependências da API
│   │   └── routes/           # Rotas da API
│   │
│   ├── core/                  # Configurações centrais
│   │   ├── config.py         # Configurações da aplicação
│   │   ├── security.py       # Segurança e autenticação
│   │   └── logger.py         # Configuração de logs
│   │
│   ├── db/                    # Configuração do banco de dados
│   │
│   ├── models/                # Modelos de dados (SQLAlchemy)
│   │
│   ├── schemas/               # Esquemas Pydantic
│   │
│   ├── services/              # Serviços de negócio
│   │
│   └── function.json          # Configuração da Azure Function
│
├── host.json                  # Configuração do host da Azure Function
├── function_app.py            # Ponto de entrada para Azure Functions
├── main.py                    # Ponto de entrada para execução local
├── requirements.txt           # Dependências do projeto
└── .env.example               # Exemplo de variáveis de ambiente
```

## 🛠️ Etapas de Deploy com Azure CLI

### 1. Login no Azure

```bash
az login
```

### 2. Criar recursos necessários (se ainda não existirem)

```bash
# Criar grupo de recursos (se necessário)
az group create --name seu-grupo-recursos --location brazilsouth

# Criar plano de serviço (se necessário)
az functionapp plan create --resource-group seu-grupo-recursos --name seu-plano-servico --sku B1 --is-linux

# Criar conta de armazenamento (se necessário)
az storage account create --name suacontaarmazenamento --location brazilsouth --resource-group seu-grupo-recursos --sku Standard_LRS
```

### 3. Publicar a aplicação

```bash
# Comando principal para publicação da aplicação
func azure functionapp publish smartclip
```

### 4. Configurar variáveis de ambiente

```bash
# Configurar variáveis de ambiente necessárias
az functionapp config appsettings set --name smartclip --resource-group seu-grupo-recursos --settings "DATABASE_URL=sua-connection-string" "SECRET_KEY=sua-chave-secreta"
```

### 5. Verificar o status da implantação

```bash
# Verificar logs da aplicação
az functionapp log tail --name smartclip --resource-group seu-grupo-recursos
```

## 📝 Notas importantes

- O projeto utiliza FastAPI integrado com Azure Functions através do adaptador ASGI
- As configurações de CI/CD estão disponíveis no arquivo `.github/workflows/main_smartclip.yml`
- Para execução local, use o comando `python main.py`
- Para testes locais das funções, use `func start`

## 🔧 Solução de Problemas

### Erros de dependências durante o deploy

Se você encontrar erros relacionados a dependências durante o deploy, verifique:

1. **Versões incompatíveis**: Certifique-se de que todas as versões no `requirements.txt` estão disponíveis no PyPI
2. **Dependências específicas**: Algumas versões de pacotes como `azure-functions-durable` podem não estar disponíveis. Use a versão mais recente compatível.
3. **Logs de erro**: Analise os logs de erro do deploy para identificar exatamente qual dependência está causando o problema

