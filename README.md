# Workflow Auditor (AI Workflow Review Tool)

A simple AI-powered web app that compares a workflow step against policy text and produces structured audit feedback.

This project demonstrates how AI can assist analysts by reviewing procedures, identifying potential compliance gaps, and generating clear explanations.

---

## What This Project Does

Input:
- A workflow step
- Optional policy or SOP text

Output:
- Compliance verdict
- Feedback suggestions
- Policy-based reasoning

The goal is to show how AI can support real-world review and auditing workflows.

---

## Tech Stack

- Python
- Streamlit
- OpenAI API
- GitHub Codespaces

---

## Run in GitHub Codespaces (Easiest Way)

1. Open this repository
2. Click **Code → Codespaces → Create Codespace**
3. In the terminal run:

```bash
pip install -r requirements.txt
python -m streamlit run ui_app.py --server.address 0.0.0.0 --server.port 8501
