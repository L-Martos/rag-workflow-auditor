from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Charge Recon Assistant", layout="wide")


ACTIVITY_FIELDS = [
    "Account",
    "Encounter",
    "Service Date",
    "Case Number",
    "Department",
    "CPT/HCPCS",
    "Implant Item",
    "Quantity",
    "Provider",
]

CHARGE_FIELDS = [
    "Account",
    "Encounter",
    "Charge Date",
    "Department",
    "CPT/HCPCS",
    "Revenue Code",
    "Quantity",
    "Charge Amount",
    "Provider",
]

MAPPING_FIELDS = [
    "CPT/HCPCS",
    "Expected Department",
    "Revenue Code",
    "Implant Flag",
    "Supply Flag",
]

EXCEPTION_COLUMNS = [
    "Exception Type",
    "Why This Was Flagged",
    "Suggested Review Step",
    "Account",
    "Encounter",
    "Service Date",
    "Charge Date",
    "Case Number",
    "Department",
    "Expected Department",
    "CPT/HCPCS",
    "Implant Item",
    "Quantity Activity",
    "Quantity Charge",
    "Charge Amount",
    "Provider Activity",
    "Provider Charge",
    "Revenue Code",
    "Expected Revenue Code",
    "Days Late",
    "Matched On",
]

REVIEW_STEPS = {
    "Missing Charge": "Review charge entry or patient charge detail.",
    "Charge Without Activity": "Verify the source activity or documentation.",
    "Quantity Mismatch": "Verify the quantity entered in the charging workflow.",
    "Duplicate Charge": "Review for duplicate CPT/HCPCS posting.",
    "Missing Implant": "Review the implant log against posted charges.",
    "Missing Supply": "Review supply usage against posted charges.",
    "Cost Center Mismatch": "Verify the department or cost center mapping.",
    "Late Charge": "Review the delay between service and charge posting.",
    "CPT Mapping Issue": "Verify the CPT/HCPCS mapping table.",
    "Revenue Code Issue": "Verify the mapped revenue code.",
    "Provider Mismatch": "Verify the performing or billing provider.",
}

EXCEPTION_EXPLANATIONS = {
    "Missing Charge": "An activity record did not have a matching patient charge.",
    "Charge Without Activity": "A patient charge did not have a matching activity record.",
    "Quantity Mismatch": "A matched activity and charge record have different quantities.",
    "Duplicate Charge": "More than one charge was found for the same account, date, and CPT/HCPCS.",
    "Missing Implant": "The activity indicates an implant item, but no related implant charge was found.",
    "Missing Supply": "The mapping indicates a supply-related item, but no related supply charge was found.",
    "Cost Center Mismatch": "The charge department does not match the expected department in the mapping file.",
    "Late Charge": "The charge posted after the service date.",
    "CPT Mapping Issue": "The CPT/HCPCS code was not found in the mapping file.",
    "Revenue Code Issue": "The posted revenue code does not match the mapping file.",
    "Provider Mismatch": "The provider on the charge does not match the activity record.",
}

RESULT_TAB_ORDER = [
    ("Summary", "summary"),
    ("Missing Charges", "missing_charges"),
    ("Charge Without Activity", "charge_without_activity"),
    ("Quantity Mismatch", "quantity_mismatch"),
    ("Duplicate Charges", "duplicate_charges"),
    ("Implant / Supply Issues", "implant_supply_issues"),
    ("Cost Center Mismatch", "cost_center_mismatch"),
    ("Late Charges", "late_charges"),
    ("Mapping Issues", "mapping_issues"),
    ("Provider Mismatch", "provider_mismatch"),
    ("All Exceptions", "all_exceptions"),
]

SHEET_NAMES = {
    "missing_charges": "Missing Charges",
    "charge_without_activity": "Charge Without Activity",
    "quantity_mismatch": "Quantity Mismatch",
    "duplicate_charges": "Duplicate Charges",
    "implant_supply_issues": "Implant Supply Issues",
    "cost_center_mismatch": "Cost Center Mismatch",
    "late_charges": "Late Charges",
    "mapping_issues": "Mapping Issues",
    "provider_mismatch": "Provider Mismatch",
    "all_exceptions": "All Exceptions",
}


@dataclass
class ValidationMessage:
    level: str
    text: str


@dataclass
class ReconOutputs:
    summary: pd.DataFrame
    validation_notes: pd.DataFrame
    results: Dict[str, pd.DataFrame]


def load_file(uploaded_file) -> pd.DataFrame:
    suffix = uploaded_file.name.lower()
    if suffix.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if suffix.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")
    raise ValueError("Unsupported file type. Please upload a CSV or XLSX file.")


def normalize_text(value) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper()


def parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.normalize()


