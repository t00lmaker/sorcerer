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

# Configurações AWS SQS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/code-analysis-queue

# Configurações do processador
MAX_WORKERS=5
```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 3. Configuração da Fila SQS

Crie uma fila SQS no AWS Console com as seguintes configurações recomendadas:

- **Visibility Timeout**: 300 segundos (5 minutos)
- **Message Retention**: 14 dias
- **Receive Message Wait Time**: 20 segundos (para long polling)
- **Dead Letter Queue**: Recomendado para mensagens com falha

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

As mensagens devem ter o seguinte formato JSON:

```json
{
  "request_id": "uuid-unique-id",
  "timestamp": "2025-09-21T10:30:00",
  "java_code": "public class Example { ... }",
  "file_path": "path/to/file.java",
  "metadata": {
    "source": "api",
    "priority": "normal"
  }
}
```

### Enviando Mensagens de Teste

Use o script `example_sender.py` para enviar mensagens de teste:

```bash
python example_sender.py
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