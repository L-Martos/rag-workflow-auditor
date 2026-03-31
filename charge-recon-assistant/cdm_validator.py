import csv

# Column names in your CDM file
HCPCS_COL = "HCPCS"
REV_COL = "Revenue Code"

def validate_cdm(input_file, output_file):
    """
    Read a CDM CSV and:
      - flag duplicate HCPCS codes
      - flag invalid revenue codes (non-4-digit numbers)
    Writes a new CSV with an 'Error' column.
    """
    seen_codes = set()
    invalid_rows = []
    valid_rows = []

    try:
        with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames

            # Safety check: required columns
            if HCPCS_COL not in fieldnames or REV_COL not in fieldnames:
                print(f"ERROR: Expected columns '{HCPCS_COL}' and '{REV_COL}' in the file.")
                print(f"Found columns: {fieldnames}")
                return

            for row in reader:
                code = row.get(HCPCS_COL, "").strip()
                revenue = row.get(REV_COL, "").strip()

                # Flag duplicate HCPCS
                if code in seen_codes:
                    row["Error"] = "Duplicate HCPCS"
                    invalid_rows.append(row)
                    continue
                else:
                    seen_codes.add(code)

                # Check Revenue Code is 4-digit numeric
                if not revenue.isdigit() or len(revenue) != 4:
                    row["Error"] = "Invalid Revenue Code"
                    invalid_rows.append(row)
                    continue

                # Passed all checks
                row["Error"] = ""
                valid_rows.append(row)

    except FileNotFoundError:
        print(f"ERROR: Input file '{input_file}' not found.")
        return

    # Write combined report
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames + ["Error"])
        writer.writeheader()
        writer.writerows(valid_rows + invalid_rows)

    # Simple summary
    total = len(valid_rows) + len(invalid_rows)
    print(f"Validation complete! Cleaned file saved as {output_file}")
    print(f"Total rows: {total}")
    print(f"Valid rows: {len(valid_rows)}")
    print(f"Rows with issues: {len(invalid_rows)}")


if __name__ == "__main__":
    # You can change filenames here if needed
    validate_cdm("cdm_input.csv", "cleaned_cdm_output.csv")
