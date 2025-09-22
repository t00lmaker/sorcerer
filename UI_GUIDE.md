# 🖥️ Interfaces Gráficas para Desenvolvimento

Este documento descreve as interfaces gráficas disponíveis para monitorar e gerenciar o sistema durante o desenvolvimento.

## 🚀 Como Iniciar

```bash
# Subir todos os serviços
docker-compose up -d

# Aguardar alguns segundos para inicialização completa
sleep 10

# Verificar status
docker-compose ps
```

## 📊 DynamoDB Admin

**URL:** http://localhost:8001

### Funcionalidades:
- ✅ Visualizar todas as tabelas DynamoDB
- ✅ Navegar pelos dados das tabelas
- ✅ Executar queries e scans
- ✅ Criar, editar e deletar itens
- ✅ Exportar dados em JSON

### Como Usar:
1. Acesse http://localhost:8001
2. Clique na tabela `CodeSuggestions`
3. Visualize as sugestões salvas pelo sistema
4. Use o filtro para buscar por `AnalysisId` específico
5. Clique em qualquer item para ver detalhes completos

### 🎯 Casos de Uso Típicos:
- **Debug**: Verificar se as sugestões estão sendo salvas corretamente
- **Monitoramento**: Acompanhar o volume de dados processados
- **Limpeza**: Deletar dados de teste

## 📬 SQS Insight

**URL:** http://localhost:8080

### Funcionalidades:
- ✅ Visualizar filas SQS
- ✅ Monitorar mensagens em tempo real
- ✅ Ver mensagens pendentes e processadas
- ✅ Estatísticas de throughput
- ✅ Interface simples e confiável

### Como Usar:
1. Acesse http://localhost:8080
2. Visualize a fila `your-queue-name`
3. Monitore mensagens chegando e sendo processadas
4. Verifique estatísticas de desempenho

### 🎯 Casos de Uso Típicos:
- **Monitoramento de Fila**: Verificar se mensagens estão chegando
- **Performance**: Monitorar latência e throughput
- **Debug**: Ver mensagens que falharam ou ficaram presas

## 🔧 Comandos Úteis

### Verificar Serviços
```bash
# Status dos containers
docker-compose ps

# Logs do LocalStack
docker-compose logs localstack

# Logs do DynamoDB Admin
docker-compose logs dynamodb-admin

# Logs do SQS Insight
docker-compose logs sqs-insight
```

### Resetar Ambiente
```bash
# Parar todos os serviços
docker-compose down

# Limpar volumes (CUIDADO: apaga todos os dados)
docker-compose down -v

# Recriar ambiente limpo
docker-compose up -d
```

### Comandos AWS CLI (LocalStack)
```bash
# Listar tabelas
aws dynamodb list-tables --endpoint-url http://localhost:4566

# Listar filas
aws sqs list-queues --endpoint-url http://localhost:4566

# Verificar itens na tabela
aws dynamodb scan --table-name CodeSuggestions --endpoint-url http://localhost:4566
```

## 🐛 Troubleshooting

### DynamoDB Admin não carrega dados
1. Verifique se o LocalStack está rodando: `docker-compose ps`
2. Aguarde a inicialização completa (pode demorar 30-60 segundos)
3. Verifique logs: `docker-compose logs dynamodb-admin`

### SQS Insight não conecta
1. Verifique se o LocalStack está rodando: `docker-compose ps`
2. Verifique se a fila foi criada: `docker-compose logs cloud-setup`
3. Aguarde a inicialização completa
4. Reinicie se necessário: `docker-compose restart sqs-insight`

### Não consigo ver dados nas tabelas
1. Verifique se a tabela foi criada: `docker-compose logs cloud-setup`
2. Envie uma mensagem de teste: `python example_sender.py`
3. Execute o processador: `python main.py`

## 📱 Screenshots das Interfaces

### DynamoDB Admin
```
┌─────────────────────────────────────────────┐
│ DynamoDB Admin                              │
├─────────────────────────────────────────────┤
│ Tables:                                     │
│ ├── CodeSuggestions (XX items)             │
│ │   ├── AnalysisId: uuid-123...            │
│ │   ├── SuggestionId: uuid-456...          │
│ │   └── Description: "Migrate to Optional" │
│ └── (outras tabelas...)                    │
└─────────────────────────────────────────────┘
```

### LocalStack Web UI
```
┌─────────────────────────────────────────────┐
│ LocalStack Dashboard                        │
├─────────────────────────────────────────────┤
│ Services Status:                            │
│ ├── SQS: ✅ Running (1 queue)               │
│ ├── DynamoDB: ✅ Running (1 table)          │
│ └── Other services...                      │
└─────────────────────────────────────────────┘
```

## 🎯 Próximos Passos

1. **Inicie os serviços**: `docker-compose up -d`
2. **Acesse o DynamoDB Admin**: http://localhost:8001
3. **Envie mensagens de teste**: `python example_sender.py`
4. **Execute o processador**: `python main.py`
5. **Monitore os dados**: Acompanhe em tempo real pelas interfaces

Happy debugging! 🚀