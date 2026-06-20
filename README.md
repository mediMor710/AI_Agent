# NexusAI — Agent Conversationnel d'Intelligence Commerciale

> An AI-powered conversational agent for sales data analysis, document search, and automated PDF report generation — built with Amazon Bedrock and Claude 4.5 Haiku.

---

## Overview

NexusAI is a conversational AI agent that allows any user — regardless of technical background — to interact with sales data and internal company documents using natural language questions in English or French.

Instead of requiring SQL, Python, or Excel skills, users simply type a question and receive:
- A **text answer** with key figures
- An optional **chart** (bar, pie, trend, histogram)
- An optional **PDF report** filtered to their exact request

NexusAI is built on top of **Amazon Bedrock** using **Claude 4.5 Haiku** as the language model, and is available both as a **web interface** (Flask) and a **desktop application** (Electron).

---

## Features

| Feature | Description |
|---------|-------------|
| **Natural language analytics** | Ask any question about sales data — Claude writes the pandas code dynamically |
| **Document search (RAG)** | Answers about company policies pulled from real internal documents |
| **Filtered PDF reports** | Auto-generates reports filtered by category, region, year, segment, state, or ship mode |
| **Bilingual support** | Automatic detection and response in English or French |
| **Daily insight card** | A new suggested question every day to inspire data exploration |
| **Session memory** | Remembers the last 10 messages for follow-up questions |
| **Desktop app** | Electron wraps the web interface as a standalone desktop application |

---

## Architecture

NexusAI is organized into three layers:

```
┌─────────────────────────────────────────────┐
│         Layer 1 — Presentation              │
│         Flask Web Interface (index.html)    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Layer 2 — Orchestration             │
│  Language detection → Classification →      │
│  Routing (greeting / report / RAG / analytics)│
└────┬─────────────┬──────────────┬───────────┘
     │             │              │
┌────▼───┐   ┌─────▼────┐  ┌─────▼──────┐
│Analytics│   │   RAG    │  │   Report   │
│ Module  │   │  Module  │  │  Generator │
└────┬───┘   └─────┬────┘  └─────┬──────┘
     │             │              │
┌────▼─────────────▼──────────────▼──────────┐
│              Amazon Bedrock                  │
│     Claude 4.5 Haiku + Knowledge Base       │
└─────────────────────────────────────────────┘
```

### How a request flows

1. User types a question in the chat interface
2. Flask validates and receives the request
3. The orchestrator detects the language (EN/FR)
4. It checks in order: greeting → report request → classify (analytics or RAG)
5. The right module is called and produces a result
6. The response is returned as a consistent JSON object: `text + chart + report_url`
7. The interface displays the answer

---

## Tech Stack

| Role | Technology |
|------|-----------|
| Web framework | Flask 3.0 |
| AI model | Claude 4.5 Haiku (Amazon Bedrock) |
| Document search | Amazon Bedrock Knowledge Base |
| Document storage | Amazon S3 |
| Data analysis | Python · pandas · NumPy |
| Chart generation | Matplotlib |
| PDF generation | ReportLab |
| Desktop wrapper | Electron (Node.js) |
| Environment config | python-dotenv |

---

## Project Structure

```
nexusai/
├── app.py                  ← Flask entry point — routes, validation, rate limiting
├── orchestrator.py         ← Routes questions to the right module
├── bedrock_client.py       ← Language detection, classification, RAG answers
├── code_executor.py        ← Dynamic code generation and sandboxed execution
├── security.py             ← Security guard — scans generated code before running
├── report_generator.py     ← PDF report builder with filter support
├── data_loader.py          ← Loads Sales_Data.csv once at startup (singleton)
├── daily_question.py       ← Daily insight card questions (EN + FR)
├── config.py               ← All settings loaded from .env
├── requirements.txt        ← Python dependencies
├── .env                    ← Secret keys — never commit this file!
├── .gitignore
├── main.js                 ← Electron desktop wrapper
├── package.json            ← Node.js / Electron config
├── KnowledgeBase/
│   ├── Sales_Data.csv                          ← Main sales dataset
│   ├── FAQs.csv                                ← Company policy Q&A pairs
│   └── Bitext_Sample_Customer_Support_...csv   ← 27k support conversations
├── static/
│   ├── charts/             ← Generated chart images (auto-cleaned after 24h)
│   └── reports/            ← Generated PDF reports (auto-cleaned after 48h)
└── templates/
    └── index.html          ← Browser UI — chat, sidebars, JavaScript
```

---

## Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher (only for the Electron desktop app)
- **AWS account** with access to Amazon Bedrock
- **Amazon Bedrock model access** enabled for Claude 4.5 Haiku
- **Amazon S3 bucket** with your knowledge base documents uploaded
- **Amazon Bedrock Knowledge Base** created and synced

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/mediMor710/AI_Agent.git
cd AI_Agent
```

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Install Node.js dependencies (optional — desktop app only)

```bash
npm install
```

---

## Configuration

### Step 1 — Create your `.env` file

Create a file named `.env` in the project root:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
KNOWLEDGE_BASE_ID=your_knowledge_base_id_here
BEDROCK_MODEL_ID='YOUR_BEDROCK_MODEL_ID_HERE'
```

