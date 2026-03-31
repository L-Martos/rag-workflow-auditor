![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![AI](https://img.shields.io/badge/AI-OpenAI-green)

# AI Workflow Compliance Auditor

A Streamlit-based AI tool that reviews a workflow step and compares it against policy text to provide structured audit feedback.

## Live App
Add your deployed Streamlit link here once deployed.

## What This Tool Does

This application allows a user to:

- Enter a workflow step
- Paste policy, SOP, or checklist text
- Compare workflow activity against policy requirements
- Receive audit-style feedback with:
  - Verdict
  - Compliance issues
  - Suggested improvements
  - Policy-based citations

## Real-World Context

This project was inspired by real workflow auditing experience in revenue integrity operations, where processes must be reviewed against policies to identify compliance gaps, missed actions, and workflow risks.

The application demonstrates how AI can assist with structured audit reasoning in operational environments such as:

- Healthcare
- Revenue Integrity
- Revenue Cycle
- Fintech
- SaaS operations
- Compliance workflows

## App Preview

![App Screenshot](app_screenshot.png)

## Tech Stack

- Python
- Streamlit
- OpenAI API
- GitHub
- GitHub Codespaces

## How It Works

1. Enter a workflow step
2. Paste policy text
3. Click **Audit**
4. The app compares the workflow step against the policy
5. The tool returns a structured compliance review

## Run Locally

```bash
pip install -r requirements.txt
streamlit run ui_app.py
