import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF

# --- HELPER: Generate PDF Report ---
def generate_pdf_report(report_df, display_cols, col_config, title, agg_level, rep_df=None):
    if rep_df is None:
        rep_df = report_df

    class PDF(FPDF):
        def __init__(self):
            super().__init__('L', 'mm', 'A4')
            self.set_auto_page_break(auto=True, margin=13)

        def header(self):
            # 0.5 inch left margin = 13mm
            self.set_left_margin(13)
            self.set_right_margin(10)
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(0, 51, 102)
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, "Government of Pakistan  |  QESCO  |  Government of Balochistan", ln=True, align='C', fill=True)
            self.ln(3)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(0, 51, 102)
            self.cell(0, 10, "QESCO Government Department", ln=True, align='C')
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(0, 0, 0)
            self.cell(0, 7, f"Revenue Report - {agg_level} Summary", ln=True, align='C')
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
            self.ln(4)
            self.set_text_color(0, 0, 0)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, f"Page {self.page_no()}", align='C')

    pdf = PDF()
    pdf.add_page()
    # Set left margin for content after header
    pdf.set_left_margin(2)

    # Build table headers
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    col_widths = []
    for col in display_cols:
        if col in ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME', 'DEPARTMENT_NAME']:
            col_widths.append(46)
        else:
            col_widths.append(25)
    for i, col_name in enumerate(display_cols):
        header = col_config.get(col_name, {}).get("label", col_name) if isinstance(col_config, dict) else col_name
        pdf.cell(col_widths[i], 7, str(header), border=1, align='C', fill=True)
    pdf.ln()

    # Table rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 7)
    fill = False
    for _, row in report_df.iterrows():
        if fill:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        fill = not fill
        for i, col in enumerate(display_cols):
            val = str(row.get(col, ''))[:20]
            pdf.cell(col_widths[i], 5, val, border=1, align='C', fill=True)
        pdf.ln()

    # Totals row - use original rep_df for correct totals
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_widths[0], 7, "TOTAL", border=1, align='C', fill=True)
    for i, col in enumerate(display_cols[1:], 1):
        if col == 'Connections':
            val = str(rep_df['CONSNO'].count())[:18]
        elif col == 'Active':
            if 'PDISC' in rep_df.columns:
                val = str((rep_df['PDISC'] == 0).sum())
            else:
                val = str(rep_df['CONSNO'].count())
        elif col == 'Disconnected':
            if 'PDISC' in rep_df.columns:
                val = str((rep_df['PDISC'] > 0).sum())
            else:
                val = '0'
        elif col == 'ASSESSMENT_AMNT':
            val = f"{rep_df['ASSESSMENT_AMNT'].sum()/1e6:.2f}M"
        elif col == 'PAYMENT_NOR':
            val = f"{rep_df['PAYMENT_NOR'].sum()/1e6:.2f}M"
        elif col == 'TOTAL_CL_BAL':
            val = f"{rep_df['TOTAL_CL_BAL'].sum()/1e6:.2f}M"
        elif col == 'Recovery_%':
            total_ass = rep_df['ASSESSMENT_AMNT'].sum()
            total_pay = rep_df['PAYMENT_NOR'].sum()
            val = f"{(total_pay/total_ass*100):.1f}%" if total_ass > 0 else "0%"
        elif col == 'Accuracy_%':
            total_match = rep_df['MATCH'].sum()
            total_all = rep_df['ALL'].sum()
            val = f"{(total_match/total_all*100):.1f}%" if total_all > 0 else "0%"
        else:
            val = ''
        pdf.cell(col_widths[i], 7, val, border=1, align='C', fill=True)
    pdf.ln()

    return bytes(pdf.output())

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="QESCO | Government Department — Billing Accuracy & Payment Recovery Dashboard", layout="wide", page_icon="⚡")

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
        st.error("Password incorrect")
        return False
    return True

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_excel('data/ALL-ENRICHED-COMBINED-Cleaned.xlsx')
    # Clean numeric columns
    num_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ACCURCY', 'MATCH', 'NOT MATCH', 'ALL', 'PDISC']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    df['ARREARS'] = df['ASSESSMENT_AMNT'] - df['PAYMENT_NOR']
    df['STATUS'] = df['PDISC'].apply(lambda x: "Active" if x == 0 else "Disconnected")
    return df, datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- 4. MAIN APP ---
