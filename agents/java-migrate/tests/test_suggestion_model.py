from pydantic import BaseModel, Field

class Suggestion(BaseModel):
    file_path: str = Field(..., description="The path of the Java file being analyzed.")
    description: str = Field(..., description="A brief description of the suggested change.")
    start_line: int = Field(..., description="The starting line number of the code to be changed.")
    end_line: int = Field(..., description="The ending line number of the code to be changed.")
    original_snippet: str = Field(..., description="The original code snippet that is being suggested for change.")
    modified_code: str = Field(..., description="The modified code snippet after applying the suggestion.")
    difficulty_level: int = Field(..., description="The difficulty level of the suggested change, from 1 to 5.")
    additional_info: str = Field(None, description="Any additional information or context regarding the suggestion.")