def parse_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def normalize_flag(value) -> bool:
    text = normalize_text(value)
    return bool(text in {"Y", "YES", "TRUE", "1", "T"})


def safe_date_str(value) -> Optional[str]:
    if pd.isna(value) or value is None:
        return None
    return pd.Timestamp(value).date().isoformat()


def choose_default_column(columns: List[str], target_field: str) -> int:
    normalized_target = normalize_text(target_field)
    for idx, column in enumerate(columns, start=1):
        if normalize_text(column) == normalized_target:
            return idx
    return 0


def build_mapping_ui(df: pd.DataFrame, fields: List[str], section_key: str) -> Dict[str, Optional[str]]:
    options = ["-- Not available --"] + list(df.columns)
    mapping: Dict[str, Optional[str]] = {}
    for field in fields:
        selected = st.selectbox(
            field,
            options=options,
            index=choose_default_column(list(df.columns), field),
            key=f"{section_key}_{field}",
        )
        mapping[field] = None if selected == "-- Not available --" else selected
    return mapping


def validate_mapping_configuration(
    activity_map: Dict[str, Optional[str]],
    charge_map: Dict[str, Optional[str]],
    mapping_map: Optional[Dict[str, Optional[str]]],
    activity_raw: pd.DataFrame,
    charge_raw: pd.DataFrame,
    mapping_raw: Optional[pd.DataFrame],
) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []

    required_activity = ["Account", "Service Date", "CPT/HCPCS", "Quantity"]
    required_charge = ["Account", "Charge Date", "CPT/HCPCS", "Quantity"]

    missing_activity = [field for field in required_activity if not activity_map.get(field)]
    missing_charge = [field for field in required_charge if not charge_map.get(field)]

    if missing_activity:
        messages.append(
            ValidationMessage("error", f"Activity file is missing required mappings for: {', '.join(missing_activity)}.")
        )
    if missing_charge:
        messages.append(
            ValidationMessage("error", f"Patient Charges file is missing required mappings for: {', '.join(missing_charge)}.")
        )

    for label, selected_map in [
        ("Activity", activity_map),
        ("Patient Charges", charge_map),
        ("Mapping", mapping_map or {}),
    ]:
        used_columns = [column for column in selected_map.values() if column]
        duplicates = sorted({column for column in used_columns if used_columns.count(column) > 1})
        if duplicates:
            messages.append(
                ValidationMessage(
                    "warning",
                    f"{label} mapping uses the same source column more than once: {', '.join(duplicates)}. Confirm that this is intentional.",
                )
            )

    if activity_raw.empty:
        messages.append(ValidationMessage("error", "The Activity / Reconciliation file has no rows."))
    if charge_raw.empty:
        messages.append(ValidationMessage("error", "The Patient Charges file has no rows."))
    if mapping_raw is not None and mapping_raw.empty:
        messages.append(ValidationMessage("warning", "The Mapping file is empty, so mapping-based checks will be skipped."))

    if mapping_raw is not None and mapping_map and not mapping_map.get("CPT/HCPCS"):
        messages.append(ValidationMessage("warning", "Mapping file was uploaded without a CPT/HCPCS mapping, so mapping-based checks will be skipped."))
    if mapping_raw is None:
        messages.append(ValidationMessage("info", "No Mapping file was uploaded. Mapping-based checks will be skipped, but core reconciliation will still run."))

    return messages


def standardize_dataframe(df: pd.DataFrame, mapping: Dict[str, Optional[str]], dataset_type: str) -> pd.DataFrame:
    standardized = pd.DataFrame(index=df.index)
    for target_field, source_column in mapping.items():
        standardized[target_field] = df[source_column] if source_column else pd.NA

    text_fields = [
        "Account",
        "Encounter",
        "Case Number",
        "Department",
        "CPT/HCPCS",
        "Implant Item",
        "Provider",
        "Revenue Code",
        "Expected Department",
    ]
    for column in text_fields:
        if column in standardized.columns:
            standardized[column] = standardized[column].apply(normalize_text)

    if "Service Date" in standardized.columns:
        standardized["Service Date"] = parse_date(standardized["Service Date"])
    if "Charge Date" in standardized.columns:
        standardized["Charge Date"] = parse_date(standardized["Charge Date"])
    if "Quantity" in standardized.columns:
        standardized["Quantity"] = parse_numeric(standardized["Quantity"])
    if "Charge Amount" in standardized.columns:
        standardized["Charge Amount"] = parse_numeric(standardized["Charge Amount"])
    if dataset_type == "mapping":
        standardized["Implant Flag"] = standardized["Implant Flag"].apply(normalize_flag)
        standardized["Supply Flag"] = standardized["Supply Flag"].apply(normalize_flag)

    standardized = standardized.reset_index(drop=True).copy()
    standardized["row_id"] = standardized.index
    return standardized


