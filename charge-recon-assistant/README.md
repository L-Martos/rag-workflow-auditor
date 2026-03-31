# Charge Recon Assistant

Charge Recon Assistant is a Streamlit application designed to help hospital departments and Revenue Integrity teams perform charge reconciliation by comparing activity/reconciliation exports against patient charge exports to identify missing charges and other reconciliation issues.

## Features
- Missing Charges detection
- Charge Without Activity
- Quantity Mismatch
- Duplicate Charges
- Implant / Supply Issues
- Cost Center Mismatch
- Late Charges
- Mapping Issues
- Provider Mismatch
- Exception Dashboard Summary
- Excel Exception Report Export

## How It Works
1. Upload Activity/Reconciliation file
2. Upload Patient Charges file
3. Upload optional Mapping file
4. App compares datasets and identifies reconciliation exceptions
5. Dashboard summarizes exception counts
6. Download Excel exception report

## Use Case
This tool is designed for:
- Charge Nurses
- Department Charge Entry Teams
- Revenue Integrity Analysts
- CDM Teams
- Revenue Cycle Managers
- Consultants
- Small Hospitals and Clinics

## Tech Stack
- Python
- Streamlit
- Pandas
- OpenPyXL
- GitHub

## Disclaimer
Do not upload PHI unless approved by your organization. Use de-identified data whenever possible.

## Screenshots

### Upload Page
![Upload](screenshots/upload.png)

### Results Dashboard
![Dashboard](screenshots/dashboard.png)
