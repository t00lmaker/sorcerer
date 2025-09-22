# Sistema de Análise de Código Java Orientado por Eventos

Este sistema implementa um processador assíncrono de análise de código Java usando Amazon SQS como fila de mensagens, permitindo processamento paralelo e orientado por eventos.

## Arquitetura

O sistema funciona da seguinte forma:

1. **Polling Contínuo**: O agente consulta continuamente a fila SQS buscando novas mensagens
2. **Processamento Assíncrono**: Cada mensagem é processada em uma thread separada usando ThreadPoolExecutor
3. **Processamento Paralelo**: Múltiplas mensagens podem ser processadas simultaneamente
4. **Aguarda Inteligente**: Quando não há mensagens, o sistema aguarda 10 segundos antes da próxima consulta
5. **Long Polling**: Utiliza long polling do SQS (20 segundos) para reduzir custos e latência

## Configuração

### 1. Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Configurações do Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# Configurações AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1

# Configurações SQS
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/code-analysis-queue

# Configurações DynamoDB
DYNAMODB_SUGGESTIONS_TABLE=CodeSuggestions

# Configurações do processador
MAX_WORKERS=5
```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 3. Executando com Docker Compose (Desenvolvimento Local)

Para desenvolvimento local, você pode usar o LocalStack que simula os serviços AWS:

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar se os serviços estão rodando
docker-compose ps
```

**Interfaces Gráficas Disponíveis:**

1. **DynamoDB Admin** - Interface para visualizar tabelas DynamoDB
   - URL: http://localhost:8001
   - Permite visualizar, editar e consultar dados das tabelas
   - Ideal para debug e monitoramento das sugestões salvas

2. **SQS Insight** - Interface para monitorar filas SQS
   - URL: http://localhost:8080
   - Visualização de filas, mensagens em tempo real
   - Estatísticas de throughput e performance

3. **API do Sistema** - Sua API principal
   - URL: http://localhost:8000
   - Endpoints para interação com o sistema

### 4. Configuração da Infraestrutura AWS (Produção)

#### Fila SQS
Crie uma fila SQS no AWS Console com as seguintes configurações recomendadas:

- **Visibility Timeout**: 900 segundos (15 minutos)
- **Message Retention**: 14 dias
- **Receive Message Wait Time**: 20 segundos (para long polling)
- **Dead Letter Queue**: Recomendado para mensagens com falha

#### Tabela DynamoDB
Crie uma tabela DynamoDB com a seguinte configuração:

```bash
aws dynamodb create-table \
    --table-name CodeSuggestions \
    --attribute-definitions \
        AttributeName=AnalysisId,AttributeType=S \
        AttributeName=SuggestionId,AttributeType=S \
    --key-schema \
        AttributeName=AnalysisId,KeyType=HASH \
        AttributeName=SuggestionId,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

**Configuração da tabela:**
- **Nome da tabela**: `CodeSuggestions`
- **Partition Key (HASH)**: `AnalysisId` (String) - ID da análise
- **Sort Key (RANGE)**: `SuggestionId` (String) - ID da sugestão
- **Billing Mode**: Provisioned (5 RCU, 5 WCU) ou On-Demand conforme necessário

**Estrutura dos itens salvos no DynamoDB:**
```json
{
  "AnalysisId": "uuid-da-requisicao",
  "SuggestionId": "uuid-da-sugestao",
  "AnalyzerId": "uuid-da-requisicao",
  "FilePath": "caminho/para/arquivo.java",
  "Analyzer": "java8to21",
  "Description": "Descrição da sugestão",
  "StartLine": 10,
  "EndLine": 15,
  "OriginalSnippet": "código original",
  "ModifiedCode": "código modificado",
  "DifficultyLevel": 3,
  "Last": false,
  "AdditionalNotes": "notas adicionais",
  "repo": "nome-do-repositorio",
  "created_at": "2025-09-21T10:30:00",
  "status": "pending",
  "metadata": {
    "params": {},
    "processed_by": "sqs-processor",
    "version": "1.0"
  }
}
```

**Como recuperar os dados:**
```python
# Exemplo de recuperação usando o modelo Suggestion
item = dynamodb_response['Item']
suggestion = Suggestion(
    id=item['SuggestionId'],
    analyzer_id=item['AnalyzerId'],
    file_path=item['FilePath'],
    analyzer=AnalyzerEnum(item['Analyzer']),
    description=item['Description'],
    start_line=int(item['StartLine']),
    end_line=int(item['EndLine']),
    original_snippet=item['OriginalSnippet'],
    modified_code=item['ModifiedCode'],
    difficulty_level=int(item['DifficultyLevel']),
    additional_notes=item.get('AdditionalNotes'),
    last=bool(item['Last']) if 'Last' in item else False
)
```

## Uso

### Executando o Processador

```bash
python main.py
```

O processador irá:
- Conectar na fila SQS configurada
- Iniciar o loop de polling contínuo
- Processar mensagens conforme chegam
- Logar todas as atividades

### Formato das Mensagens SQS

As mensagens devem seguir o modelo `Analyze` com o seguinte formato JSON:

```json
{
  "id": "uuid-unique-id",
  "repo": "https://github.com/example/java-project.git",
  "analyzers": ["java8to21", "simpler3to4"],
  "params": {
    "branch": "main",
    "target_version": "21",
    "priority": "high"
  }
}
```

**Campos:**
- `id`: UUID único da requisição (opcional, será gerado se não fornecido)
- `repo`: Nome ou URL do repositório a ser analisado
- `analyzers`: Array de analisadores a executar (`java8to21`, `simpler3to4`)
- `params`: Parâmetros adicionais específicos do analisador (opcional)

### Enviando Mensagens de Teste

Use o script `example_sender.py` para enviar mensagens de teste:

```bash
python example_sender.py
```

## Monitoramento e Debug

### Usando DynamoDB Admin

1. Acesse http://localhost:8001
2. Visualize a tabela `CodeSuggestions`
3. Consulte os dados salvos em tempo real
4. Execute queries para filtrar sugestões por `AnalysisId`

### Usando SQS Insight

1. Acesse http://localhost:8080
2. Visualize a fila `your-queue-name`
3. Monitore mensagens chegando em tempo real
4. Verifique estatísticas de throughput e performance

### Queries Úteis no DynamoDB

**Buscar todas as sugestões de uma análise:**
```bash
# Via AWS CLI (LocalStack)
aws dynamodb query \
  --table-name CodeSuggestions \
  --key-condition-expression "AnalysisId = :aid" \
  --expression-attribute-values '{":aid":{"S":"seu-analysis-id"}}' \
  --endpoint-url http://localhost:4566
