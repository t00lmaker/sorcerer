import boto3
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import Optional

app = FastAPI()

class AnalyzerEnum(str, Enum):
    JAVA8_TO_21 = "java8to21"
    SIMPLER_3_TO_4 = "simpler3to4"

class AnalyzeInput(BaseModel):
    id: Optional[UUID] = None
    repo: str
    analyzers: list[AnalyzerEnum]
    params: Optional[dict[str, str]] = None

sqs_client = boto3.client("sqs", region_name="us-east-1" )  # Substitua pela região correta
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "http://localhost:4566/000000000000/your-queue-name")

@app.post("/analyze")
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
    

@app.get("/analyze/{id}")
def get_analyze(id: str):
    try:
        
        return {"status": "Analysis completed", "id": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))