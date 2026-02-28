# RAG Workflow Auditor (Beginner Edition)

An AI-assisted workflow auditing tool that compares operational steps against policy text and generates structured compliance feedback.

This project demonstrates how large language models can support analysts by identifying potential gaps between real workflows and written procedures.

## OpenAI API Requirement

The application interface runs immediately, but generating AI audit results requires an OpenAI API key with available credits.

If no credits are available, the app will display a message instead of results. This behavior is expected and handled gracefully.

## Quick Start

### 1) Set up Python
- Python 3.10+ recommended
- Create a virtual environment (optional but recommended)

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
## Screenshot

![Workflow Auditor UI](screenshot.png)


