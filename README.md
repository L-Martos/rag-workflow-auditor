![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![AI](https://img.shields.io/badge/AI-OpenAI-green)

# AI Workflow Compliance Auditor

A simple AI tool that reviews a workflow step and compares it against policy text to provide quick audit feedback.

## Real-World Context

This project was inspired by real workflow auditing experience in revenue integrity operations, where processes must be reviewed against policies to identify compliance gaps and missed actions.

The application demonstrates how AI can assist with structured audit reasoning — a common challenge across healthcare, fintech, and SaaS operational environments.


This project demonstrates building and running a small AI application using Python, Streamlit, and the OpenAI API.

---

## App Preview

![App Screenshot](app_screenshot.png)

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
3. Wait for environment to load
4. In the terminal run:

```bash
pip install -r requirements.txt
python -m streamlit run ui_app.py --server.address 0.0.0.0 --server.port 8501
