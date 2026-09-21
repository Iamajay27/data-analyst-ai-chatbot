# 📊 Data Analyst AI Chatbot

A portfolio-ready Streamlit application that lets users upload CSV/Excel data, explore it, run safe read-only SQL, and — when an LLM API key is configured — ask natural-language questions that are converted into validated SQLite queries.

## Features

- CSV, XLSX and XLS upload
- Automatic data cleaning on a working copy
- Data profiling and quality metrics
- SQLite database integration
- Read-only SQL validator
- Natural-language-to-SQL chatbot
- AI explanation of query results
- Interactive Plotly charts
- Dataset explorer and schema viewer
- SQL explorer
- Basic automated insights
- Pytest test suite

## Tech Stack

Python, Pandas, NumPy, SQLite, Streamlit, Plotly, OpenAI API, pytest.

## Project Structure

```text
data-analyst-ai-chatbot/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
├── database/
├── src/
│   ├── data_loader.py
│   ├── data_cleaner.py
│   ├── data_profiler.py
│   ├── database.py
│   ├── sql_validator.py
│   ├── query_executor.py
│   ├── visualization.py
│   ├── insights.py
│   ├── llm_client.py
│   └── chatbot.py
├── utils/
└── tests/
```

## Run in VS Code

### 1. Open the folder

Open `data-analyst-ai-chatbot` in VS Code.

### 2. Create virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the AI key

Copy `.env.example` to `.env`:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

The app still supports upload, dashboards, data exploration, and manual SQL without the key.

### 5. Run the application

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

## Run Tests

```bash
pytest -q
```

## Security

The app validates generated SQL and permits only a single read-only SELECT/CTE query. Destructive operations such as `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, and `CREATE` are blocked.

API keys are loaded from `.env`; `.env` is ignored by Git.

## Example Questions

- What is the total sales?
- Which category has the highest revenue?
- Show sales by city.
- What is the average profit?
- What are the top 10 products by sales?
- Show monthly revenue.

## Resume Bullets

**Data Analyst AI Chatbot — Python, Pandas, SQL, LLM, Streamlit, Plotly**

- Built an AI-powered analytics application that lets users upload CSV/Excel datasets and query them using natural language.
- Integrated Pandas and SQLite with validated read-only LLM-generated SQL for safer automated analysis.
- Developed interactive data profiling, SQL exploration, Plotly visualizations, and AI-generated result explanations in Streamlit.

## LinkedIn Project Description

Built a Data Analyst AI Chatbot that combines Python, Pandas, SQLite, Streamlit, Plotly and an LLM. The app accepts CSV/Excel files, profiles and cleans the data, converts natural-language questions into validated read-only SQL, executes the query, and returns clear results and visualizations.

This project helped me practice data cleaning, SQL, prompt design, safe query execution, visualization, and deployment-ready Streamlit development.

## Future Improvements

- Support multiple uploaded tables and joins
- Add local/open-source LLM provider support
- Add downloadable reports
- Add richer anomaly detection
- Add chart export
- Add schema-aware conversation memory
