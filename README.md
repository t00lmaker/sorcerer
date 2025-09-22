
## Commando utilitários 


Add uma analise não conclusiva na tabela CodeSuggestions:

```sh
aws dynamodb put-item \
    --table-name CodeSuggestions --region us-east-1 \
    --item '{
        "AnalysisId": {"S": "66e51d1b-d294-4184-b0a6-dc0d2a568e76"},
        "SuggestionId": {"S": "8b874d22-708e-40e7-b1e1-6c7a8470491b"}, 
        "Analyzer": {"S": "java8to21"},
        "FilePath": {"S": "/path/to/file.java"},
        "Description": {"S": "Update method to use Java 21 features"},
        "StartLine": {"N": "10"},
        "EndLine": {"N": "20"},
        "OriginalSnippet": {"S": "public void oldMethod() {}"},
        "ModifiedCode": {"S": "public void newMethod() {}"},
        "DifficultyLevel": {"N": "2"}
    }' \
    --endpoint-url http://localhost:4566
```

Add uma analise conclusiva na tabela CodeSuggestions:

```sh
aws dynamodb put-item \
    --table-name CodeSuggestions --region us-east-1 \
    --item '{
        "AnalysisId": {"S": "66e51d1b-d294-4184-b0a6-dc0d2a568e76"},
        "SuggestionId": {"S": "8b874d22-708e-40e7-b1e1-6c7a8470491b"}, 
        "Analyzer": {"S": "java8to21"},
        "FilePath": {"S": "/path/to/file.java"},
        "Description": {"S": "Update method to use Java 21 features"},
        "StartLine": {"N": "10"},
        "EndLine": {"N": "20"},
        "OriginalSnippet": {"S": "public void oldMethod() {}"},
        "ModifiedCode": {"S": "public void newMethod() {}"},
        "DifficultyLevel": {"N": "2"},
        "Last": {"BOOL": true}
    }' \
    --endpoint-url http://localhost:4566
```

Query para recuperar CodeSugestions de uma analise especifica:

```sh
aws dynamodb query \
    --table-name CodeSuggestions --region us-east-1 \
    --key-condition-expression "AnalysisId = :analysisId" \
    --expression-attribute-values '{":analysisId":{"S":"analysis-123"}}' \
    --endpoint-url http://localhost:4566
```

Pegar uma sugestions especifica: 

```sh
aws dynamodb get-item --region us-east-1 \
    --table-name CodeSuggestions \
    --key '{"SuggestionId": {"S": "suggestion-1"}, "AnalysisId": { "S": "analysis-123"}}' \  
    --endpoint-url http://localhost:4566
```