def dataset_quality_notes(activity_df: pd.DataFrame, charge_df: pd.DataFrame, mapping_df: Optional[pd.DataFrame]) -> List[ValidationMessage]:
    notes: List[ValidationMessage] = []

    activity_missing_keys = int(
        activity_df[["Account", "Service Date", "CPT/HCPCS"]].isna().any(axis=1).sum()
    )
    charge_missing_keys = int(
        charge_df[["Account", "Charge Date", "CPT/HCPCS"]].isna().any(axis=1).sum()
    )
    activity_bad_qty = int(activity_df["Quantity"].isna().sum())
    charge_bad_qty = int(charge_df["Quantity"].isna().sum())

    if activity_missing_keys:
        notes.append(
            ValidationMessage(
                "warning",
                f"Activity file contains {activity_missing_keys} missing match-key values across Account, Service Date, or CPT/HCPCS. Some rows may show as exceptions because they could not be matched reliably.",
            )
        )
    if charge_missing_keys:
        notes.append(
            ValidationMessage(
                "warning",
                f"Patient Charges file contains {charge_missing_keys} missing match-key values across Account, Charge Date, or CPT/HCPCS. Some rows may show as exceptions because they could not be matched reliably.",
            )
        )
    if activity_bad_qty:
        notes.append(
            ValidationMessage(
                "info",
                f"Activity file contains {activity_bad_qty} rows with blank or non-numeric quantity values.",
            )
        )
    if charge_bad_qty:
        notes.append(
            ValidationMessage(
                "info",
                f"Patient Charges file contains {charge_bad_qty} rows with blank or non-numeric quantity values.",
            )
        )

    if mapping_df is not None and not mapping_df.empty:
        duplicate_codes = mapping_df["CPT/HCPCS"].dropna().duplicated(keep=False)
        duplicate_count = int(duplicate_codes.sum())
        if duplicate_count:
            notes.append(
                ValidationMessage(
                    "warning",
                    f"Mapping file contains {duplicate_count} rows with duplicate CPT/HCPCS values. The first row for each duplicated code will be used.",
                )
            )

    return notes


