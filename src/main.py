import os
from langchain_agent import LangChainAgent
from dotenv import load_dotenv
from prompts.java_migration_prompt import system_prompt


load_dotenv()

def main():
    agent = LangChainAgent(prompt_template=system_prompt)
    code_tests_dir = os.path.join(os.path.dirname(__file__), "code_tests")
    print("Diretório atual:", os.get_env("GEMINI_API_KEY"))
    for filename in os.listdir(code_tests_dir):
        if filename.endswith(".java"):
            file_path = os.path.join(code_tests_dir, filename)
            print(f"Analisando arquivo: {filename}")
            print("-" * 40)

            with open(file_path, "r") as file:
                java_code = file.read()

            try:
                suggestions_list = agent.generate_suggestions(java_code, file_path)
                for suggestion in suggestions_list.suggestions:
                    print(f"Descrição: {suggestion.description}")
                    print(f"Trecho original (linhas {suggestion.start_line}-{suggestion.end_line}):")
                    print(suggestion.original_snippet)
                    print("Código modificado:")
                    print(suggestion.modified_code)
                    print(f"Nível de dificuldade: {suggestion.difficulty_level}")
                    print("-" * 40)
            except Exception as e:
                print(f"Erro ao processar o arquivo {filename}: {e}")
                print("-" * 40)

if __name__ == "__main__":
    main()