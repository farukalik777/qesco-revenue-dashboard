"""
Data Processor Utilities
Handles enrichment of QESCO revenue data with department names and location hierarchy
"""

import pandas as pd
from datetime import datetime

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

def load_reference_data():
    """Load department codes and subdivision hierarchy"""
    try:
        df_hier = pd.read_excel(FILES["HIERARCHY"])
        df_hier.columns = [str(c).strip().upper() for c in df_hier.columns]
        df_hier['SDIV_F'] = df_hier['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))

        df_dept_map = pd.read_excel(FILES["DEPARTMENTS"])
        df_dept_map.columns = [str(c).strip().upper() for c in df_dept_map.columns]
        df_dept_map['DEPT_F'] = df_dept_map['DEPT_CODE'].apply(lambda x: clean_and_pad(x, 3))

        return df_hier, df_dept_map
    except Exception as e:
        raise Exception(f"Failed to load reference data: {e}")

def load_main_data():
    """Load and combine all main data files"""
    try:
        df_hier, df_dept_map = load_reference_data()

        cat_list = ["Provincial Govt", "Local Bodies", "Autonomous Bodies"]
        all_data = []

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

        master = pd.concat(all_data, ignore_index=True)

        # Process codes
        master['SDIV_F'] = master['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
        master['BATCH_F'] = master['BATCHNO'].apply(lambda x: clean_and_pad(x, 2))
        master['CONS_F'] = master['CONSNO'].apply(lambda x: clean_and_pad(x, 7))
        master['REF_ID'] = master['BATCH_F'] + master['SDIV_F'] + master['CONS_F']

        if 'DEPT_CODE' in master.columns:
            master['DEPT_F'] = master['DEPT_CODE'].apply(lambda x: clean_and_pad(x, 3))

        # Merge with hierarchy and department data
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

        return master, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        raise Exception(f"Failed to load main data: {e}")

def load_uploaded_file(filepath):
    """Load data from an uploaded/processed file"""
    try:
        df = pd.read_excel(filepath)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Ensure required columns exist
        required = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'CIRCLENAME', 'DEPARTMENT_NAME']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise Exception(f"Missing required columns: {missing}")

        # Convert numeric columns
        num_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ACCURCY', 'MATCH', 'NOT MATCH', 'ALL', 'PDISC']
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        df['ARREARS'] = df['ASSESSMENT_AMNT'] - df['PAYMENT_NOR']
        df['STATUS'] = df.get('PDISC', 0).apply(lambda x: "Active" if x == 0 else "Disconnected")

        return df, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        raise Exception(f"Failed to load uploaded file: {e}")

def get_data_summary(df):
    """Get summary statistics of the data"""
    summary = {
        'total_records': len(df),
        'total_assessment': df['ASSESSMENT_AMNT'].sum(),
        'total_payment': df['PAYMENT_NOR'].sum(),
        'total_arrears': df['ARREARS'].sum(),
        'total_closing': df['TOTAL_CL_BAL'].sum(),
        'accuracy': (df['MATCH'].sum() / df['ALL'].sum() * 100) if df['ALL'].sum() > 0 else 0,
        'collection_pct': (df['PAYMENT_NOR'].sum() / df['ASSESSMENT_AMNT'].sum() * 100) if df['ASSESSMENT_AMNT'].sum() > 0 else 0,
        'circles': df['CIRCLENAME'].nunique(),
        'departments': df['DEPARTMENT_NAME'].nunique(),
    }
    return summary
