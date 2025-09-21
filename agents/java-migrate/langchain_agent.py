from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from models.suggestion import SuggestionsList

class Suggestion(BaseModel):
    file_path: str
    description: str
    start_line: int
    end_line: int
    original_snippet: str
    modified_code: str
    difficulty_level: int

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