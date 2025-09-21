from pydantic import BaseModel
from typing import List, Optional

class Suggestion(BaseModel):
    file_path: str
    description: str
    start_line: int
    end_line: int
    original_snippet: str
    modified_code: str
    difficulty_level: int
    additional_notes: Optional[str] = None  # Campo opcional para informações extras

class SuggestionsList(BaseModel):
    suggestions: List[Suggestion]