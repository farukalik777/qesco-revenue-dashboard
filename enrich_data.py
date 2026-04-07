import pandas as pd
import glob

# Load reference files
print("Loading reference files...")

dept_codes = pd.read_excel("data/All Departments Codes.xlsx")
subdiv_codes = pd.read_excel("data/SubDivisioncode.xlsx")

print(f"Department codes: {len(dept_codes)} records")
print(f"Sub-Division codes: {len(subdiv_codes)} records")

# Prepare reference data
dept_ref = dept_codes[['DEPT_CODE', 'DEPARTMENT_NAME']].drop_duplicates()
subdiv_ref = subdiv_codes[['SDIVCODE', 'SDNAME', 'SUBDIVNAME', 'DIVCODE', 'DNAME', 'DIVNAME', 'CIRCLECODE', 'CIRCLE', 'CIRCLENAME']]

def enrich_data(df, source_name):
    """Add department name and location hierarchy to a dataframe"""
    df = df.copy()

    # Merge with department names
    df = df.merge(dept_ref, on='DEPT_CODE', how='left')

    # Merge with sub-division/circle info
    df = df.merge(subdiv_ref, on='SDIVCODE', how='left')

    print(f"{source_name}: {len(df)} records enriched")
    return df

# Process each main file
output_files = []

# 1. AUTO-BODIES
print("\n--- AUTO-BODIES ---")
auto_bodies = pd.read_excel("data/AUTO-BODIES-02-2026.xlsx")
auto_bodies = enrich_data(auto_bodies, "AUTO-BODIES")
auto_bodies.to_excel("data/AUTO-BODIES-02-2026-Enriched.xlsx", index=False)
output_files.append("data/AUTO-BODIES-02-2026-Enriched.xlsx")

# 2. LOCAL-BODIES (Export Worksheet sheet only)
print("\n--- LOCAL-BODIES ---")
local_bodies = pd.read_excel("data/LOCAL-BODIES-02-2026.xlsx", sheet_name="Export Worksheet")
local_bodies = enrich_data(local_bodies, "LOCAL-BODIES")
local_bodies.to_excel("data/LOCAL-BODIES-02-2026-Enriched.xlsx", index=False)
output_files.append("data/LOCAL-BODIES-02-2026-Enriched.xlsx")

# 3. PROV-GOVT-DEPT (all sheets)
print("\n--- PROV-GOVT-DEPT ---")
prov_files = pd.read_excel("data/PROV-GOVT-DEPT 02-2026.xlsx", sheet_name=None)
all_prov_combined = []

for sheet_name, df in prov_files.items():
    if sheet_name != "Sheet1":  # Skip the SQL sheet
        df = df.copy()
        df['SOURCE_SHEET'] = sheet_name
        all_prov_combined.append(df)

prov_govt = pd.concat(all_prov_combined, ignore_index=True)
prov_govt = enrich_data(prov_govt, "PROV-GOVT-DEPT")
prov_govt.to_excel("data/PROV-GOVT-DEPT-02-2026-Enriched.xlsx", index=False)
output_files.append("data/PROV-GOVT-DEPT-02-2026-Enriched.xlsx")

print("\n" + "="*50)
print("ENRICHMENT COMPLETE!")
print("="*50)
print("\nOutput files created:")
for f in output_files:
    print(f"  - {f}")

print("\nNew columns added:")
print("  - DEPARTMENT_NAME (from All Departments Codes)")
print("  - SDNAME, SUBDIVNAME (Sub-Division)")
print("  - DIVCODE, DNAME, DIVNAME (Division)")
print("  - CIRCLECODE, CIRCLE, CIRCLENAME (Circle)")
