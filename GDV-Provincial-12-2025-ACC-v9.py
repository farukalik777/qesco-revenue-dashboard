import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. PAGE CONFIGURATION (Must be at the very top)
st.set_page_config(page_title="QESCO (Provincial Govt Dept Dashboard)", layout="wide", page_icon="🏛️")

# Vibrant Custom Styling
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-top: 3px solid #6c757d;
    }
    div[data-testid="stSidebar"] { background-color: #e9ecef; }
    /* Ultra-compact Table CSS */
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th { 
        padding: 1px 3px !important; 
        font-size: 10.5px !important; 
        line-height: 1.0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD PROTECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == "Qesco@786"}), key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == "Qesco@786"}), key="password")
        st.error("😕 Password incorrect")
        return False
    return True

# --- CONFIGURATION ---
FILES = {
    "REVENUE": "1yrWTmDqNwM-7MUTYbSRjy8kW9watFm-8",
    "HIERARCHY": "1PXzjMPsYH_41rSaOHEfOmjwxBfHF9WbX",
    "DEPARTMENTS": "1dHIIzj5gpwqU4yQ6ZQgpiys-DHYF-5qp"
}

def get_drive_url(file_id):
    return f"https://drive.google.com/uc?id={file_id}"

def clean_and_pad(val, length):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '', 'total']: 
        return "0" * length
    return str(val).split('.')[0].strip().zfill(length)

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)
def load_vibrant_data():
    try:
        xls = pd.ExcelFile(get_drive_url(FILES["REVENUE"]))
        all_sheets = [pd.read_excel(xls, sheet_name=name) for name in xls.sheet_names]
        df_rev = pd.concat(all_sheets, ignore_index=True)
        df_rev.columns = [str(c).strip().upper() for c in df_rev.columns]

        df_hier = pd.read_excel(get_drive_url(FILES["HIERARCHY"]))
        df_dept = pd.read_excel(get_drive_url(FILES["DEPARTMENTS"]))
        df_hier.columns = [str(c).strip().upper() for c in df_hier.columns]
        df_dept.columns = [str(c).strip().upper() for c in df_dept.columns]

        # Padding for Merge
        df_rev['SDIV_F'] = df_rev['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
        df_hier['SDIV_F'] = df_hier['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))

        # 15-Digit Reference Assembly
        df_rev['BATCH_F'] = df_rev['BATCHNO'].apply(lambda x: clean_and_pad(x, 2))
        df_rev['CONS_F'] = df_rev['CONSNO'].apply(lambda x: clean_and_pad(x, 7))
        df_rev['REF_ID'] = df_rev['BATCH_F'] + df_rev['SDIV_F'] + df_rev['CONS_F']

        # MERGING
        master = pd.merge(df_rev, df_hier[['SDIV_F', 'CIRCLECOD', 'CIRCLENAME', 'DIVCOCD', 'DIVNAME', 'SUBDIVNAME']], on='SDIV_F', how='left')
        
        # Dept Merge
        if 'DEPT_CODE' in master.columns:
            master['DEPT_F'] = master['DEPT_CODE'].apply(lambda x: str(x).split('.')[0].strip() if pd.notna(x) else "")
            df_dept['DEPT_F'] = df_dept['DEPT_CODE'].apply(lambda x: str(x).split('.')[0].strip() if pd.notna(x) else "")
            master = pd.merge(master, df_dept[['DEPT_F', 'DEPARTMENT_NAME']], on='DEPT_F', how='left')

        master['STATUS'] = master['PDISC'].apply(lambda x: "Active" if x == 0 else "Disconnected")
        master['DEPARTMENT_NAME'] = master['DEPARTMENT_NAME'].fillna("Other/Private")
        
        return master, df_hier, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        st.error(f"Sync Failure: {e}")
        return None, None, None

# --- MAIN APP EXECUTION ---
if check_password():
    df, df_hier, sync_time = load_vibrant_data()

    if df is not None:
        # SIDEBAR FILTERS
        with st.sidebar:
            st.markdown("### 🎯 Filters")
            s_cir = st.multiselect("Circle", sorted(df['CIRCLENAME'].dropna().unique()))
            div_data = df[df['CIRCLENAME'].isin(s_cir)] if s_cir else df
            s_div = st.multiselect("Division", sorted(div_data['DIVNAME'].dropna().unique()))
            s_dep = st.multiselect("Department", sorted(df['DEPARTMENT_NAME'].dropna().unique()))
            status_view = st.radio("Status", ["All", "Active", "Disconnected"])
            st.info(f"Last Synced: {sync_time}")

        # FILTER LOGIC
        f_df = df.copy()
        if s_cir: f_df = f_df[f_df['CIRCLENAME'].isin(s_cir)]
        if s_div: f_df = f_df[f_df['DIVNAME'].isin(s_div)]
        if s_dep: f_df = f_df[f_df['DEPARTMENT_NAME'].isin(s_dep)]
        if status_view != "All": f_df = f_df[f_df['STATUS'] == status_view]

        # TOP METRICS
        st.markdown("## ⚡ QESCO Provincial Departments")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receivables", f"{f_df['TOTAL_CL_BAL'].sum()/1e6:.1f}M")
        m2.metric("Assessment", f"{f_df['ASSESSMENT_AMNT'].sum()/1e6:.1f}M")
        m3.metric("Payment", f"{f_df['PAYMENT_NOR'].sum()/1e6:.1f}M")
        rec_pct = (f_df['PAYMENT_NOR'].sum() / f_df['ASSESSMENT_AMNT'].sum() * 100) if f_df['ASSESSMENT_AMNT'].sum() > 0 else 0
        m4.metric("Recovery %", f"{rec_pct:.1f}%")

        tab1, tab2, tab3 = st.tabs(["📊 Revenue Insights", "🎯 Accuracy", "📋 Master Ledger"])

        with tab1:
            # --- COMPACT SORTED TABLE ---
            st.markdown("### 📋 Executive Summary (Millions)")
            
            # Aggregation & Sorting by CIRCLECOD
            perf_data = f_df.groupby(['CIRCLECOD', 'CIRCLENAME', 'DIVCOCD', 'DIVNAME']).agg({
                'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum', 'TOTAL_CL_BAL': 'sum'
            }).reset_index().sort_values(['CIRCLECOD', 'DIVCOCD'])

            perf_data['REC_%'] = (perf_data['PAYMENT_NOR'] / perf_data['ASSESSMENT_AMNT'] * 100).fillna(0)
            
            for c in ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL']:
                perf_data[c] /= 1e6

            # Total Row
            qesco_total = pd.DataFrame({
                'DIVNAME
