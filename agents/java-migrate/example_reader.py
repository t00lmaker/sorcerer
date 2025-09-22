"""
Exemplo de como recuperar sugestões do DynamoDB usando o modelo Suggestion.
"""
import boto3
from uuid import UUID
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class AnalyzerEnum(str, Enum):
    JAVA8_TO_21 = "java8to21"
    SIMPLER_3_TO_4 = "simpler3to4"

class Suggestion(BaseModel):
    id: Optional[UUID] = None
    analyzer_id: str  # ID do analisador/análise
    file_path: str
    analyzer: AnalyzerEnum
    description: str
    start_line: int
    end_line: int
    original_snippet: str
    modified_code: str
    difficulty_level: int
    additional_notes: Optional[str] = None
    last: bool = False

class DynamoDBSuggestionReader:
    def __init__(self, table_name: str = 'CodeSuggestions', region: str = 'us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def get_suggestions_by_analysis(self, analysis_id: str) -> List[Suggestion]:
        """
        Recupera todas as sugestões de uma análise específica.
        
        Args:
            analysis_id: ID da análise (AnalysisId)
            
        Returns:
            Lista de objetos Suggestion
        """
        try:
            response = self.table.query(
                KeyConditionExpression='AnalysisId = :analysis_id',
                ExpressionAttributeValues={
                    ':analysis_id': analysis_id
                }
            )
            
            suggestions = []
            for item in response.get('Items', []):
                suggestion = self._item_to_suggestion(item)
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            print(f"Erro ao recuperar sugestões: {e}")
            return []
    
    def get_suggestion(self, analysis_id: str, suggestion_id: str) -> Optional[Suggestion]:
        """
        Recupera uma sugestão específica.
        
        Args:
            analysis_id: ID da análise (AnalysisId)
            suggestion_id: ID da sugestão (SuggestionId)
            
        Returns:
            Objeto Suggestion ou None se não encontrado
        """
        try:
            response = self.table.get_item(
                Key={
                    'AnalysisId': analysis_id,
                    'SuggestionId': suggestion_id
                }
            )
            
            item = response.get('Item')
            if item:
                return self._item_to_suggestion(item)
            
            return None
            
        except Exception as e:
            print(f"Erro ao recuperar sugestão: {e}")
            return None
    
    def _item_to_suggestion(self, item: dict) -> Suggestion:
        """
        Converte um item do DynamoDB para objeto Suggestion.
        
        Args:
            item: Item do DynamoDB
            
        Returns:
            Objeto Suggestion
        """
        return Suggestion(
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

# Exemplo de uso
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Para LocalStack
    if os.getenv('AWS_ENDPOINT_URL'):
        import boto3
        boto3.setup_default_session(
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        # Configurar endpoint para LocalStack
        dynamodb = boto3.resource('dynamodb', 
                                  endpoint_url=os.getenv('AWS_ENDPOINT_URL'),
                                  region_name='us-east-1')
    
    reader = DynamoDBSuggestionReader()
    
    # Exemplo: recuperar todas as sugestões de uma análise
    analysis_id = "exemplo-analysis-uuid"
    suggestions = reader.get_suggestions_by_analysis(analysis_id)
    
    print(f"Encontradas {len(suggestions)} sugestões para análise {analysis_id}")
    
    for suggestion in suggestions:
        print(f"- Sugestão: {suggestion.description}")
        print(f"  Arquivo: {suggestion.file_path}")
        print(f"  Linhas: {suggestion.start_line}-{suggestion.end_line}")
        print(f"  Dificuldade: {suggestion.difficulty_level}")
        print("-" * 50)