def prepare_mapping_lookup(mapping_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    if mapping_df is None or mapping_df.empty or "CPT/HCPCS" not in mapping_df.columns:
        return None
    lookup = mapping_df.dropna(subset=["CPT/HCPCS"]).drop_duplicates(subset=["CPT/HCPCS"], keep="first").copy()
    return lookup.set_index("CPT/HCPCS", drop=False)


def build_primary_key(row: pd.Series, date_field: str) -> Tuple[Optional[str], Optional[pd.Timestamp], Optional[str]]:
    return row.get("Account"), row.get(date_field), row.get("CPT/HCPCS")


def build_fallback_key(row: pd.Series) -> Tuple[Optional[str], Optional[str]]:
    return row.get("Account"), row.get("CPT/HCPCS")


def score_candidate_match(activity_row: pd.Series, charge_row: pd.Series) -> Tuple[int, str]:
    score = 0
    matched_on: List[str] = ["Account", "CPT/HCPCS"]

    service_date = activity_row.get("Service Date")
    charge_date = charge_row.get("Charge Date")
    if pd.notna(service_date) and pd.notna(charge_date):
        date_gap = abs(int((charge_date - service_date).days))
        score += max(0, 3 - min(date_gap, 3))
        matched_on.append("Date")

    if activity_row.get("Case Number") and charge_row.get("Case Number") and activity_row["Case Number"] == charge_row["Case Number"]:
        score += 5
        matched_on.append("Case Number")
    if activity_row.get("Encounter") and charge_row.get("Encounter") and activity_row["Encounter"] == charge_row["Encounter"]:
        score += 4
        matched_on.append("Encounter")
    if activity_row.get("Department") and charge_row.get("Department") and activity_row["Department"] == charge_row["Department"]:
        score += 2
        matched_on.append("Department")
    if activity_row.get("Provider") and charge_row.get("Provider") and activity_row["Provider"] == charge_row["Provider"]:
        score += 2
        matched_on.append("Provider")
    if pd.notna(activity_row.get("Quantity")) and pd.notna(charge_row.get("Quantity")) and activity_row["Quantity"] == charge_row["Quantity"]:
        score += 1
        matched_on.append("Quantity")

    return score, ", ".join(matched_on)


def match_records(activity_df: pd.DataFrame, charge_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    activity_lookup: Dict[Tuple[Optional[str], Optional[pd.Timestamp], Optional[str]], List[int]] = {}
    charge_lookup: Dict[Tuple[Optional[str], Optional[pd.Timestamp], Optional[str]], List[int]] = {}

    for _, row in activity_df.iterrows():
        key = build_primary_key(row, "Service Date")
        if all(key):
            activity_lookup.setdefault(key, []).append(int(row["row_id"]))

    for _, row in charge_df.iterrows():
        key = build_primary_key(row, "Charge Date")
        if all(key):
            charge_lookup.setdefault(key, []).append(int(row["row_id"]))

    activity_by_id = activity_df.set_index("row_id")
    charge_by_id = charge_df.set_index("row_id")
    matched_pairs: List[Dict[str, object]] = []
    used_activity_ids = set()
    used_charge_ids = set()

    def assign_candidates(candidate_pairs: List[Tuple[int, str, int, int]]) -> None:
        for _, matched_on, activity_id, charge_id in sorted(candidate_pairs, key=lambda item: (-item[0], item[2], item[3])):
            if activity_id in used_activity_ids or charge_id in used_charge_ids:
                continue
            used_activity_ids.add(activity_id)
            used_charge_ids.add(charge_id)
            matched_pairs.append(
                {
                    "activity_row_id": activity_id,
                    "charge_row_id": charge_id,
                    "Matched On": matched_on,
                }
            )

    for key in sorted(set(activity_lookup).intersection(set(charge_lookup))):
        exact_date_candidates: List[Tuple[int, str, int, int]] = []
        for activity_id in activity_lookup[key]:
            if activity_id in used_activity_ids:
                continue
            for charge_id in charge_lookup[key]:
                if charge_id in used_charge_ids:
                    continue
                score, matched_on = score_candidate_match(activity_by_id.loc[activity_id], charge_by_id.loc[charge_id])
                exact_date_candidates.append((score + 10, matched_on, activity_id, charge_id))
        assign_candidates(exact_date_candidates)

    fallback_activity_lookup: Dict[Tuple[Optional[str], Optional[str]], List[int]] = {}
    fallback_charge_lookup: Dict[Tuple[Optional[str], Optional[str]], List[int]] = {}

    for _, row in activity_df[~activity_df["row_id"].isin(used_activity_ids)].iterrows():
        key = build_fallback_key(row)
        if all(key):
            fallback_activity_lookup.setdefault(key, []).append(int(row["row_id"]))

    for _, row in charge_df[~charge_df["row_id"].isin(used_charge_ids)].iterrows():
        key = build_fallback_key(row)
        if all(key):
            fallback_charge_lookup.setdefault(key, []).append(int(row["row_id"]))

    for key in sorted(set(fallback_activity_lookup).intersection(set(fallback_charge_lookup))):
        fallback_candidates: List[Tuple[int, str, int, int]] = []
        for activity_id in fallback_activity_lookup[key]:
            for charge_id in fallback_charge_lookup[key]:
                activity_row = activity_by_id.loc[activity_id]
                charge_row = charge_by_id.loc[charge_id]
                score, matched_on = score_candidate_match(activity_row, charge_row)
                service_date = activity_row.get("Service Date")
                charge_date = charge_row.get("Charge Date")
                if pd.notna(service_date) and pd.notna(charge_date) and charge_date < service_date:
                    score -= 2
                fallback_candidates.append((score, f"{matched_on}, Late Match Candidate", activity_id, charge_id))
        assign_candidates(fallback_candidates)

    matched_df = pd.DataFrame(matched_pairs)
    unmatched_activity = activity_df[~activity_df["row_id"].isin(used_activity_ids)].copy()
    unmatched_charge = charge_df[~charge_df["row_id"].isin(used_charge_ids)].copy()
    return matched_df, unmatched_activity, unmatched_charge


def activity_charge_context(
    activity_row: Optional[pd.Series] = None,
    charge_row: Optional[pd.Series] = None,
    *,
    expected_department: Optional[str] = None,
    expected_revenue_code: Optional[str] = None,
    matched_on: Optional[str] = None,
    days_late: Optional[int] = None,
) -> Dict[str, Optional[object]]:
    account = activity_row.get("Account") if activity_row is not None else None
    if not account and charge_row is not None:
        account = charge_row.get("Account")

    encounter = activity_row.get("Encounter") if activity_row is not None else None
    if not encounter and charge_row is not None:
        encounter = charge_row.get("Encounter")

    department = activity_row.get("Department") if activity_row is not None else None
    if not department and charge_row is not None:
        department = charge_row.get("Department")

    cpt_code = activity_row.get("CPT/HCPCS") if activity_row is not None else None
    if not cpt_code and charge_row is not None:
        cpt_code = charge_row.get("CPT/HCPCS")

    return {
        "Account": account,
        "Encounter": encounter,
        "Service Date": safe_date_str(activity_row.get("Service Date")) if activity_row is not None else None,
        "Charge Date": safe_date_str(charge_row.get("Charge Date")) if charge_row is not None else None,
        "Case Number": activity_row.get("Case Number") if activity_row is not None else None,
        "Department": department,
        "Expected Department": expected_department,
        "CPT/HCPCS": cpt_code,
        "Implant Item": activity_row.get("Implant Item") if activity_row is not None else None,
        "Quantity Activity": activity_row.get("Quantity") if activity_row is not None else None,
        "Quantity Charge": charge_row.get("Quantity") if charge_row is not None else None,
        "Charge Amount": charge_row.get("Charge Amount") if charge_row is not None else None,
        "Provider Activity": activity_row.get("Provider") if activity_row is not None else None,
        "Provider Charge": charge_row.get("Provider") if charge_row is not None else None,
        "Revenue Code": charge_row.get("Revenue Code") if charge_row is not None else None,
        "Expected Revenue Code": expected_revenue_code,
        "Days Late": days_late,
        "Matched On": matched_on,
    }


def build_exception_row(
    exception_type: str,
    activity_row: Optional[pd.Series] = None,
    charge_row: Optional[pd.Series] = None,
    *,
    expected_department: Optional[str] = None,
    expected_revenue_code: Optional[str] = None,
    matched_on: Optional[str] = None,
    days_late: Optional[int] = None,
) -> Dict[str, Optional[object]]:
    row = {
        "Exception Type": exception_type,
        "Why This Was Flagged": EXCEPTION_EXPLANATIONS[exception_type],
        "Suggested Review Step": REVIEW_STEPS[exception_type],
    }
    row.update(
        activity_charge_context(
            activity_row,
            charge_row,
            expected_department=expected_department,
            expected_revenue_code=expected_revenue_code,
            matched_on=matched_on,
            days_late=days_late,
        )
    )
    return row


def empty_exception_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=EXCEPTION_COLUMNS)


def make_exception_df(rows: List[Dict[str, Optional[object]]]) -> pd.DataFrame:
    if not rows:
        return empty_exception_frame()
    frame = pd.DataFrame(rows, columns=EXCEPTION_COLUMNS)
    return frame.sort_values(
        by=["Exception Type", "Account", "Service Date", "Charge Date", "CPT/HCPCS"],
        na_position="last",
    ).reset_index(drop=True)


def find_related_charge(
    activity_row: pd.Series,
    charge_df: pd.DataFrame,
    mapping_lookup: Optional[pd.DataFrame],
    related_type: str,
) -> bool:
    related = charge_df[
        (charge_df["Account"] == activity_row.get("Account"))
        & (charge_df["Charge Date"] == activity_row.get("Service Date"))
    ]

    if activity_row.get("Encounter"):
        related = related[(related["Encounter"].isna()) | (related["Encounter"] == activity_row.get("Encounter"))]

    if related.empty:
        return False

    if related_type == "implant":
        if mapping_lookup is not None:
            implant_codes = set(mapping_lookup[mapping_lookup["Implant Flag"]]["CPT/HCPCS"])
            if implant_codes:
                return related["CPT/HCPCS"].isin(implant_codes).any()
        return related["CPT/HCPCS"] == activity_row.get("CPT/HCPCS")

    if related_type == "supply":
        if mapping_lookup is None:
            return False
        supply_codes = set(mapping_lookup[mapping_lookup["Supply Flag"]]["CPT/HCPCS"])
        if not supply_codes:
            return False
        return related["CPT/HCPCS"].isin(supply_codes).any()

    return False


def build_summary(activity_df: pd.DataFrame, charge_df: pd.DataFrame, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Metric": "Total Activity Records", "Value": len(activity_df)},
            {"Metric": "Total Charge Records", "Value": len(charge_df)},
            {"Metric": "Missing Charges", "Value": len(results["missing_charges"])},
            {"Metric": "Charge Without Activity", "Value": len(results["charge_without_activity"])},
            {"Metric": "Quantity Mismatch", "Value": len(results["quantity_mismatch"])},
            {"Metric": "Duplicate Charges", "Value": len(results["duplicate_charges"])},
            {"Metric": "Implant/Supply Issues", "Value": len(results["implant_supply_issues"])},
            {"Metric": "Cost Center Mismatch", "Value": len(results["cost_center_mismatch"])},
            {"Metric": "Late Charges", "Value": len(results["late_charges"])},
            {"Metric": "Mapping Issues", "Value": len(results["mapping_issues"])},
            {"Metric": "Provider Mismatch", "Value": len(results["provider_mismatch"])},
            {"Metric": "All Exceptions", "Value": len(results["all_exceptions"])},
        ]
    )


