"""
Exemplo de como enviar uma mensagem para a fila SQS para análise de código.
Este script demonstra o formato esperado das mensagens.
"""
import os
import boto3
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
def send_analysis_request(java_code: str, file_path: str, queue_url: str):
    """
    Envia uma requisição de análise de código para a fila SQS.
    
    Args:
        java_code: Código Java a ser analisado
        file_path: Caminho do arquivo (pode ser fictício)
        queue_url: URL da fila SQS
    """
    sqs_client = boto3.client('sqs', 'us-east-1')
    
    message_body = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "java_code": java_code,
        "file_path": file_path,
        "metadata": {
            "source": "example_sender",
            "priority": "normal"
        }
    }
    
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
        MessageAttributes={
            'request_type': {
                'StringValue': 'java_code_analysis',
                'DataType': 'String'
            },
            'priority': {
                'StringValue': 'normal',
                'DataType': 'String'
            }
        }
    )
    
    print(f"Mensagem enviada com ID: {response['MessageId']}")
    return response

if __name__ == "__main__":
    # Exemplo de código Java
    example_java_code = """
    public class ExampleClass {
        private String name;
        
        public ExampleClass(String name) {
            this.name = name;
        }
        
        public String getName() {
            return name;
        }
        
        public void setName(String name) {
            this.name = name;
        }
        
        // Método com possível melhoria
        public void printInfo() {
            System.out.println("Nome: " + name);
        }
    }
    """
    
    
    try:
        send_analysis_request(example_java_code, "ExampleClass.java", os.getenv('SQS_QUEUE_URL'))
        print("Requisição enviada com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar requisição: {e}")