```

**Contar sugestões por status:**
```bash
# Scan com filtro
aws dynamodb scan \
  --table-name CodeSuggestions \
  --filter-expression "#status = :status" \
  --expression-attribute-names '{"#status":"status"}' \
  --expression-attribute-values '{":status":{"S":"pending"}}' \
  --select COUNT \
  --endpoint-url http://localhost:4566
```

## Logs de Exemplo
```

## Características do Sistema

### ✅ Processamento Assíncrono
- Cada mensagem é processada em uma thread separada
- Não bloqueia o recebimento de novas mensagens
- Processamento paralelo de múltiplas requisições

### ✅ Polling Eficiente
- Long polling de 20 segundos reduz custos
- Aguarda 10 segundos quando não há mensagens
- Consulta contínua sem sobrecarregar o SQS

### ✅ Tratamento de Erros
- Logging detalhado de todas as operações
- Mensagens com erro voltam para a fila automaticamente
- Suporte a Dead Letter Queue para mensagens problemáticas

### ✅ Escalabilidade
- Configurável número de workers (threads)
- Pode processar até 10 mensagens simultâneas por consulta
- Fácil de executar múltiplas instâncias para escalar horizontalmente

### ✅ Monitoramento
- Logs estruturados com timestamps
- Métricas de tempo de processamento
- IDs únicos para rastreamento de requisições

### ✅ Instruções Inteligentes para LLM
- Modelos Pydantic com descrições detalhadas dos campos
- `PydanticOutputParser` gera instruções precisas para o LLM
- Cada campo tem uma descrição que ajuda o LLM a entender o propósito
- Melhora a qualidade e consistência das respostas geradas

**Exemplo de como as descrições ajudam o LLM:**
```python
class Suggestion(BaseModel):
    file_path: str = Field(description="Caminho completo do arquivo Java que está sendo analisado")
    description: str = Field(description="Descrição clara e concisa da sugestão de migração ou melhoria proposta")
    start_line: int = Field(description="Número da linha onde inicia o trecho de código que deve ser modificado (baseado em 1)")
    difficulty_level: int = Field(description="Nível de dificuldade da implementação de 1 a 5, onde 1=muito fácil, 2=fácil, 3=médio, 4=difícil, 5=muito difícil")
```

Essas descrições são automaticamente incluídas nas instruções enviadas para o LLM, resultando em:
- Respostas mais precisas e consistentes
- Melhor compreensão do formato esperado
- Redução de erros de parsing
- Campos preenchidos corretamente

## Logs de Exemplo

```
2025-09-21 10:30:00,123 - __main__ - INFO - Processador iniciado com 5 workers
2025-09-21 10:30:00,124 - __main__ - INFO - Utilizando fila SQS: https://sqs.us-east-1.amazonaws.com/123456789012/code-analysis-queue
2025-09-21 10:30:00,125 - __main__ - INFO - Iniciando processamento orientado por eventos
2025-09-21 10:30:02,456 - __main__ - INFO - Recebidas 3 mensagens para processamento
2025-09-21 10:30:02,457 - __main__ - INFO - Iniciadas 3 tasks de processamento assíncrono
2025-09-21 10:30:02,458 - __main__ - INFO - Iniciando processamento da requisição abc-123
2025-09-21 10:30:05,789 - __main__ - INFO - Análise concluída para abc-123: 4 sugestões geradas
2025-09-21 10:30:05,790 - __main__ - INFO - Requisição abc-123 processada com sucesso em 3.33s
```

## Extensões Possíveis

O sistema pode ser facilmente estendido para:

1. **Enviar Resultados**: Modificar `_handle_analysis_results()` para enviar resultados via:
   - Outra fila SQS
   - Banco de dados
   - API HTTP callback
   - S3 bucket

2. **Filtros de Mensagem**: Adicionar filtros baseados em atributos da mensagem

3. **Priorização**: Implementar processamento baseado em prioridade

4. **Métricas**: Integrar com CloudWatch para métricas detalhadas

5. **Healthcheck**: Adicionar endpoint de saúde para monitoramento

## Troubleshooting

### Problema: Não conecta no SQS
- Verifique as credenciais AWS
- Confirme a região e URL da fila
- Verifique permissões IAM

### Problema: Mensagens não são processadas
- Verifique o formato JSON das mensagens
- Confirme se a API Key do Google está correta
- Verifique logs para erros específicos

### Problema: Processamento muito lento
- Aumente o número de workers (MAX_WORKERS)
- Execute múltiplas instâncias do processador
- Otimize o prompt do Gemini