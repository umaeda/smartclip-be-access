# 🚀 Deploy de Azure Functions em Python com Azure CLI

Este guia apresenta o passo a passo para publicar uma Azure Function escrita em Python, utilizando apenas o Azure CLI.

## ✅ Pré-requisitos

- Conta ativa no [Azure](https://portal.azure.com)
- Azure CLI instalado ([instalar aqui](https://learn.microsoft.com/pt-br/cli/azure/install-azure-cli))
- Azure Functions Core Tools instalado ([instalar aqui](https://learn.microsoft.com/pt-br/azure/azure-functions/functions-run-local))
- Python 3.8, 3.9 ou 3.10 instalado
- Estrutura da Azure Function pronta (com `host.json`, `requirements.txt`, `function.json`, etc.)

## 📦 Estrutura Esperada do Projeto

minha-function/     
                │
                ├── host.json 
                ├── local.settings.json 
                ├── requirements.txt 
                └── MinhaFuncao/ 
                                ├── init.py 
                                └── function.json
## 🛠️ Etapas de Deploy com Azure CLI

### 1. Login no Azure

```bash
az login

