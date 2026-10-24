# Acadenic Platform

AI-powered Academic Qualifications Management Platform

## Overview

This project aims to modernize academic qualification management systems such as APELLA by providing:

- Academic profiles
- Publicationsmanagement
- Research projects
- Teaching activities
- Evaluation workflows
- ORCID integration
- OpenAlex integration
- AI-powered research analysis
- Natural language assistant

## Technology Stack

### Backend

- FastAPI
- SQLAlchemy
- Alembic

### Database

- PostgreSQL

### Frontend

- Next.js
- Tailwind CSS

### AI


- Hugging Face
- Google GEmini API
- Retrieval Augmented Generation (RAG)

## Development Roadmap

### Sprint 1 - Backend Foundation

- [x] PostgreSQL Setup
- [x] FastAPI Setup
- [x] SQLAlchemy Configuration
- [x] Alembic Setup
- [x] User Model
- [x] User Registartion Endpoint
- [x] JWT Authentication
- [x] Protected Endpoint (/users/me)

---

### Sprint 2 - Academic Institutions

- [x] Institution Model
- [x] Institutions API
- [x] Greek Universities Dataset
- [x] Institution Seeder
- [x] Department Model
- [x] Department API

---

### Sprint 3 - Academic CV & Research Portfolio

- [x] Academic Profile Model
- [x] Profile API
- [x] Degrees Module
- [x] Publications Module
- [x] Research Projects Module
- [x] Teaching Experience Module

## AI Benchmark

The benchmark currently uses a mock provider to verify prompt preparation,
evaluation and result storage. Mock scores do not represent real-model quality.

The default configuration contains 12 test types, 22 cases and 3 repetitions
per case, producing 66 runs.

### Running the benchmark

Run these commands from the `backend` directory with your Python virtual
environment activated.

```powershell
# Show available options
python ai_benchmark/benchmark.py --help

# Run the full mock benchmark
python ai_benchmark/benchmark.py

# Run Test 1 once for each configured candidate
python ai_benchmark/benchmark.py --provider mock --test test_01_extraction --runs 1

# Run Tests 1 and 2 once per configured candidate
python ai_benchmark/benchmark.py --provider mock --test test_01_extraction --test test_02_summary --runs 1
```

- `--provider`: selects the provider; currently only `mock` is implemented.
- `--test`: selects a test identifier. Repeat it to select multiple tests.
  If omitted, all configured tests run.
- `--runs`: sets repetitions per case and must be a positive integer.
  If omitted, the value from `test_config.json` is used.

### Results

Results are saved under `backend/ai_benchmark/results/`.
Generated results are excluded from Git.

Each result includes identifiers, the model response, execution details,
evaluation metrics, requested generation options and parsing diagnostics.
A shared batch ID groups results from the same benchmark execution.

Provider failures are recorded separately from answer-quality evaluation.

### AI

- Mock provider and shared benchmark infrastructure implemented.
- Planned provider integrations: Ollama, Hugging Face and Google Gemini API.
- Final application provider to be selected through comparative benchmarking.

## Author

Marios Lampousis