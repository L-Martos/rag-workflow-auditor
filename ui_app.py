import os
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Workflow Auditor", layout="wide")
st.title("Workflow Auditor (Beginner → Compare to Policy)")

# --- API KEY (Codespaces Secret) ---
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Missing OPENAI_API_KEY (Codespaces Secret). Add it in GitHub → Settings → Secrets and variables → Codespaces, then rebuild Codespace.")
    st.stop()

client = OpenAI(api_key=api_key)

col1, col2 = st.columns(2)

with col1:
    step = st.text_area(
        "Enter a workflow step",
        height=220,
        placeholder="e.g., Validate input; if valid, submit to API; handle errors; log result."
    )

with col2:
    policy = st.text_area(
        "Paste policy text (optional, but recommended)",
        height=220,
        placeholder="Paste any policy, SOP, or checklist text here."
    )

if st.button("Audit"):
    if not step.strip():
        st.warning("Please enter a workflow step.")
        st.stop()

    system_prompt = (
        "You are a careful auditor. If policy text is provided, you MUST read it and compare the step against it.\n\n"
        "Output EXACTLY 3 sections:\n"
        "1) Verdict (Compliant / Issues Found)\n"
        "2) Feedback (2-4 bullets)\n"
        "3) Citations (quote exact lines from the policy you used, or say 'No policy provided')."
    )

    user_content = f"WORKFLOW STEP:\n{step.strip()}\n\n"
    if policy.strip():
        user_content += f"POLICY TEXT:\n{policy.strip()}\n"

    try:
        with st.spinner("Auditing..."):
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
            )

        st.subheader("Audit Result")
        st.write(resp.choices[0].message.content)

    except Exception:
        # ONE clean message, no red traceback
        st.error("The app is running, but the OpenAI API request failed (usually because the API account has no credits/quota).")
        st.info("Fix later if you want live results: add OpenAI billing/credits or use a funded API key. The UI is still working.")