if check_password():
    df, sync_time = load_data()

    if df is not None:
        # --- SIDEBAR FILTERS ---
        with st.sidebar:
            st.markdown("### 🏛️ Navigation & Filters")
            s_cat = st.multiselect("Government Category", df['SOURCE'].unique(), default=df['SOURCE'].unique())
            cat_df = df[df['SOURCE'].isin(s_cat)]

            s_cir = st.multiselect("Select Circle", sorted(cat_df['CIRCLENAME'].dropna().unique()))
            div_data = cat_df[cat_df['CIRCLENAME'].isin(s_cir)] if s_cir else cat_df
            s_div = st.multiselect("Select Division", sorted(div_data['DIVNAME'].dropna().unique()))
            sub_data = div_data[div_data['DIVNAME'].isin(s_div)] if s_div else div_data
            s_sub = st.multiselect("Select Sub-Division", sorted(sub_data['SUBDIVNAME'].dropna().unique()))
            dep_data = sub_data[sub_data['SUBDIVNAME'].isin(s_sub)] if s_sub else sub_data
            s_dep = st.multiselect("Select Department", sorted(dep_data['DEPARTMENT_NAME'].dropna().unique()))

            st.divider()
            status_view = st.radio("Connection Status", ["All", "Active (0)", "Disconnected (1)"])
            st.info(f"Last Synced: {sync_time}")

        # Apply Filters
        f_df = cat_df.copy()
        if s_cir: f_df = f_df[f_df['CIRCLENAME'].isin(s_cir)]
        if s_div: f_df = f_df[f_df['DIVNAME'].isin(s_div)]
        if s_sub: f_df = f_df[f_df['SUBDIVNAME'].isin(s_sub)]
        if s_dep: f_df = f_df[f_df['DEPARTMENT_NAME'].isin(s_dep)]
        if status_view == "Active (0)": f_df = f_df[f_df['STATUS'] == "Active"]
        elif status_view == "Disconnected (1)": f_df = f_df[f_df['STATUS'] == "Disconnected"]

        # --- HEADER ---
        st.markdown("## ⚡ QESCO | Government Departments — Dashboard")
        st.divider()

        # --- KPI CARDS ---
        def format_money(val):
            if val >= 1e9: return f"Rs {val/1e9:.2f}B"
            elif val >= 1e6: return f"Rs {val/1e6:.2f}M"
            elif val >= 1e3: return f"Rs {val/1e3:.2f}K"
            else: return f"Rs {val:.0f}"

        total_ass = f_df['ASSESSMENT_AMNT'].sum()
        total_pay = f_df['PAYMENT_NOR'].sum()
        total_cl_bal = f_df['TOTAL_CL_BAL'].sum()
        total_arrears = f_df['ARREARS'].sum()
        accuracy = (f_df['MATCH'].sum() / f_df['ALL'].sum() * 100) if f_df['ALL'].sum() > 0 else 0
        collection_pct = (total_pay / total_ass * 100) if total_ass > 0 else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Assessment", format_money(total_ass))
        with kpi2:
            st.metric("Collection", format_money(total_pay))
        with kpi3:
            st.metric("Closing Bal", format_money(total_cl_bal))
        with kpi4:
            st.metric("Arrears", format_money(total_arrears))

        kpi5, kpi6, kpi7 = st.columns(3)
        with kpi5:
            st.metric("Collection %", f"{collection_pct:.1f}%")
        with kpi6:
            st.metric("Accuracy", f"{accuracy:.1f}%")
        with kpi7:
            st.metric("Records", f"{len(f_df):,}")

        st.divider()

        # --- TABS ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Revenue Overview", "🎯 Accuracy Analysis", "📈 Arrears & Closing Balance", "📋 Master Ledger", "📑 Custom Report"])

        # ===== TAB 1: REVENUE OVERVIEW =====
        with tab1:
            st.markdown("<h2 style='text-align: center; color: #003366;'>Revenue Performance Analysis</h2>", unsafe_allow_html=True)
            st.divider()

            c1, c2 = st.columns([1.6, 1], gap="large")
            with c1:
                st.markdown("### 📉 Assessment vs Recovery by Division")
                perf_data = f_df.groupby('DIVNAME')[['ASSESSMENT_AMNT', 'PAYMENT_NOR']].sum().reset_index()
                perf_data = perf_data.sort_values('ASSESSMENT_AMNT', ascending=False).head(15)
                fig = px.bar(perf_data, x='DIVNAME', y=['ASSESSMENT_AMNT', 'PAYMENT_NOR'], barmode='group',
                            color_discrete_sequence=['#0056b3', '#00d4ff'])
                fig.update_layout(height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02), plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("### 🔴 Top 10 Departments by Arrears")
                dept_arrears = f_df.groupby('DEPARTMENT_NAME')['ARREARS'].sum().nlargest(10).reset_index()
                fig_pie = px.pie(dept_arrears, values='ARREARS', names='DEPARTMENT_NAME', hole=0.4,
                               color_discrete_sequence=px.colors.qualitative.Prism)
                fig_pie.update_layout(height=350, showlegend=False, margin=dict(t=50, b=50, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("### 📊 Revenue by Circle")
            circle_data = f_df.groupby('CIRCLENAME').agg({
                'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum', 'ARREARS': 'sum'
            }).reset_index().sort_values('ASSESSMENT_AMNT', ascending=False)
            circle_data['COLLECTION%'] = (circle_data['PAYMENT_NOR'] / circle_data['ASSESSMENT_AMNT'] * 100).round(1)
            fig_circle = px.bar(circle_data, x='CIRCLENAME', y=['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'ARREARS'],
                               barmode='group', color_discrete_sequence=['#003366', '#00d4ff', '#ff6b6b'])
            fig_circle.update_layout(height=300, plot_bgcolor='white')
            st.plotly_chart(fig_circle, use_container_width=True)

            # Executive Summary Table
            st.markdown("### 📋 Executive Financial Summary (Millions)")
            exec_tab = f_df.groupby(['CIRCLENAME', 'DIVNAME']).agg({
                'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum', 'TOTAL_CL_BAL': 'sum', 'ARREARS': 'sum'
            }).reset_index().sort_values(['CIRCLENAME', 'DIVNAME'])
            exec_tab['RECOVERY_%'] = (exec_tab['PAYMENT_NOR'] / exec_tab['ASSESSMENT_AMNT'] * 100).fillna(0)

            qesco_total = pd.DataFrame({
                'CIRCLENAME': ['⭐ QESCO TOTAL'],
                'DIVNAME': [''],
                'ASSESSMENT_AMNT': [exec_tab['ASSESSMENT_AMNT'].sum()],
                'PAYMENT_NOR': [exec_tab['PAYMENT_NOR'].sum()],
                'TOTAL_CL_BAL': [exec_tab['TOTAL_CL_BAL'].sum()],
                'ARREARS': [exec_tab['ARREARS'].sum()],
                'RECOVERY_%': [(exec_tab['PAYMENT_NOR'].sum()/exec_tab['ASSESSMENT_AMNT'].sum()*100) if exec_tab['ASSESSMENT_AMNT'].sum()>0 else 0]
            })

            final_table = pd.concat([exec_tab, qesco_total], ignore_index=True)
            for c in ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ARREARS']: final_table[c] /= 1e6

            st.dataframe(final_table, use_container_width=True, hide_index=True, column_config={
                "CIRCLENAME": st.column_config.TextColumn("Circle"),
                "DIVNAME": st.column_config.TextColumn("Division"),
                "ASSESSMENT_AMNT": st.column_config.NumberColumn("Assessment (M)", format="%.2f M"),
                "PAYMENT_NOR": st.column_config.NumberColumn("Payment (M)", format="%.2f M"),
                "TOTAL_CL_BAL": st.column_config.NumberColumn("Closing (M)", format="%.2f M"),
                "ARREARS": st.column_config.NumberColumn("Arrears (M)", format="%.2f M"),
                "RECOVERY_%": st.column_config.NumberColumn("Recovery %", format="%.1f%%")
            })

        # ===== TAB 2: ACCURACY ANALYSIS =====
        with tab2:
            st.markdown("<h2 style='text-align: center; color: #b22222;'>🎯 Accuracy Analysis</h2>", unsafe_allow_html=True)
            st.divider()

            # KPI cards for accuracy
            acc_m1, acc_m2, acc_m3, acc_m4 = st.columns(4)
            match_sum = f_df['MATCH'].sum()
            not_match_sum = f_df['NOT MATCH'].sum()
            all_sum = f_df['ALL'].sum()

            with acc_m1:
                st.metric("Accuracy %", f"{(match_sum/all_sum*100) if all_sum > 0 else 0:.1f}%")
            with acc_m2:
                st.metric("Match Count", f"{match_sum:,.0f}")
            with acc_m3:
                st.metric("Not Match Count", f"{not_match_sum:,.0f}")
            with acc_m4:
                st.metric("Total Records", f"{all_sum:,.0f}")

            c1, c2 = st.columns([1, 1.2], gap="large")
            with c1:
                st.markdown("#### 🌡️ Accuracy Heatmap by Location")
                h_axis = 'SUBDIVNAME' if s_sub else ('DIVNAME' if s_div else 'CIRCLENAME')
                heat_data = f_df.groupby([h_axis, 'STATUS'])['ACCURCY'].mean().unstack().fillna(0)
                fig_heat = px.imshow(heat_data, text_auto=".1f", color_continuous_scale='RdYlGn')
                fig_heat.update_layout(height=400)
                st.plotly_chart(fig_heat, use_container_width=True)

            with c2:
                st.markdown("#### 📊 Department Accuracy Ranking")
                dept_acc = f_df.groupby('DEPARTMENT_NAME')['ACCURCY'].mean().sort_values(ascending=True).reset_index()
                dept_acc = dept_acc[dept_acc['ACCURCY'] > 0].tail(15)
                fig_rank = px.bar(dept_acc, y='DEPARTMENT_NAME', x='ACCURCY', orientation='h',
                                 color='ACCURCY', color_continuous_scale='RdYlGn',
                                 text=dept_acc['ACCURCY'].apply(lambda x: f'{x:.1f}%'))
                fig_rank.add_vline(x=100, line_dash="dot", line_color="black")
                fig_rank.update_layout(height=400, xaxis_range=[0, 120], plot_bgcolor='white')
                st.plotly_chart(fig_rank, use_container_width=True)

            st.divider()
            c1, c2 = st.columns(2)
            dept_acc_sorted = dept_acc.sort_values('ACCURCY')
            with c1:
                st.error("📉 **Bottom 5 Performers**")
                st.table(dept_acc_sorted.head(5).set_index('DEPARTMENT_NAME'))
            with c2:
                st.success("📈 **Top 5 Performers**")
                st.table(dept_acc_sorted.tail(5).iloc[::-1].set_index('DEPARTMENT_NAME'))

        # ===== TAB 3: ARREARS & CLOSING BALANCE =====
        with tab3:
            st.markdown("<h2 style='text-align: center; color: #8b0000;'>📈 Arrears & Closing Balance Analysis</h2>", unsafe_allow_html=True)
            st.divider()

            # Arrears KPIs
            ar1, ar2, ar3, ar4 = st.columns(4)
            arrears_total = f_df['ARREARS'].sum()
            arrears_count = (f_df['ARREARS'] > 0).sum()
            avg_arrears = f_df[f_df['ARREARS'] > 0]['ARREARS'].mean()
            max_arrears = f_df['ARREARS'].max()

            with ar1:
                st.metric("Total Arrears", format_money(arrears_total))
            with ar2:
                st.metric("Accounts in Arrears", f"{arrears_count:,}")
            with ar3:
                st.metric("Avg Arrears", format_money(avg_arrears))
            with ar4:
                st.metric("Max Arrear", format_money(max_arrears))

            c1, c2 = st.columns([1.6, 1], gap="large")
            with c1:
                st.markdown("#### 📉 Arrears by Division")
                div_arrears = f_df.groupby('DIVNAME')['ARREARS'].sum().nlargest(15).reset_index()
                fig_ar_div = px.bar(div_arrears, x='DIVNAME', y='ARREARS', color='ARREARS',
                                   color_continuous_scale='Reds_r', text=div_arrears['ARREARS'].apply(lambda x: f'{x/1e6:.1f}M'))
                fig_ar_div.update_layout(height=350, plot_bgcolor='white')
                st.plotly_chart(fig_ar_div, use_container_width=True)

            with c2:
                st.markdown("#### 🔴 Top 10 Departments by Arrears")
                dept_arrears = f_df.groupby('DEPARTMENT_NAME')['ARREARS'].sum().nlargest(10).reset_index()
                fig_ar_dept = px.pie(dept_arrears, values='ARREARS', names='DEPARTMENT_NAME', hole=0.4,
                                    color_discrete_sequence=px.colors.qualitative.Set3)
                fig_ar_dept.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_ar_dept, use_container_width=True)

            # Closing Balance KPIs
            st.divider()
            st.markdown("#### 💰 Closing Balance Analysis")
            cl1, cl2, cl3, cl4 = st.columns(4)
            total_cl = f_df['TOTAL_CL_BAL'].sum()
            avg_cl = f_df['TOTAL_CL_BAL'].mean()
            max_cl = f_df['TOTAL_CL_BAL'].max()

            with cl1:
                st.metric("Total Closing", format_money(total_cl))
            with cl2:
                st.metric("Avg Closing", format_money(avg_cl))
            with cl3:
                st.metric("Max Closing", format_money(max_cl))
            with cl4:
                st.metric("Active Accounts", f"{(f_df['STATUS']=='Active').sum():,}")

            st.markdown("**Closing Balance by Department**")
            cl_dept = f_df.groupby('DEPARTMENT_NAME').agg({
                'TOTAL_CL_BAL': 'sum', 'ASSESSMENT_AMNT': 'sum'
            }).reset_index()
            cl_dept['CL_BAL_PCT'] = (cl_dept['TOTAL_CL_BAL'] / cl_dept['ASSESSMENT_AMNT'] * 100).round(1)
            cl_dept = cl_dept.sort_values('TOTAL_CL_BAL', ascending=False).head(20)
            cl_dept['TOTAL_CL_BAL'] = cl_dept['TOTAL_CL_BAL'].apply(lambda x: f"{x/1e6:.2f}M")
            st.dataframe(cl_dept, use_container_width=True, hide_index=True, column_config={
                "DEPARTMENT_NAME": st.column_config.TextColumn("Department"),
                "TOTAL_CL_BAL": st.column_config.TextColumn("Closing Balance"),
                "ASSESSMENT_AMNT": st.column_config.NumberColumn("Assessment", format="%.0f"),
                "CL_BAL_PCT": st.column_config.NumberColumn("Closing %", format="%.1f%%")
            })

            # Arrears by Circle/SubDivision
            st.markdown("**Arrears by Location**")
            loc_tabs = st.tabs(["By Circle", "By Division", "By Sub Division"])
            with loc_tabs[0]:
                ar_circle = f_df.groupby('CIRCLENAME').agg({'ARREARS': 'sum', 'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum'}).reset_index()
                ar_circle['ARREARS_PCT'] = (ar_circle['ARREARS'] / ar_circle['ASSESSMENT_AMNT'] * 100).round(1)
                ar_circle = ar_circle.sort_values('ARREARS', ascending=False)
                st.dataframe(ar_circle, use_container_width=True)
            with loc_tabs[1]:
                ar_div = f_df.groupby('DIVNAME').agg({'ARREARS': 'sum', 'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum'}).reset_index()
                ar_div['ARREARS_PCT'] = (ar_div['ARREARS'] / ar_div['ASSESSMENT_AMNT'] * 100).round(1)
                ar_div = ar_div.sort_values('ARREARS', ascending=False)
                st.dataframe(ar_div, use_container_width=True)
            with loc_tabs[2]:
                ar_sub = f_df.groupby(['SUBDIVNAME', 'SDNAME']).agg({'ARREARS': 'sum', 'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum'}).reset_index()
                ar_sub['ARREARS_PCT'] = (ar_sub['ARREARS'] / ar_sub['ASSESSMENT_AMNT'] * 100).round(1)
                ar_sub = ar_sub.sort_values('ARREARS', ascending=False)
                st.dataframe(ar_sub, use_container_width=True)

        # ===== TAB 4: MASTER LEDGER =====
        with tab4:
            st.markdown("### 📋 Detailed Revenue Ledger")
            identity_cols = ['CONSNO', 'NAME', 'DEPT_CODE', 'DEPARTMENT_NAME', 'SOURCE', 'STATUS']
            revenue_cols = ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL', 'ARREARS', 'ACCURCY']
            location_cols = ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']
            cols_to_show = identity_cols + revenue_cols + location_cols

            search_query = st.text_input("🔍 Search by Name, Consumer No, or Department Code")

            display_df = f_df.copy()
            if search_query:
                display_df = f_df[
                    f_df['NAME'].str.contains(search_query, case=False, na=False) |
                    f_df['CONSNO'].astype(str).str.contains(search_query, na=False) |
                    f_df['DEPT_CODE'].astype(str).str.contains(search_query, na=False)
                ]

            st.dataframe(display_df[cols_to_show], use_container_width=True, height=600, column_config={
                "ASSESSMENT_AMNT": st.column_config.NumberColumn("Assessment", format="Rs %,.0f"),
                "PAYMENT_NOR": st.column_config.NumberColumn("Payment", format="Rs %,.0f"),
                "TOTAL_CL_BAL": st.column_config.NumberColumn("Closing Balance", format="Rs %,.0f"),
                "ARREARS": st.column_config.NumberColumn("Arrears", format="Rs %,.0f"),
                "ACCURCY": st.column_config.ProgressColumn("Accuracy %", min_value=0, max_value=100)
            })

            st.download_button(label="📥 Export to CSV", data=display_df[cols_to_show].to_csv(index=False).encode('utf-8'),
                             file_name=f"QESCO_Ledger_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

        # ===== TAB 5: CUSTOM REPORT =====
        with tab5:
            st.markdown("<h2 style='text-align: center; color: #003366;'>📑 Customizable Report</h2>", unsafe_allow_html=True)
            st.divider()

            # Aggregation level selector
            agg_level = st.radio("Aggregation Level", ["Circle", "Division", "Sub Division", "Department", "Circle+Dept"], horizontal=True)

            # Multi-select filters for report (cascading based on aggregation level)
            st.markdown("#### 🔍 Filter Report Data")
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

            with filter_col1:
                rep_circles = st.multiselect("Circle(s)", options=sorted(f_df['CIRCLENAME'].dropna().unique()), default=[], key="rep2_cir")
            with filter_col2:
                cir_df = f_df[f_df['CIRCLENAME'].isin(rep_circles)] if rep_circles else f_df
                rep_divisions = st.multiselect("Division(s)", options=sorted(cir_df['DIVNAME'].dropna().unique()), default=[], key="rep2_div")
            with filter_col3:
                div_df = cir_df[cir_df['DIVNAME'].isin(rep_divisions)] if rep_divisions else cir_df
                if agg_level in ["Circle", "Division"]:
                    rep_subdivisions = st.multiselect("Sub Division(s)", options=[], default=[], key="rep2_sub")
                else:
                    rep_subdivisions = st.multiselect("Sub Division(s)", options=sorted(div_df['SUBDIVNAME'].dropna().unique()), default=[], key="rep2_sub")
            with filter_col4:
                sub_df = div_df[div_df['SUBDIVNAME'].isin(rep_subdivisions)] if rep_subdivisions else div_df
                if agg_level == "Circle":
                    rep_departments = st.multiselect("Department(s)", options=sorted(cir_df['DEPARTMENT_NAME'].dropna().unique()), default=[], key="rep2_dep")
                elif agg_level == "Division":
                    rep_departments = st.multiselect("Department(s)", options=sorted(div_df['DEPARTMENT_NAME'].dropna().unique()), default=[], key="rep2_dep")
                elif agg_level == "Sub Division":
                    rep_departments = st.multiselect("Department(s)", options=sorted(sub_df['DEPARTMENT_NAME'].dropna().unique()), default=[], key="rep2_dep")
                else:
                    rep_departments = st.multiselect("Department(s)", options=sorted(sub_df['DEPARTMENT_NAME'].dropna().unique()), default=[], key="rep2_dep")

            # Apply filters to f_df for report
            rep_df = f_df.copy()
            if rep_circles: rep_df = rep_df[rep_df['CIRCLENAME'].isin(rep_circles)]
            if rep_divisions: rep_df = rep_df[rep_df['DIVNAME'].isin(rep_divisions)]
            if rep_subdivisions: rep_df = rep_df[rep_df['SUBDIVNAME'].isin(rep_subdivisions)]
            if rep_departments: rep_df = rep_df[rep_df['DEPARTMENT_NAME'].isin(rep_departments)]

            # Build report based on aggregation level
            if agg_level == "Circle":
                grp_cols = ['CIRCLENAME']
                grp_name = "Circle"
            elif agg_level == "Division":
                grp_cols = ['CIRCLENAME', 'DIVNAME']
                grp_name = "Division"
            elif agg_level == "Sub Division":
                grp_cols = ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']
                grp_name = "Sub Division"
            elif agg_level == "Department":
                grp_cols = ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME', 'DEPARTMENT_NAME']
                grp_name = "Department"
            else:  # Circle+Dept - simple circle-wise department summary
                grp_cols = ['CIRCLENAME', 'DEPARTMENT_NAME']
                grp_name = "Circle+Department"

            # Build aggregation using filtered data
            agg_dict = {'CONSNO': 'count', 'ASSESSMENT_AMNT': 'sum', 'PAYMENT_NOR': 'sum', 'TOTAL_CL_BAL': 'sum', 'MATCH': 'sum', 'ALL': 'sum'}
            if agg_level in ["Department", "Circle+Dept"]:
                agg_dict['PDISC'] = 'sum'

            report_df = rep_df.groupby(grp_cols).agg(agg_dict).reset_index()

            # Rename columns
            report_df.rename(columns={'CONSNO': 'Connections', 'MATCH': 'Match', 'ALL': 'Total'}, inplace=True)
            if 'PDISC' in report_df.columns:
                report_df.rename(columns={'PDISC': 'Disconnected'}, inplace=True)
                report_df['Active'] = report_df['Connections'] - report_df['Disconnected']
            else:
                report_df['Active'] = report_df['Connections']  # No disconnected data available
            report_df['Recovery_%'] = (report_df['PAYMENT_NOR'] / report_df['ASSESSMENT_AMNT'] * 100).round(1)
            report_df['Accuracy_%'] = (report_df['Match'] / report_df['Total'] * 100).round(1)

            # Apply format
            for c in ['ASSESSMENT_AMNT', 'PAYMENT_NOR', 'TOTAL_CL_BAL']:
                report_df[c] = report_df[c].apply(lambda x: f"{x/1e6:.2f}M")

            st.divider()
            # Column selector
            st.markdown("#### 🔧 Select Columns to Display")
            col_opts = st.columns(4)
            with col_opts[0]:
                show_circle = st.checkbox("Circle", value=True)
            with col_opts[1]:
                show_division = st.checkbox("Division", value=True)
            with col_opts[2]:
                show_subdiv = st.checkbox("Sub Division", value=True)
            with col_opts[3]:
                show_dept = st.checkbox("Department", value=True)

            col_opts2 = st.columns(4)
            with col_opts2[0]:
                show_connections = st.checkbox("Connections", value=True)
            with col_opts2[1]:
                show_active = st.checkbox("Active Count", value=True)
            with col_opts2[2]:
                show_pdisc = st.checkbox("Disconnected Count", value=True)
            with col_opts2[3]:
                show_billing = st.checkbox("Billing", value=True)

            col_opts3 = st.columns(4)
            with col_opts3[0]:
                show_payment = st.checkbox("Payment", value=True)
            with col_opts3[1]:
                show_recovery = st.checkbox("Recovery %", value=True)
            with col_opts3[2]:
                show_accuracy = st.checkbox("Accuracy", value=True)
            with col_opts3[3]:
                show_closing = st.checkbox("Closing Balance", value=True)

            st.divider()

            # Re-build display columns based on checkboxes
            display_cols = []
            col_config = {}

            if show_circle and 'CIRCLENAME' in report_df.columns:
                display_cols.append('CIRCLENAME')
                col_config['CIRCLENAME'] = st.column_config.TextColumn("Circle")
            if show_division and 'DIVNAME' in report_df.columns:
                display_cols.append('DIVNAME')
                col_config['DIVNAME'] = st.column_config.TextColumn("Division")
            if show_subdiv and 'SUBDIVNAME' in report_df.columns:
                display_cols.append('SUBDIVNAME')
                col_config['SUBDIVNAME'] = st.column_config.TextColumn("Sub Division")
            if show_dept and 'DEPARTMENT_NAME' in report_df.columns:
                display_cols.append('DEPARTMENT_NAME')
                col_config['DEPARTMENT_NAME'] = st.column_config.TextColumn("Department")

            if show_connections:
                display_cols.append('Connections')
                col_config['Connections'] = st.column_config.NumberColumn("Connections", format="%d")
            if show_active and 'Active' in report_df.columns:
                display_cols.append('Active')
                col_config['Active'] = st.column_config.NumberColumn("Active", format="%d")
            if show_pdisc and 'Disconnected' in report_df.columns:
                display_cols.append('Disconnected')
                col_config['Disconnected'] = st.column_config.NumberColumn("Disconnected", format="%d")

            if show_billing:
                display_cols.append('ASSESSMENT_AMNT')
                col_config['ASSESSMENT_AMNT'] = st.column_config.TextColumn("Billing (M)")
            if show_payment:
                display_cols.append('PAYMENT_NOR')
                col_config['PAYMENT_NOR'] = st.column_config.TextColumn("Payment (M)")
            if show_recovery:
                display_cols.append('Recovery_%')
                col_config['Recovery_%'] = st.column_config.NumberColumn("Recovery %", format="%.1f%%")
            if show_accuracy:
                display_cols.append('Accuracy_%')
                col_config['Accuracy_%'] = st.column_config.NumberColumn("Accuracy %", format="%.1f%%")
            if show_closing:
                display_cols.append('TOTAL_CL_BAL')
                col_config['TOTAL_CL_BAL'] = st.column_config.TextColumn("Closing (M)")

            # Build totals row data
            total_display = {
                'Connections': report_df['Connections'].sum() if 'Connections' in display_cols else None,
                'Active': report_df['Active'].sum() if 'Active' in display_cols and 'Active' in report_df.columns else None,
                'Disconnected': report_df['Disconnected'].sum() if 'Disconnected' in report_df.columns else None,
                'ASSESSMENT_AMNT': f"{rep_df['ASSESSMENT_AMNT'].sum()/1e6:.2f}M",
                'PAYMENT_NOR': f"{rep_df['PAYMENT_NOR'].sum()/1e6:.2f}M",
                'Recovery_%': f"{(rep_df['PAYMENT_NOR'].sum()/rep_df['ASSESSMENT_AMNT'].sum()*100):.1f}%",
                'Accuracy_%': f"{(rep_df['MATCH'].sum()/rep_df['ALL'].sum()*100):.1f}%",
                'TOTAL_CL_BAL': f"{rep_df['TOTAL_CL_BAL'].sum()/1e6:.2f}M"
            }
            if show_circle: total_display['CIRCLENAME'] = '⭐ TOTAL'
            if show_division: total_display['DIVNAME'] = ''
            if show_subdiv: total_display['SUBDIVNAME'] = ''
            if show_dept: total_display['DEPARTMENT_NAME'] = ''

            # Show report with styled totals row
            if display_cols:
                st.markdown(f"#### 📊 Report by {grp_name}")
                st.dataframe(report_df[display_cols], use_container_width=True, hide_index=True, column_config=col_config)

                # Display totals row with distinct styling
                st.markdown("**⭐ Total Row**")
                total_df = pd.DataFrame([total_display])
                st.dataframe(total_df[display_cols], use_container_width=True, hide_index=True, column_config=col_config)

                st.divider()
                # Export buttons
                st.markdown("#### 📥 Export Options")
                export_col1, export_col2 = st.columns(2)

                with export_col1:
                    csv_data = report_df[display_cols].to_csv(index=False).encode('utf-8')
                    st.download_button(label="📥 Export to CSV", data=csv_data,
                                     file_name=f"QESCO_Report_{agg_level}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

                with export_col2:
                    if st.button("📄 Generate PDF"):
                        pdf_bytes = generate_pdf_report(report_df, display_cols, col_config, "QESCO Report", agg_level, rep_df)
                        st.session_state['pdf_data'] = pdf_bytes

                    if 'pdf_data' in st.session_state and st.session_state['pdf_data'] is not None:
                        st.download_button(label="📄 Download PDF", data=st.session_state['pdf_data'],
                                         file_name=f"QESCO_Report_{agg_level}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
                        # Clear after display
                        st.session_state['pdf_data'] = None
            else:
                st.warning("Please select at least one column to display.")

