# Java Migration Application

This project is designed to assist developers in modernizing Java code from version 8 to version 21. It utilizes LangChain to analyze Java code and suggest updates that leverage the latest features and best practices of the Java language.

## Project Structure

```
java-migration-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── langchain_agent.py     # Implementation of the LangChain agent
│   ├── models
│   │   └── suggestion.py      # Pydantic model for storing suggestions
│   ├── prompts
│   │   └── java_migration_prompt.txt # Prompt for analyzing Java code
│   └── utils
│       └── file_handler.py    # Utility functions for file operations
├── tests
│   ├── test_langchain_agent.py # Unit tests for the LangChain agent
│   └── test_suggestion_model.py # Unit tests for the Suggestion model
├── requirements.txt            # Project dependencies
├── .env                        # Environment variables
└── README.md                   # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd java-migration-app
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add any necessary configuration settings.

## Usage

To run the application, execute the following command:

```bash
python src/main.py
```

You will be prompted to enter a Java code string. The application will analyze the code and provide suggestions for modernization.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.