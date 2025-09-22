"""
Exemplo demonstrando como as descrições dos campos Pydantic são utilizadas pelo PydanticOutputParser.
Este script mostra as instruções de formato que são geradas e enviadas para o LLM.
"""
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import Optional, List
from uuid import UUID
from enum import Enum

class AnalyzerEnum(str, Enum):
    JAVA8_TO_21 = "java8to21"
    SIMPLER_3_TO_4 = "simpler3to4"

class Suggestion(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Identificador único da sugestão (será gerado automaticamente se não fornecido)")
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

def main():
    """Demonstra as instruções de formato geradas pelo PydanticOutputParser"""
    
    # Criar o parser
    parser = PydanticOutputParser(pydantic_object=SuggestionsList)
    
    # Obter as instruções de formato que serão enviadas para o LLM
    format_instructions = parser.get_format_instructions()
    
    print("=" * 80)
    print("INSTRUÇÕES DE FORMATO GERADAS PARA O LLM:")
    print("=" * 80)
    print(format_instructions)
    print("=" * 80)
    
    print("\nComo usar no prompt:")
    print("=" * 40)
    print(f"""
Analyze the following Java code and provide migration suggestions:

{{java_code}}

{format_instructions}
    """)

if __name__ == "__main__":
    main()