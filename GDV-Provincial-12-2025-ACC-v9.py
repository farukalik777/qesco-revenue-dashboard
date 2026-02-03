import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="QESCO Executive Dashboard", layout="wide", page_icon="🏛️")

# Vibrant Custom Styling - Restored to original rich UI
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #6c757d;
    }
    div[data-testid="stSidebar"] { background-color: #e9ecef; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px; white-space: pre-wrap; background-color: #f8f9fa;
        border-radius: 5px 5px 0px 0px; padding: 5px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #ff4b4b; }
    
    /* Executive Table Styling */
    div[data-testid="stDataFrame"] td { font-size: 11px !important; padding: 2px !important; }
    div[data-testid="stDataFrame"] th { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PASSWORD PROTECTION ---
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
    return True

# --- 3. DATA ENGINE ---
FILES = {
    "Provincial Govt": "1yrWTmDqNwM-7MUTYbSRjy8kW9watFm-8",
    "Local Bodies": "1PVFiOKr-iKVkOEYg4Cxop3gvQQchwldu",
    "Federal Govt": "1jtQ9SX63fN2Xrvg3Rp1uaCI7or5d_yYa",
    "Autonomous Bodies": "1DtB7QCCki_aCARrahS0-6O8Ptemz2nJm",
    "HIERARCHY": "1PXzjMPsYH_41rSaOHEfOmjwxBfHF9WbX",
    "DEPARTMENTS": "1dHIIzj5gpwqU4yQ6ZQgpiys-DHYF-5qp"
}

def get_drive_url(file_id):
    return f"https://drive.google.com/uc?id={file_id}"

def clean_and_pad(val, length):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '', 'total']: 
        return "0" * length
    return str(val).split('.')[0].strip().zfill(length)

@st.cache_data(ttl=3600)
def load_vibrant_data():
    try:
        # Load Reference Tables
        df_hier = pd.read_excel(get_drive_url(FILES["HIERARCHY"]))
        df_hier.columns = [str(c).strip().upper() for c in df_hier.columns]
        df_hier['SDIV_F'] = df_hier['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))

        df_dept_map = pd.read_excel(get_drive_url(FILES["DEPARTMENTS"]))
        df_dept_map.columns = [str(c).strip().upper() for c in df_dept_map.columns]
        df_dept_map['DEPT_F'] = df_dept_map['DEPT_CODE'].apply(lambda x: clean_and_pad(x, 3))

        # Consolidated Load
        cat_list = ["Provincial Govt", "Local Bodies", "Federal Govt", "Autonomous Bodies"]
        all_data = []
        for cat in cat_list:
            xls = pd.ExcelFile(get_drive_url(FILES[cat]))
            for sheet in xls.sheet_names:
                tmp = pd.read_excel(xls, sheet_name=sheet)
                tmp.columns = [str(c).strip().upper() for c in tmp.columns]
                if 'SDIVCODE' in tmp.columns:
                    tmp = tmp[tmp['SDIVCODE'].notna()]
                    tmp = tmp[~tmp['SDIVCODE'].astype(str).str.contains('TOTAL', case=False)]
                    tmp['GOV_CAT'] = cat
                    all_data.append(tmp)
        
        master = pd.concat(all_data, ignore_index=True)

        # 15-Digit Reference & Dept Code Processing
        master['SDIV_F'] = master['SDIVCODE'].apply(lambda x: clean_and_pad(x, 5))
        master['BATCH_F'] = master['BATCHNO'].apply(lambda x: clean_and_pad(x, 2))
        master['CONS_F'] = master['CONSNO'].apply(lambda x: clean_and_pad(x, 7))
        master['REF_ID'] = master['BATCH_F'] + master['SDIV_F'] + master['CONS_F']
        
        if 'DEPT_CODE' in master.columns:
            master['DEPT_F'] = master['DEPT_CODE'].apply(lambda x: clean_and_pad(x, 3))

        # Merging
        master = pd.merge(master, df_hier[['SDIV_F', 'CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']], on='SDIV_F', how='left')
        master = pd.merge(master, df_dept_map[['DEPT_F', 'DEPARTMENT_NAME']], on='DEPT_F', how='left')
        
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

# --- 4. MAIN APP LOGIC ---
if check_password():
    df, sync_time = load_vibrant_data()

    if df is not None:
        # --- SIDEBAR ---
        with st.sidebar:
            st.markdown("### 🏛️ Navigation & Filters")
            s_cat = st.multiselect("Govt Category", df['GOV_CAT'].unique(), default=df['GOV_CAT'].unique())
            cat_df = df[df['GOV_CAT'].isin(s_cat)]

            s_cir = st.multiselect("Select Circle", sorted(cat_df['CIRCLENAME'].dropna().unique()))
            div_data = cat_df[cat_df['CIRCLENAME'].isin(s_cir)] if s_cir else cat_df
            s_div = st.multiselect("Select Division", sorted(div_data['DIVNAME'].dropna().unique()))
            sub_data = div_data[div_data['DIVNAME'].isin(s_div)] if s_div else div_data
            s_sub = st.multiselect("Select Sub-Division", sorted(sub_data['SUBDIVNAME'].dropna().unique()))
            
            s_dep = st.multiselect("Select Department", sorted(df['DEPARTMENT_NAME'].dropna().unique()))
            
            st.divider()
            status_view = st.radio("Connection Status", ["All", "Active (0)", "PDISC (1)"])
            st.info(f"Last Synced: {sync_time}")

        # Filter Application
        f_df = cat_df.copy()
        if s_cir: f_df = f_df[f_df['CIRCLENAME'].isin(s_cir)]
        if s_div: f_df = f_df[f_df['DIVNAME'].isin(s_div)]
        if s_sub: f_df = f_df[f_df['SUBDIVNAME'].isin(s_sub)]
        if s_dep: f_df = f_df[f_df['DEPARTMENT_NAME'].isin(s_dep)]
        if status_view == "Active (0)": f_df = f_df[f_df['STATUS'] == "Active"]
        elif status_view == "PDISC (1)": f_df = f_df[f_df['STATUS'] == "Disconnected"]

        # --- TOP HEADER & METRICS ---
        st.markdown("## ⚡ QESCO Consolidated Government Departments DashBoard")
        st.divider()

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        trec = f_df['TOTAL_CL_BAL'].sum()
        total_pay = f_df['PAYMENT_NOR'].sum()
        total_ass = f_df['ASSESSMENT_AMNT'].sum()

        m1.metric("Total Receivables", f"{trec/1e9:.2f}B" if trec >= 1e9 else f"{trec/1e6:.2f}M")
        m2.metric("Billing Accuracy", f"{f_df['ACCURCY'].mean():.1f}%")
        m3.metric("Current Assessment", f"{total_ass/1e6:.2f}M")
        m4.metric("Current Payment", f"{total_pay/1e6:.2f}M")
        m5.metric("Payment %", f"{(total_pay/total_ass*100) if total_ass > 0 else 0:.1f}%")
        m6.metric("Selected Records", f"{len(f_df):,}")

        # --- TABS ---
        tab1, tab2, tab3 = st.tabs(["📊 Revenue Insights", "🎯 Accuracy Analysis", "📋 Master Ledger"])

        with tab1:
            st.markdown("<h2 style='text-align: center; color: #003366;'>Revenue Performance Analysis</h2>", unsafe_allow_html=True)
            st.divider()
            
            c1, c2 = st.columns([1.6, 1], gap="large")
            with c1:
                st.markdown("### 📉 Assessment vs Recovery")
                perf_data = f_df.groupby('DIVNAME')[['ASSESSMENT_AMNT', 'PAYMENT_NOR']].sum().reset_index()
                fig = px.bar(perf_data, x='DIVNAME', y=['ASSESSMENT_AMNT', 'PAYMENT_NOR'], barmode='group', color_discrete_sequence=['#0056b3', '#00d4ff'])
                fig.update_layout(height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02), plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
                
            with c2:
                st.markdown("### Top 10 Defaulter Departments")
                dept_debt = f_df.groupby('DEPARTMENT_NAME')['TOTAL_CL_BAL'].sum().nlargest(10).reset_index()
                fig_pie = px.pie(dept_debt, values='TOTAL_CL_BAL', names='DEPARTMENT_NAME', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
                fig_pie.update_layout(height=300, showlegend=False, margin=dict(t=50, b=50, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)

            # Executive Table with QESCO TOTAL
            st.markdown("### 📋 Executive Financial Summary (Millions)")
            perf_tab = f_df.groupby(['CIRCLENAME', 'DIVNAME']).agg({'ASSESSMENT_AMNT':'sum', 'PAYMENT_NOR':'sum', 'TOTAL_CL_BAL':'sum'}).reset_index().sort_values(['CIRCLENAME', 'DIVNAME'])
            perf_tab['RECOVERY_%'] = (perf_tab['PAYMENT_NOR'] / perf_tab['ASSESSMENT_AMNT'] * 100).fillna(0)
            
            qesco_total = pd.DataFrame({
                'DIVNAME': ['⭐ QESCO TOTAL'],
                'ASSESSMENT_AMNT': [perf_tab['ASSESSMENT_AMNT'].sum()],
                'PAYMENT_NOR': [perf_tab['PAYMENT_NOR'].sum()],
                'RECOVERY_%': [(perf_tab['PAYMENT_NOR'].sum()/perf_tab['ASSESSMENT_AMNT'].sum()*100) if perf_tab['ASSESSMENT_AMNT'].sum()>0 else 0],
                'TOTAL_CL_BAL': [perf_tab['TOTAL_CL_BAL'].sum()]
            })
            
            final_table = pd.concat([perf_tab[['DIVNAME', 'ASSESSMENT_AMNT', 'PAYMENT_NOR', 'RECOVERY_%', 'TOTAL_CL_BAL']], qesco_total], ignore_index=True)
            for c in ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL']: final_table[c] /= 1e6

            st.dataframe(final_table, use_container_width=True, hide_index=True, column_config={
                "DIVNAME": st.column_config.TextColumn("Division"),
                "ASSESSMENT_AMNT": st.column_config.NumberColumn("Assessment", format="%.1f M"),
                "PAYMENT_NOR": st.column_config.NumberColumn("Payment", format="%.1f M"),
                "RECOVERY_%": st.column_config.NumberColumn("Rec %", format="%.1f%%"),
                "TOTAL_CL_BAL": st.column_config.NumberColumn("Closing", format="%.1f M")
            })

        with tab2:
            st.markdown("<h2 style='text-align: center; color: #b22222;'>🎯 Accuracy Analysis</h2>", unsafe_allow_html=True)
            st.divider()
            h_axis = 'SUBDIVNAME' if s_sub else ('DIVNAME' if s_div else 'CIRCLENAME')
            
            col_l, col_r = st.columns([1, 1.2], gap="large")
            with col_l:
                st.markdown(f"#### 🌡️ {h_axis} Heatmap")
                heat_data = f_df.groupby([h_axis, 'STATUS'])['ACCURCY'].mean().unstack().fillna(0)
                fig_heat = px.imshow(heat_data, text_auto=".1f", color_continuous_scale='RdYlGn')
                fig_heat.update_layout(height=450)
                st.plotly_chart(fig_heat, use_container_width=True)
                
            with col_r:
                st.markdown("#### 📊 Department Accuracy Ranking")
                dept_acc = f_df.groupby('DEPARTMENT_NAME')['ACCURCY'].mean().sort_values(ascending=True).reset_index()
                fig_rank = px.bar(dept_acc, y='DEPARTMENT_NAME', x='ACCURCY', orientation='h', color='ACCURCY', color_continuous_scale='RdYlGn', text=dept_acc['ACCURCY'].apply(lambda x: f'{x:.1f}%'))
                fig_rank.add_vline(x=100, line_dash="dot", line_color="black")
                fig_rank.update_layout(height=500, xaxis_range=[0, 120], plot_bgcolor='white')
                st.plotly_chart(fig_rank, use_container_width=True)

            st.divider()
            c1, c2 = st.columns(2)
            dept_acc_sorted = dept_acc.sort_values('ACCURCY')
            c1.error("📉 **Bottom 5 Performers**")
            c1.table(dept_acc_sorted.head(5).set_index('DEPARTMENT_NAME'))
            c2.success("📈 **Top 5 Performers**")
            c2.table(dept_acc_sorted.tail(5).iloc[::-1].set_index('DEPARTMENT_NAME'))

        with tab3:
            st.markdown("### 📋 Detailed Revenue Ledger")
            identity_cols = ['REF_ID', 'NAME', 'DEPT_F', 'DEPARTMENT_NAME', 'GOV_CAT', 'STATUS']
            revenue_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ACCURCY']
            location_cols = ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']
            cols_to_show = identity_cols + revenue_cols + location_cols
            
            search_query = st.text_input("🔍 Search by Name, 15-Digit Ref ID, or Dept Code")
            display_df = f_df
            if search_query:
                display_df = f_df[f_df['NAME'].str.contains(search_query, case=False, na=False) | f_df['REF_ID'].str.contains(search_query, na=False) | f_df['DEPT_F'].str.contains(search_query, na=False)]

            st.dataframe(display_df[cols_to_show], use_container_width=True, height=600, column_config={
                "REF_ID": "Reference ID", "DEPT_F": "Dept Code", "TOTAL_CL_BAL": st.column_config.NumberColumn("Closing", format="Rs %d"),
                "ACCURCY": st.column_config.ProgressColumn("Accuracy %", min_value=0, max_value=100)
            })
            st.download_button(label="📥 Export to CSV", data=display_df[cols_to_show].to_csv(index=False).encode('utf-8'), file_name=f"QESCO_Ledger_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
