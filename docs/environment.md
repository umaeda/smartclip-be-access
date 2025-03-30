# Configuração de Variáveis de Ambiente

## Introdução

Este documento descreve como configurar as variáveis de ambiente necessárias para executar o projeto SmartClip Backend. As variáveis de ambiente são usadas para armazenar configurações sensíveis, como chaves secretas e credenciais de banco de dados, de forma segura sem expô-las no código-fonte.

## Configuração para Desenvolvimento Local

1. Crie um arquivo `.env` na raiz do projeto baseado no arquivo `.env.example`
2. Preencha todas as variáveis necessárias com valores apropriados

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo com seus valores
nano .env  # ou use seu editor preferido
```

## Variáveis de Ambiente Necessárias

### Configuração Básica da API
- `API_STR`: Prefixo para todas as rotas da API (padrão: "/api")
- `PROJECT_NAME`: Nome do projeto (padrão: "FastAPI Backend")

### Segurança
- `SECRET_KEY`: Chave secreta para assinatura de tokens JWT e proteção CSRF
  - **IMPORTANTE**: Gere uma chave forte e única para ambientes de produção
  - Você pode gerar uma chave com: `openssl rand -hex 32`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tempo de expiração dos tokens de acesso em minutos

### CORS (Cross-Origin Resource Sharing)
- `BACKEND_CORS_ORIGINS`: Lista de origens permitidas para CORS, separadas por vírgula

### Banco de Dados
- `POSTGRES_SERVER`: Endereço do servidor PostgreSQL
- `POSTGRES_USER`: Usuário do PostgreSQL
- `POSTGRES_PASSWORD`: Senha do PostgreSQL
- `POSTGRES_DB`: Nome do banco de dados
- `SQLALCHEMY_DATABASE_URI`: URI completa de conexão com o banco de dados (opcional)
- `DATABASE_URL`: Alias para a URI do banco de dados (opcional)

### Google OAuth (se utilizado)
- `GOOGLE_CLIENT_ID`: ID do cliente OAuth do Google
- `GOOGLE_CLIENT_SECRET`: Chave secreta do cliente OAuth do Google
- `GOOGLE_REDIRECT_URI`: URI de redirecionamento para autenticação OAuth

### Limitação de Taxa
- `RATE_LIMIT_PER_MINUTE`: Número máximo de requisições permitidas por minuto

## Configuração para Produção

Em ambientes de produção, como Azure Functions, configure as variáveis de ambiente através do painel de configuração do serviço ou usando ferramentas de CI/CD.

### Azure Functions

Para o Azure Functions, você pode configurar as variáveis de ambiente no portal do Azure:

1. Acesse o portal do Azure e navegue até sua Function App
2. Vá para "Configuração" > "Configurações do aplicativo"
3. Adicione cada variável de ambiente necessária como um par chave-valor
4. Clique em "Salvar" para aplicar as alterações

## Boas Práticas de Segurança

1. **Nunca comite arquivos .env ou local.settings.json no repositório**
2. Use segredos diferentes para ambientes de desenvolvimento e produção
3. Limite o acesso às credenciais de produção apenas a pessoas autorizadas
4. Considere o uso de um serviço de gerenciamento de segredos como Azure Key Vault para ambientes de produção
5. Rotacione regularmente as chaves secretas e senhas