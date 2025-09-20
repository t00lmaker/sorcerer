from typing import List
import os

def read_java_file(file_path: str) -> str:
    """Reads the content of a Java file."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        return file.read()

def save_suggestions_to_file(suggestions: List[dict], output_path: str) -> None:
    """Saves the modernization suggestions to a specified output file."""
    with open(output_path, 'w') as file:
        for suggestion in suggestions:
            file.write(f"File Path: {suggestion['file_path']}\n")
            file.write(f"Description: {suggestion['description']}\n")
            file.write(f"Start Line: {suggestion['start_line']}\n")
            file.write(f"End Line: {suggestion['end_line']}\n")
            file.write(f"Original Snippet:\n{suggestion['original_snippet']}\n")
            file.write(f"Modified Code:\n{suggestion['modified_code']}\n")
            file.write(f"Difficulty Level: {suggestion['difficulty_level']}\n")
            file.write("\n" + "="*40 + "\n\n")