def build_validation_notes_table(messages: List[ValidationMessage]) -> pd.DataFrame:
    if not messages:
        return pd.DataFrame([{"Severity": "Info", "Message": "No validation notes."}])
    return pd.DataFrame([{"Severity": msg.level.title(), "Message": msg.text} for msg in messages])


def run_reconciliation(
    activity_df: pd.DataFrame,
    charge_df: pd.DataFrame,
    mapping_df: Optional[pd.DataFrame] = None,
) -> ReconOutputs:
    matched_pairs, unmatched_activity, unmatched_charge = match_records(activity_df, charge_df)
    mapping_lookup = prepare_mapping_lookup(mapping_df)
    quality_messages = dataset_quality_notes(activity_df, charge_df, mapping_df)

    activity_index = activity_df.set_index("row_id")
    charge_index = charge_df.set_index("row_id")

    missing_charge_rows = [build_exception_row("Missing Charge", activity_row=row) for _, row in unmatched_activity.iterrows()]
    charge_without_activity_rows = [
        build_exception_row("Charge Without Activity", charge_row=row) for _, row in unmatched_charge.iterrows()
    ]

    duplicate_charge_rows = [
        build_exception_row("Duplicate Charge", charge_row=row)
        for _, row in charge_df[
            charge_df.duplicated(subset=["Account", "Charge Date", "CPT/HCPCS"], keep=False)
            & charge_df["Account"].notna()
            & charge_df["Charge Date"].notna()
            & charge_df["CPT/HCPCS"].notna()
        ].iterrows()
    ]

    quantity_rows: List[Dict[str, Optional[object]]] = []
    provider_rows: List[Dict[str, Optional[object]]] = []
    late_rows: List[Dict[str, Optional[object]]] = []
    cost_center_rows: List[Dict[str, Optional[object]]] = []
    revenue_rows: List[Dict[str, Optional[object]]] = []

    for _, pair in matched_pairs.iterrows():
        activity_row = activity_index.loc[int(pair["activity_row_id"])]
        charge_row = charge_index.loc[int(pair["charge_row_id"])]
        matched_on = pair["Matched On"]

        if pd.notna(activity_row.get("Quantity")) and pd.notna(charge_row.get("Quantity")):
            if activity_row["Quantity"] != charge_row["Quantity"]:
                quantity_rows.append(
                    build_exception_row(
                        "Quantity Mismatch",
                        activity_row,
                        charge_row,
                        matched_on=matched_on,
                    )
                )

        if activity_row.get("Provider") and charge_row.get("Provider") and activity_row["Provider"] != charge_row["Provider"]:
            provider_rows.append(
                build_exception_row(
                    "Provider Mismatch",
                    activity_row,
                    charge_row,
                    matched_on=matched_on,
                )
            )

        if pd.notna(activity_row.get("Service Date")) and pd.notna(charge_row.get("Charge Date")):
            if charge_row["Charge Date"] > activity_row["Service Date"]:
                days_late = int((charge_row["Charge Date"] - activity_row["Service Date"]).days)
                late_rows.append(
                    build_exception_row(
                        "Late Charge",
                        activity_row,
                        charge_row,
                        matched_on=matched_on,
                        days_late=days_late,
                    )
                )

        if mapping_lookup is not None:
            cpt_code = activity_row.get("CPT/HCPCS") or charge_row.get("CPT/HCPCS")
            if cpt_code in mapping_lookup.index:
                map_row = mapping_lookup.loc[cpt_code]
                expected_department = map_row.get("Expected Department")
                expected_revenue = map_row.get("Revenue Code")

                if expected_department and charge_row.get("Department") and expected_department != charge_row.get("Department"):
                    cost_center_rows.append(
                        build_exception_row(
                            "Cost Center Mismatch",
                            activity_row,
                            charge_row,
                            expected_department=expected_department,
                            matched_on=matched_on,
                        )
                    )

                if expected_revenue and charge_row.get("Revenue Code") and expected_revenue != charge_row.get("Revenue Code"):
                    revenue_rows.append(
                        build_exception_row(
                            "Revenue Code Issue",
                            activity_row,
                            charge_row,
                            expected_revenue_code=expected_revenue,
                            matched_on=matched_on,
                        )
                    )

    implant_supply_rows: List[Dict[str, Optional[object]]] = []
    for _, activity_row in unmatched_activity.iterrows():
        map_row = None
        cpt_code = activity_row.get("CPT/HCPCS")
        if mapping_lookup is not None and cpt_code in mapping_lookup.index:
            map_row = mapping_lookup.loc[cpt_code]

        if activity_row.get("Implant Item") and not find_related_charge(activity_row, charge_df, mapping_lookup, "implant"):
            implant_supply_rows.append(build_exception_row("Missing Implant", activity_row=activity_row))

        if map_row is not None and bool(map_row.get("Supply Flag")) and not find_related_charge(activity_row, charge_df, mapping_lookup, "supply"):
            implant_supply_rows.append(build_exception_row("Missing Supply", activity_row=activity_row))

    mapping_rows: List[Dict[str, Optional[object]]] = []
    if mapping_lookup is not None:
        mapped_codes = set(mapping_lookup["CPT/HCPCS"].dropna())
        for _, row in activity_df[(activity_df["CPT/HCPCS"].notna()) & (~activity_df["CPT/HCPCS"].isin(mapped_codes))].iterrows():
            mapping_rows.append(build_exception_row("CPT Mapping Issue", activity_row=row))
        for _, row in charge_df[(charge_df["CPT/HCPCS"].notna()) & (~charge_df["CPT/HCPCS"].isin(mapped_codes))].iterrows():
            mapping_rows.append(build_exception_row("CPT Mapping Issue", charge_row=row))
        mapping_rows.extend(revenue_rows)

    results = {
        "missing_charges": make_exception_df(missing_charge_rows),
        "charge_without_activity": make_exception_df(charge_without_activity_rows),
        "quantity_mismatch": make_exception_df(quantity_rows),
        "duplicate_charges": make_exception_df(duplicate_charge_rows),
        "implant_supply_issues": make_exception_df(implant_supply_rows),
        "cost_center_mismatch": make_exception_df(cost_center_rows),
        "late_charges": make_exception_df(late_rows),
        "mapping_issues": make_exception_df(mapping_rows),
        "provider_mismatch": make_exception_df(provider_rows),
    }

    non_empty = [frame.astype(object) for frame in results.values() if not frame.empty]
    results["all_exceptions"] = pd.concat(non_empty, ignore_index=True) if non_empty else empty_exception_frame()

    summary = build_summary(activity_df, charge_df, results)
    validation_notes = build_validation_notes_table(quality_messages)
    return ReconOutputs(summary=summary, validation_notes=validation_notes, results=results)


