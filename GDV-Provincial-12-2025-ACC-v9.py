import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="QESCO (Provincial Govt Dept Dashboard)", layout="wide", page_icon="🏛️")

# 2. VIBRANT CUSTOM STYLING (Including Ultra-Compact Table Grid)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 10px; 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-top: 3px solid #003366;
    }
    div[data-testid="stSidebar"] { background-color: #e9ecef; }
    
    /* This section reduces row height and font size by 30% for the compact look */
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th { 
        padding: 1px 3px !important; 
        font-size: 10.5px !important; 
        line-height: 1.0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. PASSWORD PROTECTION LOGIC
def check_password():
    def password_entered():
        if st.session_state["password"] == "Qesco@786":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password to Access QESCO Dashboard", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password to Access QESCO Dashboard", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# 4. CONFIGURATION & UTILITIES
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

# 5. DATA ENGINE
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
                all_sheets.append(temp_df)
        df_rev = pd.concat(all_sheets, ignore_index=True)

        # Load Hierarchy and Dept
        df_hier = pd.read_excel(get_drive_url(FILES["HIERARCHY"]))
        df_dept = pd.read_excel(get_drive_url(FILES["DEPARTMENTS"]))
        df_hier.columns = [str(c).strip().upper() for c in df_hier.columns]
        df_dept.columns = [str(c).strip().upper() for c in df_dept.columns]

        # Padding for Merge Keys and Reference assembly
        df_rev['BATCH_F'] = df_rev['BATCHNO'].apply(lambda x: clean_and_pad(x, 2))
        df_rev['SDIV_F'] = df_rev['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
        df_rev['CONS_F'] = df_rev['CONSNO'].apply(lambda x: clean_and_pad(x, 7))
        df_rev['REF_ID'] = df_rev['BATCH_F'] + df_rev['SDIV_F'] + df_rev['CONS_F']

        df_hier['SDIV_F'] = df_hier['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))

        # Merge with Hierarchy (Include CircleCod and DivCocd for sorting)
        master = pd.merge(df_rev, df_hier[['SDIV_F', 'CIRCLECOD', 'CIRCLENAME', 'DIVCOCD', 'DIVNAME', 'SUBDIVNAME']], on='SDIV_F', how='left')
        
        # Dept Merge
        if 'DEPT_CODE' in master.columns:
            master['DEPT_F'] = master['DEPT_CODE'].apply(lambda x: str(x).split('.')[0].strip() if pd.notna(x) else "")
            df_dept['DEPT_F'] = df_dept['DEPT_CODE'].apply(lambda x: str(x).split('.')[0].strip() if pd.notna(x) else "")
            master = pd.merge(master, df_dept[['DEPT_F', 'DEPARTMENT_NAME']], on='DEPT_F', how='left')
        
        master['STATUS'] = master['PDISC'].apply(lambda x: "Active" if x == 0 else "Disconnected")
        master['DEPARTMENT_NAME'] = master['DEPARTMENT_NAME'].fillna("Other/Private")
        
        num_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ACCURCY']
        for c in num_cols:
            if c in master.columns:
                master[c] = pd.to_numeric(master[c], errors='coerce').fillna(0)

        return master, df_hier, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        st.error(f"Sync Failure: {e}")
        return None, None, None

# --- 6. MAIN APP LOGIC (IF PASSWORD CORRECT) ---
if check_password():
    df, df_hier, sync_time = load_vibrant_data()

    if df is not None:
        # SIDEBAR
        with st.sidebar:
            st.markdown("### 🎯 Navigation Filters")
            s_cir = st.multiselect("Circle", sorted(df['CIRCLENAME'].dropna().unique()))
            div_data = df[df['CIRCLENAME'].isin(s_cir)] if s_cir else df
            s_div = st.multiselect("Division", sorted(div_data['DIVNAME'].dropna().unique()))
            s_dep = st.multiselect("Department", sorted(df['DEPARTMENT_NAME'].dropna().unique()))
            status_view = st.radio("Connection Status", ["All", "Active", "Disconnected"])
            st.info(f"Last Synced: {sync_time}")

        # FILTERING
        f_df = df.copy()
        if s_cir: f_df = f_df[f_df['CIRCLENAME'].isin(s_cir)]
        if s_div: f_df = f_df[f_df['DIVNAME'].isin(s_div)]
        if s_dep: f_df = f_df[f_df['DEPARTMENT_NAME'].isin(s_dep)]
        if status_view == "Active": f_df = f_df[f_df['STATUS'] == "Active"]
        elif status_view == "Disconnected": f_df = f_df[f_df['STATUS'] == "Disconnected"]

        # TOP HEADER & KPI CARDS
        st.markdown("## ⚡ QESCO Provincial Government Departments DashBoard")
        st.divider()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Receivables", f"{f_df['TOTAL_CL_BAL'].sum()/1e9:.2f}B")
        m2.metric("Assessment", f"{f_df['ASSESSMENT_AMNT'].sum()/1e6:.1f}M")
        m3.metric("Payment", f"{f_df['PAYMENT_NOR'].sum()/1e6:.1f}M")
        
        pay_pct = (f_df['PAYMENT_NOR'].sum() / f_df['ASSESSMENT_AMNT'].sum() * 100) if f_df['ASSESSMENT_AMNT'].sum() > 0 else 0
        m4.metric("Recovery %", f"{pay_pct:.1f}%")
        m5.metric("Accuracy", f"{f_df['ACCURCY'].mean():.1f}%")

        # TABS
        tab1, tab2, tab3 = st.tabs(["📊 Revenue Insights", "🎯 Accuracy", "📋 Master Ledger"])

        with tab1:
            st.markdown("<h3 style='color: #003366;'>Revenue Performance Analysis</h3>", unsafe_allow_html=True)
            
            # CHART AREA
            c1, c2 = st.columns([1.6, 1], gap="large")
            with c1:
                st.markdown("#### 📉 Assessment vs Recovery")
                chart_data = f_df.groupby('DIVNAME')[['ASSESSMENT_AMNT', 'PAYMENT_NOR']].sum().reset_index()
                fig = px.bar(chart_data, x='DIVNAME', y=['ASSESSMENT_AMNT', 'PAYMENT_NOR'], barmode='group')
                fig.update_layout(height=300, plot_bgcolor='white', yaxis=dict(showgrid=True, gridcolor='LightGrey', griddash='dot'))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("#### 🏆 Debt by Dept")
                dept_debt = f_df.groupby('DEPARTMENT_NAME')['TOTAL_CL_BAL'].sum().nlargest(10).reset_index()
                fig_pie = px.pie(dept_debt, values='TOTAL_CL_BAL', names='DEPARTMENT_NAME', hole=0.4)
                fig_pie.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            # COMPACT SORTED TABLE
            st.divider()
            st.markdown("#### 📋 Executive Financial Summary (Millions)")
            
            # Step 1: Aggregation including Codes for Sorting
            perf_table = f_df.groupby(['CIRCLECOD', 'CIRCLENAME', 'DIVCOCD', 'DIVNAME']).agg({
                'ASSESSMENT_AMNT': 'sum',
                'PAYMENT_NOR': 'sum',
                'TOTAL_CL_BAL': 'sum'
            }).reset_index()

            # Step 2: Sorting by CIRCLECOD then DIVCOCD
            perf_table = perf_table.sort_values(['CIRCLECOD', 'DIVCOCD'])

            # Step 3: Calculation & Conversion
            perf_table['REC_%'] = (perf_table['PAYMENT_NOR'] / perf_table['ASSESSMENT_AMNT'] * 100).fillna(0)
            for col in ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL']:
                perf_table[col] /= 1e6

            # Step 4: QESCO Total Row
            qesco_total = pd.DataFrame({
                'DIVNAME': ['⭐ QESCO TOTAL'],
                'ASSESSMENT_AMNT': [perf_table['ASSESSMENT_AMNT'].sum()],
                'PAYMENT_NOR': [perf_table['PAYMENT_NOR'].sum()],
                'REC_%': [pay_pct],
                'TOTAL_CL_BAL': [perf_table['TOTAL_CL_BAL'].sum()]
            })

            # Step 5: Final Selection & Compact Display
            final_display = pd.concat([perf_table[['DIVNAME', 'ASSESSMENT_AMNT', 'PAYMENT_NOR', 'REC_%', 'TOTAL_CL_BAL']], qesco_total], ignore_index=True)

            st.dataframe(
                final_display, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "DIVNAME": st.column_config.TextColumn("Division Name", width=120),
                    "ASSESSMENT_AMNT": st.column_config.NumberColumn("Assmt", format="%.1fM", width=55),
                    "PAYMENT_NOR": st.column_config.NumberColumn("Paymt", format="%.1fM", width=55),
                    "REC_%": st.column_config.NumberColumn("Rec %", format="%.1f%%", width=45),
                    "TOTAL_CL_BAL": st.column_config.NumberColumn("Closing", format="%.1fM", width=65)
                }
            )

        with tab2:
            st.markdown("#### Accuracy Drill-Down")
            # Heatmap and Accuracy Chart logic goes here...

        with tab3:
            st.markdown("#### Detailed Master Ledger")
            # Searchable Dataframe logic goes here...

    else:
        st.warning("🔄 System Initializing... Please verify data connections.")