### Step 2 — Place your data files

```
KnowledgeBase/
├── Sales_Data.csv
├── FAQs.csv
└── Bitext_Sample_Customer_Support_Training_Dataset_27k_responses.csv
```

### Step 3 — Set up AWS (if starting from scratch)

1. **IAM User** — Create a user with `AmazonBedrockFullAccess` and `AmazonS3FullAccess` policies. Generate access keys.
2. **Model access** — In Amazon Bedrock console, enable access to `Claude 4.5 Haiku` (`anthropic.claude-4-5-haiku-20241022-v1:0`).
3. **S3 Bucket** — Create a bucket, upload your `FAQs.csv` and Bitext CSV into a `documents/` folder.
4. **Knowledge Base** — Create a Knowledge Base pointing to your S3 bucket. Use `Titan Embeddings G1` as the embedding model. After creation, click **Sync** and wait for status **Available**.
5. Copy the **Knowledge Base ID** into your `.env` file.

---

## Running the App

### As a web application

```bash
python app.py
```

Then open your browser at:
```
http://127.0.0.1:5000
```

### As a desktop application (Electron)

```bash
npm start
```

Electron will automatically start the Flask server and open the application window.

---

## Usage Examples

### Analytics questions
```
"Show the top 10 products by sales"
"What is the total revenue by region?"
"Compare profit between 2019 and 2021"
"Plot the monthly sales trend"
"Show a sales distribution histogram"
"Which products are sold at a loss?"
```

### Document / policy questions
```
"What is your return policy?"
"How do I cancel an order?"
"What payment methods do you accept?"
"How long does shipping take?"
"What should I do if my package is lost?"
```

### Report generation
```
"Generate a full sales report"
"Generate a report for the Technology category"
"Generate a profit report for the West region in 2021"
"Generate a report for the Consumer segment"
"Create a report for California in 2020"
```

### Greetings
```
"Hello"
"Bonjour"
"What can you do?"
```

---

## Dataset

NexusAI uses the **Sample Superstore** dataset — one of the most widely used datasets in data science, originally from Tableau.

| Property | Value |
|----------|-------|
| Rows | ~9,994 |
| Columns | 21 |
| Coverage | United States only |
| Years | 2016 – 2021 |
| Categories | Furniture · Office Supplies · Technology |
| Regions | Central · East · South · West |
| Segments | Consumer · Corporate · Home Office |

Key numeric columns: `sales`, `profit`, `discount`, `quantity`

---

## Knowledge Base

The RAG (Retrieval-Augmented Generation) system uses two document sources:

| File | Content |
|------|---------|
| `FAQs.csv` | ~100 Q&A pairs covering returns, payments, shipping, accounts, warranties |
| `Bitext_Sample_...csv` | 27,000 real customer support conversations covering cancellations, refunds, complaints, invoices, delivery |

These documents are indexed in Amazon Bedrock's Knowledge Base as a vector database. When a policy question arrives, Bedrock retrieves the 5 most relevant chunks and passes them to Claude to generate a grounded answer.

---

## Security

NexusAI includes a dedicated `security.py` module that scans all AI-generated code **before execution**. The following patterns are blocked:

| Pattern | Reason |
|---------|--------|
| `os.remove`, `os.rmdir`, `os.system` | File deletion and shell execution |
| `shutil.rmtree`, `shutil.move` | File system manipulation |
| `open(..., "w")` or `open(..., "a")` | Writing to files |
| `subprocess` | Running external shell commands |
| `eval()`, `compile()` | Dynamic code execution |
| `__import__()` | Sneaky library imports |
| `requests`, `urllib`, `socket` | Network access |

Generated code also runs inside a **sandboxed namespace** — it can only access the DataFrame, math libraries, and the chart-saving function. It has no access to the rest of the application or the file system.

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| In-memory sessions | Conversation history is lost if the server restarts |
| No authentication | Single-user design — no login system |
| AWS API costs | Every Claude call has a cost — manage usage for large-scale deployment |
| Report filter matching | Filters rely on exact value matching from the dataset — typos will not match |
| No automated tests | No unit or integration test suite currently |

---

## Future Improvements

- Persistent session storage with Redis or a database
- User authentication and multi-user support
- Support for additional data formats (Excel, SQL databases)
- Distribution and correlation charts in generated reports
- Dockerization for easier deployment
- Automated test suite

---

## Authors

Developed as a **Projet de Fin d'Études (PFE)** in the field of Data Engineering / Artificial Intelligence.

---

## License

This project was developed for academic purposes.