def signature_for_run(
    activity_file,
    charge_file,
    mapping_file,
    activity_map: Dict[str, Optional[str]],
    charge_map: Dict[str, Optional[str]],
    mapping_map: Optional[Dict[str, Optional[str]]],
) -> Tuple[object, ...]:
    return (
        getattr(activity_file, "name", None),
        getattr(charge_file, "name", None),
        getattr(mapping_file, "name", None),
        tuple(sorted(activity_map.items())),
        tuple(sorted(charge_map.items())),
        tuple(sorted((mapping_map or {}).items())),
    )


def display_messages(messages: List[ValidationMessage]) -> None:
    for message in messages:
        if message.level == "error":
            st.error(message.text)
        elif message.level == "warning":
            st.warning(message.text)
        else:
            st.info(message.text)


def display_summary_metrics(summary_df: pd.DataFrame) -> None:
    values = dict(zip(summary_df["Metric"], summary_df["Value"]))
    top_row = [
        "Total Activity Records",
        "Total Charge Records",
        "Missing Charges",
        "Charge Without Activity",
        "All Exceptions",
    ]
    cols = st.columns(len(top_row))
    for col, metric in zip(cols, top_row):
        col.metric(metric, int(values.get(metric, 0)))

    second_row = [
        "Quantity Mismatch",
        "Duplicate Charges",
        "Implant/Supply Issues",
        "Late Charges",
        "Mapping Issues",
        "Provider Mismatch",
    ]
    cols = st.columns(len(second_row))
    for col, metric in zip(cols, second_row):
        col.metric(metric, int(values.get(metric, 0)))


