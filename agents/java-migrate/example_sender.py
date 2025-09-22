"""
Exemplo de como enviar uma mensagem para a fila SQS para análise de código.
Este script demonstra o formato esperado das mensagens usando o modelo Analyze.
"""
import os
import boto3
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

def send_analysis_request(repo: str, analyzers: list[str], params: dict = None, queue_url: str = None):
    """
    Envia uma requisição de análise de código para a fila SQS.
    
    Args:
        repo: Nome/URL do repositório a ser analisado
        analyzers: Lista de analisadores a executar ["java8to21", "simpler3to4"]
        params: Parâmetros adicionais (opcional)
        queue_url: URL da fila SQS
    """
    sqs_client = boto3.client('sqs')
    
    message_body = {
        "id": str(uuid.uuid4()),
        "repo": repo,
        "analyzers": analyzers,
        "params": params or {}
    }
    
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
        MessageAttributes={
            'request_type': {
                'StringValue': 'code_analysis',
                'DataType': 'String'
            },
            'repo': {
                'StringValue': repo,
                'DataType': 'String'
            }
        }
    )
    
    print(f"Mensagem enviada com ID: {response['MessageId']}")
    print(f"Request ID: {message_body['id']}")
    return response

if __name__ == "__main__":
    # Configurar suas credenciais AWS e URL da fila
    queue_url = os.getenv("SQS_QUEUE_URL", "http://localhost:4566/000000000000/your-queue-name")
    
    try:
        # Exemplo 1: Apenas migração Java
        send_analysis_request(
            repo="https://github.com/example/java-project.git",
            analyzers=["java8to21"],
            params={"branch": "main", "target_version": "21"},
            queue_url=queue_url
        )
        
        # Exemplo 2: Múltiplos analisadores
        send_analysis_request(
            repo="my-local-repo",
            analyzers=["java8to21", "simpler3to4"],
            params={"priority": "high"},
            queue_url=queue_url
        )
        
        print("Requisições enviadas com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar requisições: {e}")