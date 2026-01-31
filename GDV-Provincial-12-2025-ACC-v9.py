import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Provincial  Govt Dept Dashboard", layout="wide", page_icon="🏛️")

# Vibrant Custom Styling to match your provided screenshots
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
   .stTabs [data-baseweb="tab-list"] { gap: 10px; }
   .stTabs [data-baseweb="tab"] {
       height: 40px;
       white-space: pre-wrap;
       background-color: #f8f9fa;
       border-radius: 5px 5px 0px 0px;
       padding: 5px 20px;
   }
   .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #ff4b4b; }
   </style>
   """, unsafe_allow_html=True)

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
clean_val = str(val).split('.')[0].strip()
return clean_val.zfill(length)

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)
def load_vibrant_data():
try:
# Load Revenue Data
xls = pd.ExcelFile(get_drive_url(FILES["REVENUE"]))
all_sheets = []
for name in xls.sheet_names:
temp_df = pd.read_excel(xls, sheet_name=name)
temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
if 'SDIVCODE' in temp_df.columns:
temp_df = temp_df[temp_df['SDIVCODE'].notna()]
temp_df = temp_df[~temp_df['SDIVCODE'].astype(str).str.contains('TOTAL', case=False)]
all_sheets.append(temp_df)
df_rev = pd.concat(all_sheets, ignore_index=True)

# Load Hierarchy and Dept
df_hier = pd.read_excel(get_drive_url(FILES["HIERARCHY"]))
df_dept = pd.read_excel(get_drive_url(FILES["DEPARTMENTS"]))
df_hier.columns = [str(c).strip().upper() for c in df_hier.columns]
df_dept.columns = [str(c).strip().upper() for c in df_dept.columns]

# --- SEAMLESS 15-DIGIT REFERENCE CONCATENATION ---
df_rev['BATCH_F'] = df_rev['BATCHNO'].apply(lambda x: clean_and_pad(x, 2))
df_rev['SDIV_F'] = df_rev['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
df_rev['CONS_F'] = df_rev['CONSNO'].apply(lambda x: clean_and_pad(x, 7))
df_rev['REF_ID'] = df_rev['BATCH_F'] + df_rev['SDIV_F'] + df_rev['CONS_F']

# --- MERGING ---
df_hier['SDIV_F'] = df_hier['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
master = pd.merge(df_rev, df_hier[['SDIV_F', 'CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']], on='SDIV_F', how='left')

if 'DEPT_CODE' in df_rev.columns:
master['DEPT_F'] = master['DEPT_CODE'].apply(lambda x: str(x).split('.')[0].strip() if pd.notna(x) else "")
df_dept['DEPT_F'] = df_dept['DEPT_CODE'].apply(lambda x: str(x).split('.')[0].strip() if pd.notna(x) else "")
master = pd.merge(master, df_dept[['DEPT_F', 'DEPARTMENT_NAME']], on='DEPT_F', how='left')

# Cleanup
master['STATUS'] = master['PDISC'].apply(lambda x: "Active" if x == 0 else "Disconnected")
master['DEPARTMENT_NAME'] = master['DEPARTMENT_NAME'].fillna("Other/Private")
num_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ACCURCY']
for c in num_cols:
if c in master.columns:
master[c] = pd.to_numeric(master[c], errors='coerce').fillna(0)

return master, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
except Exception as e:
st.error(f"Sync Failure: {e}")
return None, None

df, sync_time = load_vibrant_data()

if df is not None:
# --- SIDEBAR (Matches image_f4dcbb) ---
with st.sidebar:
st.markdown("### 🎯 Navigation & Filters")
s_cir = st.multiselect("Select Circle", sorted(df['CIRCLENAME'].dropna().unique()))

div_data = df[df['CIRCLENAME'].isin(s_cir)] if s_cir else df
s_div = st.multiselect("Select Division", sorted(div_data['DIVNAME'].dropna().unique()))

sub_data = div_data[div_data['DIVNAME'].isin(s_div)] if s_div else div_data
s_sub = st.multiselect("Select Sub-Division", sorted(sub_data['SUBDIVNAME'].dropna().unique()))

s_dep = st.multiselect("Select Department", sorted(df['DEPARTMENT_NAME'].dropna().unique()))

st.divider()
status_view = st.radio("Connection Status", ["All", "Active (0)", "PDISC (1)"])

st.info(f"Last Synced: {sync_time}")

# --- FILTER LOGIC ---
f_df = df.copy()
if s_cir: f_df = f_df[f_df['CIRCLENAME'].isin(s_cir)]
if s_div: f_df = f_df[f_df['DIVNAME'].isin(s_div)]
if s_sub: f_df = f_df[f_df['SUBDIVNAME'].isin(s_sub)]
if s_dep: f_df = f_df[f_df['DEPARTMENT_NAME'].isin(s_dep)]
if status_view == "Active (0)": f_df = f_df[f_df['STATUS'] == "Active"]
elif status_view == "PDISC (1)": f_df = f_df[f_df['STATUS'] == "Disconnected"]

# --- TOP HEADER & METRICS ---
st.markdown("## 🏛️  Provincial Govt Departments Dashboard")
st.divider()

m1, m2, m3, m4 = st.columns(4)
trec = f_df['TOTAL_CL_BAL'].sum()
rec_label = f"{trec/1e9:.2f}B" if trec >= 1e9 else f"{trec/1e6:.2f}M"

m1.metric("Total Receivables", rec_label)
m2.metric("Billing Accuracy", f"{f_df['ACCURCY'].mean():.1f}%")
m3.metric("Current Assessment", f"{f_df['ASSESSMENT_AMNT'].sum()/1e6:.2f}M")
    m4.metric("Selected Records", f"{len(f_df):,}")
    m4.metric("Current Payment", f"{f_df['PAYMENT_NOR'].sum()/1e6:.2f}M")
    m5.metric("Selected Records", f"{len(f_df):,}")
# --- TABS (Enhanced Visibility & Prominence) ---
tab1, tab2, tab3 = st.tabs(["📊 Revenue Insights", "🎯 Accuracy Analysis", "📋 Master Ledger"])

@@ -320,4 +321,4 @@
mime="text/csv",
)
else:
    st.warning("🔄 System Initializing... Please verify data connections.")
    st.warning("🔄 System Initializing... Please verify data connections.")
