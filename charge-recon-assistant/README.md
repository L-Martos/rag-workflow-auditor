# Charge Recon Assistant

Charge Recon Assistant is a Streamlit app for healthcare charge reconciliation teams. It compares an Activity / Reconciliation export against a Patient Charges export, optionally uses a CPT mapping file, and highlights reconciliation exceptions such as missing charges, quantity mismatches, duplicate charges, provider mismatches, late charges, and mapping issues.

The tool is system-agnostic by design. It works from exported `.csv` or `.xlsx` files and does not depend on Epic, Cerner, Banner, FinThrive, MS4, or any other single vendor platform.

## Safety and Data Handling

- Do not upload PHI unless your organization has approved this use.
- The app is intended for exported files and de-identified or sample data.
- Uploaded files are processed in-session only.
- The app does not persist uploaded data.

## Version 1 Features

- Upload Activity / Reconciliation, Patient Charges, and optional Mapping files
- Map source columns to required reconciliation fields
- Run flexible record matching based on account, date, CPT/HCPCS, and optional identifiers
- Review exception results in tabbed tables with plain-language explanations and suggested next steps
- See validation notes that call out missing match keys, duplicate mapping rows, and non-numeric quantities
- Download an Excel exception report with separate sheets

## Files Supported

- Activity / Reconciliation file: required
- Patient Charges file: required
- Mapping file: optional
- Accepted file types: `.csv`, `.xlsx`

## Setup

1. Create and activate a virtual environment if you want one.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the Streamlit app:

```bash
streamlit run app.py
```

4. Open the local URL shown in the terminal.

## Project Files

- `/Users/leoviemartos/Documents/VS project Folder/python_practice/CDM/app.py` - main Streamlit application
- `/Users/leoviemartos/Documents/VS project Folder/python_practice/CDM/requirements.txt` - Python dependencies
- `/Users/leoviemartos/Documents/VS project Folder/python_practice/CDM/cdm_validator.py` - existing CDM validation script kept in the workspace

## Notes

- If the mapping file is not uploaded, the app still runs checks that do not depend on mapping data.
- Column names do not need to match exactly because users map them in the UI before reconciliation runs.
- The code is organized into reusable functions and result objects so later versions can add charts, revenue impact logic, and expanded matching rules more easily.
