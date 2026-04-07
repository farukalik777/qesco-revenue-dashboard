"""
QESCO Data Enrichment Script
Run this monthly after receiving raw Excel files
Outputs: ALL-ENRICHED-COMBINED-Cleaned.xlsx
"""

import pandas as pd
import os
from datetime import datetime

print("=" * 60)
print("QESCO Data Enrichment - Monthly Processor")
print("=" * 60)

# File paths
FILES = {
    "Provincial Govt": "data/PROV-GOVT-DEPT 02-2026.xlsx",
    "Local Bodies": "data/LOCAL-BODIES-02-2026.xlsx",
    "Autonomous Bodies": "data/AUTO-BODIES-02-2026.xlsx",
    "HIERARCHY": "data/SubDivisioncode.xlsx",
    "DEPARTMENTS": "data/All Departments Codes.xlsx"
}

def clean_and_pad(val, length):
    """Clean and pad value to specified length"""
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '', 'total']:
        return "0" * length
    return str(val).split('.')[0].strip().zfill(length)

def process():
    # Check if files exist
    missing = [k for k, v in FILES.items() if not os.path.exists(v)]
    if missing:
        print(f"\n[!] Missing files: {missing}")
        print("    Please ensure all data files are in the 'data' folder")
        return False

    print("\n[>] Loading reference files...")

    # Load reference data
    df_hier = pd.read_excel(FILES["HIERARCHY"])
    df_hier.columns = [str(c).strip().upper() for c in df_hier.columns]
    df_hier['SDIV_F'] = df_hier['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))

    df_dept_map = pd.read_excel(FILES["DEPARTMENTS"])
    df_dept_map.columns = [str(c).strip().upper() for c in df_dept_map.columns]
    df_dept_map['DEPT_F'] = df_dept_map['DEPT_CODE'].apply(lambda x: clean_and_pad(x, 3))

    print(f"    [OK] SubDivision codes: {len(df_hier)} records")
    print(f"    [OK] Department codes: {len(df_dept_map)} records")

    # Load main data files
    print("\n[>] Loading main data files...")
    all_data = []
    cat_list = ["Provincial Govt", "Local Bodies", "Autonomous Bodies"]

    for cat in cat_list:
        xls = pd.ExcelFile(FILES[cat])
        for sheet in xls.sheet_names:
            tmp = pd.read_excel(xls, sheet_name=sheet)
            tmp.columns = [str(c).strip().upper() for c in tmp.columns]
            if 'SDIVCODE' in tmp.columns:
                tmp = tmp[tmp['SDIVCODE'].notna()]
                tmp = tmp[~tmp['SDIVCODE'].astype(str).str.contains('TOTAL', case=False)]
                tmp['SOURCE'] = cat
                all_data.append(tmp)
                print(f"    [OK] {cat} ({sheet}): {len(tmp)} records")

    master = pd.concat(all_data, ignore_index=True)
    print(f"\n    Total records loaded: {len(master):,}")

    # Process codes
    print("\n[>] Processing codes...")
    master['SDIV_F'] = master['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
    master['BATCH_F'] = master['BATCHNO'].apply(lambda x: clean_and_pad(x, 2))
    master['CONS_F'] = master['CONSNO'].apply(lambda x: clean_and_pad(x, 7))
    master['REF_ID'] = master['BATCH_F'] + master['SDIV_F'] + master['CONS_F']

    if 'DEPT_CODE' in master.columns:
        master['DEPT_F'] = master['DEPT_CODE'].apply(lambda x: clean_and_pad(x, 3))

    # Merge with hierarchy
    master = pd.merge(master, df_hier[['SDIV_F', 'CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']], on='SDIV_F', how='left')
    master = pd.merge(master, df_dept_map[['DEPT_F', 'DEPARTMENT_NAME']], on='DEPT_F', how='left')

    # Cleanup
    master['STATUS'] = master['PDISC'].apply(lambda x: "Active" if x == 0 else "Disconnected")
    master['DEPARTMENT_NAME'] = master['DEPARTMENT_NAME'].fillna("Other/Private")

    # Convert numeric columns
    num_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ACCURCY', 'MATCH', 'NOT MATCH', 'ALL', 'PDISC']
    for c in num_cols:
        if c in master.columns:
            master[c] = pd.to_numeric(master[c], errors='coerce').fillna(0)

    master['ARREARS'] = master['ASSESSMENT_AMNT'] - master['PAYMENT_NOR']

    # Remove rows with missing DEPARTMENT_NAME (empty calculations)
    cleaned = master.dropna(subset=['DEPARTMENT_NAME'])
    print(f"    [OK] Records after cleaning: {len(cleaned):,} (removed {len(master) - len(cleaned):,} empty rows)")

    # Save output
    output_file = 'data/ALL-ENRICHED-COMBINED-Cleaned.xlsx'
    cleaned.to_excel(output_file, index=False)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"    Total Records: {len(cleaned):,}")
    print(f"    Assessment:   PKR {cleaned['ASSESSMENT_AMNT'].sum():,.0f}")
    print(f"    Payment:      PKR {cleaned['PAYMENT_NOR'].sum():,.0f}")
    print(f"    Collection %: {(cleaned['PAYMENT_NOR'].sum() / cleaned['ASSESSMENT_AMNT'].sum() * 100):.1f}%")
    print(f"    Circles:      {cleaned['CIRCLENAME'].nunique()}")
    print(f"    Departments:  {cleaned['DEPARTMENT_NAME'].nunique()}")
    print(f"\n    [OK] Output saved to: {output_file}")
    print(f"    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        process()
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        input("\nPress Enter to exit...")