def display_user_help_for_tab(tab_key: str) -> None:
    help_text = {
        "missing_charges": "Use this list to find activity that likely should have produced a patient charge.",
        "charge_without_activity": "Use this list to review posted charges that may not have supporting activity or documentation.",
        "quantity_mismatch": "Use this list to compare recorded quantity against charged quantity.",
        "duplicate_charges": "Use this list to review possible duplicate charge postings.",
        "implant_supply_issues": "Use this list to review implant or supply-related charging gaps.",
        "cost_center_mismatch": "Use this list to verify that charges posted to the expected department.",
        "late_charges": "Use this list to review charges posted after the service date.",
        "mapping_issues": "Use this list to maintain CPT and revenue code mapping rules.",
        "provider_mismatch": "Use this list to verify the provider on activity versus the charge.",
        "all_exceptions": "This is a combined worklist of all exception types.",
    }
    if tab_key in help_text:
        st.caption(help_text[tab_key])


def render_results(outputs: ReconOutputs) -> None:
    tabs = st.tabs([name for name, _ in RESULT_TAB_ORDER])

    for tab, (_, key) in zip(tabs, RESULT_TAB_ORDER):
        with tab:
            if key == "summary":
                display_summary_metrics(outputs.summary)
                st.markdown("**Exception Counts**")
                st.dataframe(outputs.summary, use_container_width=True, hide_index=True)
                st.markdown("**Validation Notes**")
                st.dataframe(outputs.validation_notes, use_container_width=True, hide_index=True)
                continue

            display_user_help_for_tab(key)
            frame = outputs.results[key]
            if frame.empty:
                st.info("No records were flagged in this section.")
            else:
                st.dataframe(frame, use_container_width=True, hide_index=True)


