import boto3
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

import traceback


load_dotenv()

#print("Variáveis carregadas:", os.environ)

app = FastAPI()

class AnalyzerEnum(str, Enum):
    JAVA8_TO_21 = "java8to21"
    SIMPLER_3_TO_4 = "simpler3to4"

class AnalyzeInput(BaseModel):
    id: Optional[UUID] = None
    repo: str
    analyzers: list[AnalyzerEnum]
    params: Optional[dict[str, str]] = None

class Suggestion(BaseModel):
    id: Optional[UUID] = None
    analyzer_id: Optional[UUID] = None
    file_path: str
    description: str
    start_line: int
    end_line: int
    original_snippet: str
    modified_code: str
    difficulty_level: int
    last: bool = False
    analyzer: AnalyzerEnum
    additional_notes: Optional[str] = None

class SuggestionsListOutput(BaseModel):
    id: UUID
    completed: bool = False
    suggestions: List[Suggestion]

sqs_client = boto3.client("sqs", region_name="us-east-1" )  # Substitua pela região correta
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "http://localhost:4566/000000000000/your-queue-name")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CodeSuggestions')

@app.post("/analyze") # retornar 202 Accepted
def post_analyze(input_data: AnalyzeInput):
    try:
        message_body = input_data.model_dump_json()
        response = sqs_client.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=message_body
        )
        return {
            "message_id": response["MessageId"],
            "status": "Message sent to SQS successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/analyze/{analyze_id}", response_model=SuggestionsListOutput) # caso nao tenha analise 204 No Content, caso tenha mas ainda nao concluida 102 Processing.
def get_analyze(analyze_id: str):
    try:

        response = table.query(
            KeyConditionExpression=Key('AnalysisId').eq(analyze_id)
        )

        suggestions = [
            Suggestion(
                id=item['SuggestionId'],
                analyzer_id=item['AnalysisId'],
                file_path=item['FilePath'],
                analyzer=AnalyzerEnum(item['Analyzer']),
                description=item['Description'],
                start_line=int(item['StartLine']),
                end_line=int(item['EndLine']),
                original_snippet=item['OriginalSnippet'],
                modified_code=item['ModifiedCode'],
                difficulty_level=int(item['DifficultyLevel']),
                additional_notes=item.get('AdditionalNotes'),
                last= bool(item['Last']) if 'Last' in item else False
            )
            for item in response.get('Items', [])
        ]
    except Exception as e:
        error_trace = traceback.format_exc()
        print("Stack trace do erro:", error_trace)  
        raise HTTPException(status_code=500, detail=f"Erro ao processar itens: {str(e)}")
    
    if not suggestions:
        raise HTTPException(status_code=204, detail="No suggestions found for this analysis ID yet.")
    
    return SuggestionsListOutput(
        id=analyze_id,
        suggestions=suggestions,
        completed=any(suggestion.last for suggestion in suggestions)
    )
