import os
import json
import asyncio
import logging
import boto3
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from prompts.java_migration_prompt import system_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class AnalyzerEnum(str, Enum):
    JAVA8_TO_21 = "java8to21"
    SIMPLER_3_TO_4 = "simpler3to4"

class Analyze(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Identificador único da requisição de análise, não é necessário fornecer")
    repo: str = Field(description="Nome ou URL do repositório que será analisado")
    analyzers: list[AnalyzerEnum] = Field(description="Lista de analisadores que devem ser executados (java8to21, simpler3to4)")
    params: Optional[dict[str, str]] = Field(default=None, description="Parâmetros adicionais específicos para os analisadores")

class Suggestion(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Identificador único da sugestão, não é necessário fornecer")
    file_path: str = Field(description="Caminho completo do arquivo Java que está sendo analisado")
    description: str = Field(description="Descrição clara e concisa da sugestão de migração ou melhoria proposta")
    start_line: int = Field(description="Número da linha onde inicia o trecho de código que deve ser modificado (baseado em 1)")
    end_line: int = Field(description="Número da linha onde termina o trecho de código que deve ser modificado (baseado em 1)")
    original_snippet: str = Field(description="Trecho exato do código original que deve ser substituído")
    modified_code: str = Field(description="Código modificado/melhorado que deve substituir o trecho original")
    difficulty_level: int = Field(description="Nível de dificuldade da implementação de 1 a 5, onde 1=muito fácil, 2=fácil, 3=médio, 4=difícil, 5=muito difícil")
    last: bool = Field(default=False, description="Indica se esta é a última sugestão para este arquivo (true) ou se há mais sugestões (false)")
    analyzer: AnalyzerEnum = Field(description="Tipo de analisador que gerou esta sugestão (java8to21 ou simpler3to4)")
    additional_notes: Optional[str] = Field(default=None, description="Notas adicionais, explicações técnicas ou considerações importantes sobre a sugestão")

class SuggestionsList(BaseModel):
    suggestions: List[Suggestion] = Field(description="Lista de todas as sugestões de migração encontradas no código analisado")

class LangChainAgent:
    def __init__(self, prompt_template: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0,
        )
        self.parser = PydanticOutputParser(pydantic_object=SuggestionsList)
        self.prompt = PromptTemplate(template=prompt_template)
        self.chain = self.llm | self.parser

    def generate_suggestions(self, java_code: str, file_path: str) -> SuggestionsList:
        prompt = self.prompt.format(
            file_path=file_path,
            code_class=java_code, 
            output_format=self.parser.get_format_instructions()
        )
        
        return self.chain.invoke(prompt)

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
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.suggestions_table = self.dynamodb.Table(os.getenv('DYNAMODB_SUGGESTIONS_TABLE', 'CodeSuggestions'))
        self.queue_url = os.getenv('SQS_QUEUE_URL')
        self.running = True
        
        if not self.queue_url:
            raise ValueError("SQS_QUEUE_URL deve estar configurado nas variáveis de ambiente")
        
        logger.info(f"Processador iniciado com {max_workers} workers")
        logger.info(f"Utilizando fila SQS: {self.queue_url}")
        logger.info(f"Utilizando tabela DynamoDB: {self.suggestions_table.name}")

    async def process_code_analysis_request(self, message_body: Dict[Any, Any], receipt_handle: str) -> None:
        """
        Processa uma requisição de análise de código de forma assíncrona.
        
        Args:
            message_body: Corpo da mensagem SQS contendo os dados para análise
            receipt_handle: Handle da mensagem para deletar após processamento
        """
        start_time = datetime.now()
        
        try:
            # Carregar mensagem em uma instância de Analyze
            analyze_request = Analyze(**message_body)
            request_id = str(analyze_request.id) if analyze_request.id else 'unknown'
            
            logger.info(f"Iniciando processamento da requisição {request_id}")
            logger.info(f"Repo: {analyze_request.repo}")
            logger.info(f"Analisadores: {[analyzer.value for analyzer in analyze_request.analyzers]}")
            
            # Processar cada analisador configurado
            for analyzer in analyze_request.analyzers:
                await self._process_analyzer(analyze_request, analyzer, receipt_handle, request_id)
            
            # Deletar mensagem da fila após processamento bem-sucedido
            await self._delete_message(receipt_handle)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Requisição {request_id} processada com sucesso em {processing_time:.2f}s")
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Erro ao processar requisição após {processing_time:.2f}s: {str(e)}")
            # Em caso de erro, a mensagem não é deletada e voltará para a fila
            # Você pode implementar uma fila DLQ (Dead Letter Queue) para mensagens com muitos erros

    async def _process_analyzer(self, analyze_request: Analyze, analyzer: AnalyzerEnum, receipt_handle: str, request_id: str) -> None:
        """
        Processa um analisador específico baseado no tipo.
        
        Args:
            analyze_request: Instância do modelo Analyze com os dados da requisição
            analyzer: Tipo de analisador a ser executado
            receipt_handle: Handle da mensagem SQS
            request_id: ID da requisição para logging
        """
        try:
            logger.info(f"Processando analisador {analyzer.value} para requisição {request_id}")
            
            if analyzer == AnalyzerEnum.JAVA8_TO_21:
                await self._process_java_migration(analyze_request, request_id)
            elif analyzer == AnalyzerEnum.SIMPLER_3_TO_4:
                await self._process_simpler_migration(analyze_request, request_id)
            else:
                logger.warning(f"Analisador não implementado: {analyzer.value}")
                
        except Exception as e:
            logger.error(f"Erro ao processar analisador {analyzer.value} para requisição {request_id}: {str(e)}")
            raise

    async def _process_java_migration(self, analyze_request: Analyze, request_id: str) -> None:
        """
        Processa migração Java 8 para 21 usando o agente atual.
        
        Args:
            analyze_request: Dados da requisição de análise
            request_id: ID da requisição para logging
        """
        logger.info(f"Iniciando análise Java 8->21 para repo: {analyze_request.repo}")
        
        # Aqui você implementaria a lógica para:
        # 1. Clonar/acessar o repositório
        # 2. Encontrar arquivos .java
        # 3. Processar cada arquivo com o agente
        
        # Por enquanto, vou simular com um exemplo
        # TODO: Implementar acesso real ao repositório
        
        example_java_code = "// Código exemplo do repositório"
        file_path = f"{analyze_request.repo}/Example.java"
        
        # Executar análise em uma thread separada
        loop = asyncio.get_event_loop()
        suggestions_list = await loop.run_in_executor(
            self.executor, 
            self.agent.generate_suggestions, 
            example_java_code, 
            file_path
        )
        
        logger.info(f"Análise Java concluída para {request_id}: {len(suggestions_list.suggestions)} sugestões geradas")
        
        # Processar resultados
        await self._handle_analysis_results(request_id, suggestions_list, analyze_request)

    async def _process_simpler_migration(self, analyze_request: Analyze, request_id: str) -> None:
        """
        Processa migração Simpler 3 para 4.
        
        Args:
            analyze_request: Dados da requisição de análise
            request_id: ID da requisição para logging
        """
        logger.info(f"Iniciando análise Simpler 3->4 para repo: {analyze_request.repo}")
        
        # TODO: Implementar lógica específica para migração Simpler
        # Por enquanto, apenas log
        logger.info(f"Processamento Simpler concluído para {request_id}")

    async def _handle_analysis_results(self, request_id: str, suggestions_list, analyze_request: Analyze) -> None:
        """
        Processa os resultados da análise. Salva as sugestões no DynamoDB.
        
        Args:
            request_id: ID da requisição para logging
            suggestions_list: Lista de sugestões geradas pelo agente
            analyze_request: Dados da requisição de análise original
        """
        logger.info(f"Processando resultados da análise {request_id} para repo: {analyze_request.repo}")
        
        try:
            # Salvar cada sugestão no DynamoDB
            for suggestion in suggestions_list.suggestions:
                await self._save_suggestion_to_dynamodb(suggestion, analyze_request, request_id)
                
                # Log da sugestão processada
                logger.info(
                    f"Sugestão salva para {request_id}: "
                    f"Arquivo {suggestion.file_path}, "
                    f"Linhas {suggestion.start_line}-{suggestion.end_line}, "
                    f"Dificuldade: {suggestion.difficulty_level}"
                )
            
            logger.info(f"Todas as {len(suggestions_list.suggestions)} sugestões foram salvas no DynamoDB para requisição {request_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultados no DynamoDB para requisição {request_id}: {str(e)}")
            raise

    async def _save_suggestion_to_dynamodb(self, suggestion: Suggestion, analyze_request: Analyze, request_id: str) -> None:
        """
        Salva uma sugestão individual no DynamoDB.
        
        Args:
            suggestion: Instância da sugestão a ser salva
            analyze_request: Dados da requisição de análise original
            request_id: ID da requisição para referência
        """
        try:
            # Gerar ID único para a sugestão se não existir
            if not suggestion.id:
                suggestion.id = uuid4()
            
            # Configurar chaves conforme especificação da tabela DynamoDB
            # HASH key (partition key) e RANGE key (sort key)
            item = {
                'AnalysisId': request_id,  # HASH key (partition key)
                'SuggestionId': str(suggestion.id),  # RANGE key (sort key)
                'FilePath': suggestion.file_path,
                'Analyzer': suggestion.analyzer.value,
                'Description': suggestion.description,
                'StartLine': suggestion.start_line,
                'EndLine': suggestion.end_line,
                'OriginalSnippet': suggestion.original_snippet,
                'ModifiedCode': suggestion.modified_code,
                'DifficultyLevel': suggestion.difficulty_level,
                'Last': suggestion.last,
                'AdditionalNotes': suggestion.additional_notes or '',
                
                # Campos extras de contexto
                'repo': analyze_request.repo,
                'created_at': datetime.now().isoformat(),
                'status': 'pending',  # pending, approved, rejected
                'metadata': {
                    'params': analyze_request.params or {},
                    'processed_by': 'sqs-processor',
                    'version': '1.0'
                }
            }
            
            # Salvar no DynamoDB de forma assíncrona
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.suggestions_table.put_item(Item=item)
            )
            
            logger.debug(f"Sugestão {item['SuggestionId']} salva no DynamoDB para análise {item['AnalysisId']}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar sugestão individual no DynamoDB: {str(e)}")
            raise

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
                            logger.error(f"Erro ao fazer parse JSON da mensagem: {str(e)}")
                            # Deletar mensagem inválida
                            await self._delete_message(message['ReceiptHandle'])
                        except Exception as e:
                            logger.error(f"Erro ao processar estrutura da mensagem: {str(e)}")
                            # Deletar mensagem com estrutura inválida
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