def create_excel_report(outputs: ReconOutputs) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        outputs.summary.to_excel(writer, sheet_name="Summary", index=False)
        outputs.validation_notes.to_excel(writer, sheet_name="Validation Notes", index=False)
        for key, sheet_name in SHEET_NAMES.items():
            outputs.results[key].to_excel(writer, sheet_name=sheet_name[:31], index=False)
    output.seek(0)
    return output.getvalue()


def clear_stale_results_if_needed(current_signature: Tuple[object, ...]) -> None:
    previous_signature = st.session_state.get("charge_recon_signature")
    if previous_signature is not None and previous_signature != current_signature:
        st.session_state.pop("charge_recon_results", None)
    st.session_state["charge_recon_signature"] = current_signature


def main() -> None:
    st.title("Charge Recon Assistant")
    st.caption(
        "Compare Activity or Reconciliation exports against Patient Charges exports to identify missing charges and other reconciliation issues."
    )
    st.warning(
        "PHI warning: Do not upload PHI unless your organization has approved this use. Use exported files, de-identified data, or sample data whenever possible. Uploaded data is processed in-session only and is not stored permanently by this app."
    )

    st.subheader("File Uploads")
    upload_col1, upload_col2, upload_col3 = st.columns(3)
    with upload_col1:
        activity_file = st.file_uploader("Activity / Reconciliation file", type=["csv", "xlsx"])
    with upload_col2:
        charge_file = st.file_uploader("Patient Charges file", type=["csv", "xlsx"])
    with upload_col3:
        mapping_file = st.file_uploader("Mapping file (optional)", type=["csv", "xlsx"])

    if not activity_file or not charge_file:
        st.info("Upload the Activity / Reconciliation file and Patient Charges file to continue.")
        return

    try:
        activity_raw = load_file(activity_file)
        charge_raw = load_file(charge_file)
        mapping_raw = load_file(mapping_file) if mapping_file else None
    except Exception as exc:
        st.error(f"Unable to read one of the uploaded files: {exc}")
        return

    st.subheader("Column Mapping")
    st.write("Choose which uploaded columns correspond to each required business field.")

    mapping_col1, mapping_col2 = st.columns(2)
    with mapping_col1:
        st.markdown("**Activity File Mapping**")
        activity_map = build_mapping_ui(activity_raw, ACTIVITY_FIELDS, "activity")
    with mapping_col2:
        st.markdown("**Patient Charges Mapping**")
        charge_map = build_mapping_ui(charge_raw, CHARGE_FIELDS, "charge")

    mapping_map: Optional[Dict[str, Optional[str]]] = None
    if mapping_raw is not None:
        st.markdown("**Mapping File Mapping**")
        mapping_map = build_mapping_ui(mapping_raw, MAPPING_FIELDS, "mapping")

    setup_messages = validate_mapping_configuration(
        activity_map,
        charge_map,
        mapping_map,
        activity_raw,
        charge_raw,
        mapping_raw,
    )
    display_messages(setup_messages)
    if any(message.level == "error" for message in setup_messages):
        return

    current_signature = signature_for_run(activity_file, charge_file, mapping_file, activity_map, charge_map, mapping_map)
    clear_stale_results_if_needed(current_signature)

    st.subheader("Run Reconciliation")
    run_disabled = any(message.level == "error" for message in setup_messages)
    if st.button("Run Reconciliation", type="primary", use_container_width=True, disabled=run_disabled):
        try:
            activity_df = standardize_dataframe(activity_raw, activity_map, "activity")
            charge_df = standardize_dataframe(charge_raw, charge_map, "charge")
            mapping_df = (
                standardize_dataframe(mapping_raw, mapping_map, "mapping")
                if mapping_raw is not None and mapping_map and mapping_map.get("CPT/HCPCS")
                else None
            )
            outputs = run_reconciliation(activity_df, charge_df, mapping_df)
            st.session_state["charge_recon_results"] = outputs
            st.success("Reconciliation complete.")
        except Exception as exc:
            st.error(f"Reconciliation could not be completed: {exc}")
            return

    outputs = st.session_state.get("charge_recon_results")
    if outputs:
        st.subheader("Results")
        render_results(outputs)
        st.download_button(
            "Download Exception Report (Excel)",
            data=create_excel_report(outputs),
            file_name="charge_recon_exception_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    main()
