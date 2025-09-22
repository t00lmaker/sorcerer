import os
import json
import asyncio
import logging
import boto3
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from datetime import datetime
from langchain_agent import LangChainAgent
from dotenv import load_dotenv
from prompts.java_migration_prompt import system_prompt

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class SQSCodeAnalysisProcessor:
    def __init__(self, max_workers: int = 5):
        """
        Inicializa o processador de análise de código via SQS.
        
        Args:
            max_workers: Número máximo de threads para processamento paralelo
        """
        self.agent = LangChainAgent(prompt_template=system_prompt)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.sqs_client = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.queue_url = os.getenv('SQS_QUEUE_URL')
        self.running = True
        
        if not self.queue_url:
            raise ValueError("SQS_QUEUE_URL deve estar configurado nas variáveis de ambiente")
        
        logger.info(f"Processador iniciado com {max_workers} workers")
        logger.info(f"Utilizando fila SQS: {self.queue_url}")

    async def process_code_analysis_request(self, message_body: Dict[Any, Any], receipt_handle: str) -> None:
        """
        Processa uma requisição de análise de código de forma assíncrona.
        
        Args:
            message_body: Corpo da mensagem SQS contendo os dados para análise
            receipt_handle: Handle da mensagem para deletar após processamento
        """
        start_time = datetime.now()
        request_id = message_body.get('request_id', 'unknown')
        
        try:
            logger.info(f"Iniciando processamento da requisição {request_id}")
            
            # Extrair dados da mensagem
            java_code = message_body.get('java_code')
            file_path = message_body.get('file_path', 'unknown_file.java')
            
            if not java_code:
                raise ValueError("Campo 'java_code' não encontrado na mensagem")
            
            # Executar análise em uma thread separada para não bloquear o loop principal
            loop = asyncio.get_event_loop()
            suggestions_list = await loop.run_in_executor(
                self.executor, 
                self.agent.generate_suggestions, 
                java_code, 
                file_path
            )
            
            # Log dos resultados
            logger.info(f"Análise concluída para {request_id}: {len(suggestions_list.suggestions)} sugestões geradas")
            
            # Aqui você pode implementar o envio dos resultados para outro serviço
            # Por exemplo: enviar para outra fila SQS, salvar no banco de dados, etc.
            await self._handle_analysis_results(request_id, suggestions_list, message_body)
            
            # Deletar mensagem da fila após processamento bem-sucedido
            await self._delete_message(receipt_handle)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Requisição {request_id} processada com sucesso em {processing_time:.2f}s")
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Erro ao processar requisição {request_id} após {processing_time:.2f}s: {str(e)}")
            # Em caso de erro, a mensagem não é deletada e voltará para a fila
            # Você pode implementar uma fila DLQ (Dead Letter Queue) para mensagens com muitos erros

    async def _handle_analysis_results(self, request_id: str, suggestions_list, original_message: Dict[Any, Any]) -> None:
        """
        Processa os resultados da análise. Aqui você pode implementar:
        - Envio para outra fila SQS
        - Salvamento em banco de dados
        - Callback HTTP
        - etc.
        """
        logger.info(f"Processando resultados da análise {request_id}")
        
        # Exemplo de log dos resultados (você pode modificar conforme necessário)
        for suggestion in suggestions_list.suggestions:
            logger.info(
                f"Sugestão para {request_id}: "
                f"Linhas {suggestion.start_line}-{suggestion.end_line}, "
                f"Dificuldade: {suggestion.difficulty_level}"
            )

    async def _delete_message(self, receipt_handle: str) -> None:
        """
        Deleta mensagem da fila SQS após processamento bem-sucedido.
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            )
        except Exception as e:
            logger.error(f"Erro ao deletar mensagem da fila: {str(e)}")

    async def _receive_messages(self) -> list:
        """
        Recebe mensagens da fila SQS de forma assíncrona.
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,  # Recebe até 10 mensagens por vez
                    WaitTimeSeconds=20,  # Long polling de 20 segundos
                    MessageAttributeNames=['All']
                )
            )
            
            return response.get('Messages', [])
        
        except Exception as e:
            logger.error(f"Erro ao receber mensagens da fila SQS: {str(e)}")
            return []

    async def start_event_driven_processing(self) -> None:
        """
        Inicia o loop principal de processamento orientado por eventos.
        
        Este método:
        1. Consulta continuamente a fila SQS
        2. Processa cada mensagem em uma thread separada
        3. Aguarda 10 segundos quando não há mensagens
        4. Continua até que self.running seja False
        """
        logger.info("Iniciando processamento orientado por eventos")
        
        while self.running:
            try:
                # Receber mensagens da fila
                messages = await self._receive_messages()
                
                if messages:
                    logger.info(f"Recebidas {len(messages)} mensagens para processamento")
                    
                    # Processar cada mensagem assincronamente
                    tasks = []
                    for message in messages:
                        try:
                            # Parse do corpo da mensagem
                            message_body = json.loads(message['Body'])
                            receipt_handle = message['ReceiptHandle']
                            
                            # Criar task para processamento assíncrono
                            task = asyncio.create_task(
                                self.process_code_analysis_request(message_body, receipt_handle)
                            )
                            tasks.append(task)
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Erro ao fazer parse da mensagem: {str(e)}")
                            # Deletar mensagem inválida
                            await self._delete_message(message['ReceiptHandle'])
                    
                    # Não esperar as tasks terminarem - processamento paralelo
                    logger.info(f"Iniciadas {len(tasks)} tasks de processamento assíncrono")
                    
                else:
                    # Sem mensagens - aguardar 10 segundos antes da próxima consulta
                    logger.info("Nenhuma mensagem na fila. Aguardando 10 segundos...")
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"Erro no loop principal: {str(e)}")
                await asyncio.sleep(10)  # Aguardar antes de tentar novamente

    def stop(self) -> None:
        """
        Para o processamento e limpa recursos.
        """
        logger.info("Parando processamento...")
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("Processamento parado")

async def main():
    """
    Função principal que inicia o processador de análise de código.
    """
    processor = SQSCodeAnalysisProcessor(max_workers=5)
    
    try:
        await processor.start_event_driven_processing()
    except KeyboardInterrupt:
        logger.info("Interrupção recebida. Parando processamento...")
    finally:
        processor.stop()

if __name__ == "__main__":
    asyncio.run(main())