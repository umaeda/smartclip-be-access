# Sistema de Logging do SmartClip

Este documento descreve o sistema de logging implementado no SmartClip Backend.

## Visão Geral

O sistema de logging foi projetado para fornecer rastreabilidade e monitoramento das atividades da aplicação. Ele utiliza a biblioteca padrão `logging` do Python com configurações personalizadas para atender às necessidades do projeto.

## Características

- Logs em diferentes níveis (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Logs enviados para console e arquivo simultaneamente
- Rotação automática de arquivos de log (10MB por arquivo, máximo de 5 arquivos)
- Middleware para logging automático de requisições HTTP
- Formatação consistente com timestamp, nível e mensagem

## Como Usar

### Importando o Logger

```python
from app.core.logger import get_logger

# Crie um logger para seu módulo específico
logger = get_logger("nome_do_modulo")
```

### Níveis de Log

```python
# Informações detalhadas (apenas em ambiente de desenvolvimento)
logger.debug("Mensagem detalhada para debugging")

# Informações gerais sobre o funcionamento da aplicação
logger.info("Operação concluída com sucesso")

# Avisos que não impedem o funcionamento, mas merecem atenção
logger.warning("Algo inesperado aconteceu, mas a aplicação continua funcionando")

# Erros que afetam uma operação específica
logger.error("Erro ao processar a requisição", exc_info=True)  # exc_info=True para incluir o traceback

# Erros críticos que podem afetar toda a aplicação
logger.critical("Erro crítico que impede o funcionamento da aplicação")
```

### Boas Práticas

1. **Seja específico**: Inclua detalhes relevantes nas mensagens de log
2. **Identifique entidades**: Inclua IDs de usuários, vídeos ou outras entidades relevantes
3. **Evite dados sensíveis**: Nunca registre senhas, tokens ou informações pessoais
4. **Use o nível apropriado**: Não use ERROR para situações normais ou INFO para erros
5. **Inclua contexto**: Adicione informações que ajudem a entender o contexto da operação

## Configuração

A configuração do logger está definida em `app/core/logger.py`. O nível de log é determinado pelo ambiente:

- **Desenvolvimento**: DEBUG (todas as mensagens)
- **Produção**: INFO (apenas INFO, WARNING, ERROR e CRITICAL)

## Arquivos de Log

Os arquivos de log são armazenados no diretório `logs/` na raiz do projeto:

- `app.log`: Arquivo de log principal
- `app.log.1`, `app.log.2`, etc.: Arquivos de backup quando ocorre rotação

## Middleware de Logging

O middleware `RequestLoggingMiddleware` registra automaticamente todas as requisições HTTP e suas respostas. Não é necessário adicionar logs manualmente para cada endpoint.