# Guia de Migrações com Alembic

Este documento descreve como utilizar o Alembic para gerenciar migrações de banco de dados no projeto SmartClip.

## Índice

1. [Introdução](#introdução)
2. [Configuração do Ambiente](#configuração-do-ambiente)
3. [Comandos Básicos](#comandos-básicos)
4. [Fluxo de Trabalho](#fluxo-de-trabalho)
5. [Exemplos Práticos](#exemplos-práticos)
6. [Solução de Problemas](#solução-de-problemas)

## Introdução

O Alembic é uma ferramenta de migração de banco de dados para SQLAlchemy. Ele permite criar, gerenciar e aplicar migrações de esquema de banco de dados de forma controlada e versionada.

No projeto SmartClip, utilizamos o Alembic para manter o esquema do banco de dados sincronizado com os modelos SQLAlchemy definidos na aplicação.

## Configuração do Ambiente

Antes de executar comandos do Alembic, certifique-se de que:

1. O ambiente virtual está ativado
2. As variáveis de ambiente estão configuradas corretamente

```bash
# Ativar ambiente virtual (Windows)
.\venv\Scripts\activate

# Ativar ambiente virtual (Linux/Mac)
source venv/bin/activate

# Configurar variáveis de ambiente
# Crie um arquivo .env.dev baseado no .env.example e configure as variáveis de banco de dados
```

## Comandos Básicos

### Verificar o Status das Migrações

Para verificar quais migrações foram aplicadas e quais estão pendentes:

```bash
alembic current
```

### Criar uma Nova Migração

Para criar uma nova migração manualmente:

```bash
alembic revision -m "descrição_da_migração"
```

Para gerar uma migração automaticamente baseada nas alterações nos modelos:

```bash
alembic revision --autogenerate -m "descrição_da_migração"
```

### Aplicar Migrações

Para aplicar todas as migrações pendentes:

```bash
alembic upgrade head
```

Para aplicar até uma migração específica:

```bash
alembic upgrade <revision_id>
```

Para aplicar um número específico de migrações a partir da atual:

```bash
alembic upgrade +<n>
```

### Reverter Migrações

Para reverter a última migração:

```bash
alembic downgrade -1
```

Para reverter até uma migração específica:

```bash
alembic downgrade <revision_id>
```

Para reverter todas as migrações:

```bash
alembic downgrade base
```

## Fluxo de Trabalho

O fluxo de trabalho típico para gerenciar migrações no projeto SmartClip é:

1. **Atualizar os modelos**: Modifique os modelos SQLAlchemy em `app/models/`
2. **Verificar se o modelo foi importado**: Certifique-se de que o modelo está importado em `app/db/base.py`
3. **Gerar a migração**: Execute `alembic revision --autogenerate -m "descrição_da_alteração"`
4. **Revisar a migração**: Verifique o arquivo gerado em `alembic/versions/` para garantir que as alterações estão corretas
5. **Aplicar a migração**: Execute `alembic upgrade head`
6. **Testar**: Verifique se as alterações foram aplicadas corretamente no banco de dados

## Exemplos Práticos

### Exemplo: Adicionando Tabelas de Créditos de Vídeo

Suponha que queremos adicionar as tabelas `tb_video_credit` e `tb_video_credit_transaction` ao banco de dados:

1. Crie os modelos em `app/models/video_credit.py` e `app/models/video_credit_transaction.py`
2. Importe os modelos em `app/db/base.py`:

```python
# app/db/base.py
from app.db.base_class import Base

# Import all the models
from app.models.user import User
# ... outros imports ...
from app.models.video_credit import VideoCredit
from app.models.video_credit_transaction import VideoCreditTransaction
```

3. Gere a migração:

```bash
alembic revision --autogenerate -m "add_video_credit_tables"
```

4. Revise o arquivo de migração gerado em `alembic/versions/`
5. Aplique a migração:

```bash
alembic upgrade head
```

### Exemplo: Modificando uma Coluna Existente

Suponha que queremos alterar o valor padrão da coluna `balance` na tabela `tb_video_credit` de 10 para 5:

1. Modifique o modelo em `app/models/video_credit.py`:

```python
balance = Column(Integer, default=5, nullable=False)  # Alterado de 10 para 5
```

2. Gere a migração:

```bash
alembic revision --autogenerate -m "change_default_credit_balance"
```

3. Revise o arquivo de migração gerado
4. Aplique a migração:

```bash
alembic upgrade head
```

## Solução de Problemas

### Migração Não Detecta Alterações

Se o Alembic não detectar alterações nos modelos ao usar `--autogenerate`:

1. Verifique se o modelo está importado em `app/db/base.py`
2. Verifique se a conexão com o banco de dados está correta
3. Certifique-se de que as alterações são suportadas pelo autogenerate (algumas alterações como renomear colunas não são detectadas automaticamente)

### Erro ao Aplicar Migração

Se ocorrer um erro ao aplicar uma migração:

1. Verifique a mensagem de erro para identificar o problema
2. Corrija o arquivo de migração manualmente se necessário
3. Se a migração já foi parcialmente aplicada, pode ser necessário reverter manualmente algumas alterações no banco de dados

### Conflitos de Migração

Se houver conflitos entre migrações (por exemplo, quando várias pessoas criam migrações simultaneamente):

1. Identifique qual migração deve ser a base para as outras
2. Atualize o atributo `down_revision` nas outras migrações para apontar para a migração base
3. Resolva quaisquer conflitos nas operações de migração

---

Para mais informações, consulte a [documentação oficial do Alembic](https://alembic.sqlalchemy.org/en/latest/).