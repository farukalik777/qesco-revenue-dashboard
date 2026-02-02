import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "Qesco@786":  # Set your password here
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Enter Password to Access QESCO Dashboard", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.text_input(
            "Enter Password to Access QESCO Dashboard", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# --- MAIN APP LOGIC ---
if check_password():
    # ALL YOUR EXISTING CODE GOES INSIDE THIS IF STATEMENT
    st.success("Access Granted")
    
    # Place your load_vibrant_data(), Header, Metrics, and Tabs here...
	# 1. PAGE CONFIGURATION
		st.set_page_config(page_title="QESCO (Provincial  Govt Dept Dashboard)", layout="wide", page_icon="🏛️")

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
	    st.markdown("## ⚡ QESCO|Provincial Government Departments DashBoard")
	    st.divider()

	# We create 6 columns to fit the new metrics comfortably
	    m1, m2, m3, m4, m5, m6 = st.columns(6)
	
	# 1. Calculate Total Receivables Label
	    trec = f_df['TOTAL_CL_BAL'].sum()
	    rec_label = f"{trec/1e9:.2f}B" if trec >= 1e9 else f"{trec/1e6:.2f}M"

	# 2. Calculate Payment Metrics
	    total_payment = f_df['PAYMENT_NOR'].sum()
	    total_assessment = f_df['ASSESSMENT_AMNT'].sum()
	
	# 3. Calculate Percentage of Payment (Collection Efficiency)
	# Using a safe division to avoid errors if assessment is zero
	    pay_pct = (total_payment / total_assessment * 100) if total_assessment > 0 else 0
	
	# 4. Display Metrics
	    m1.metric("Total Receivables", rec_label)
	    m2.metric("Billing Accuracy", f"{f_df['ACCURCY'].mean():.1f}%")
	    m3.metric("Current Assessment", f"{total_assessment/1e6:.2f}M")
	    m4.metric("Current Payment", f"{total_payment/1e6:.2f}M")
	    m5.metric("Payment %", f"{pay_pct:.1f}%") # Percentage of Payment
	    m6.metric("Selected Records", f"{len(f_df):,}")
   
	# --- TABS (Enhanced Visibility & Prominence) ---
	    tab1, tab2, tab3 = st.tabs(["📊 Revenue Insights", "🎯 Accuracy Analysis", "📋 Master Ledger"])
    
	    with tab1:
	        # Using a container with a subtle background to make charts "pop"
	        with st.container():
	            st.markdown("<h2 style='text-align: center; color: #003366;'>Revenue Performance Analysis</h2>", unsafe_allow_html=True)
	            st.divider()
	            
	            # Increased column gap for better separation
	            c1, c2 = st.columns([1.6, 1], gap="large")
	            
	            with c1:
	                st.markdown("### 📉 Assessment vs Recovery")
	                # Aggregated view for maximum clarity
	                perf_data = f_df.groupby('DIVNAME')[['ASSESSMENT_AMNT', 'PAYMENT_NOR']].sum().reset_index()
	                
	                fig = px.bar(
	                    perf_data, 
	                    x='DIVNAME', 
	                    y=['ASSESSMENT_AMNT', 'PAYMENT_NOR'], 
	                    barmode='group',
	                    color_discrete_sequence=['#0056b3', '#00d4ff'] # High contrast blues
	                )
	                
	                fig.update_layout(
	                    height=300, # Increased height
	                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14)),
	                    xaxis=dict(tickangle=-45, title_font=dict(size=16), tickfont=dict(size=12)),
	                    yaxis=dict(title="Amount (PKR)", title_font=dict(size=16), gridcolor='#f0f0f0'),
	                    plot_bgcolor='white'
	                )
	                st.plotly_chart(fig, use_container_width=True)
                
	            with c2:
	                st.markdown("###  Top 10  Defaulter  Departments ")
	                dept_debt = f_df.groupby('DEPARTMENT_NAME')['TOTAL_CL_BAL'].sum().nlargest(10).reset_index()
	                
	                # Donut chart with larger center for better label visibility
	                fig_pie = px.pie(
	                    dept_debt, 
	                    values='TOTAL_CL_BAL', 
	                    names='DEPARTMENT_NAME', 
	                    hole=0.4,
	                    color_discrete_sequence=px.colors.qualitative.Prism
	                )
	                
	                fig_pie.update_traces(
	                    textposition='outside', 
	                    textinfo='percent+label',
	                    textfont_size=8,
	                    marker=dict(line=dict(color='#FFFFFF', width=2))
	                )
	                
	                fig_pie.update_layout(
	                    height=300,
	                    showlegend=False, # Removed legend to give chart maximum screen space
	                    margin=dict(t=50, b=50, l=10, r=10)
	                )
	                st.plotly_chart(fig_pie, use_container_width=True)

    
	    with tab2:
	        st.markdown("<h2 style='text-align: center; color: #b22222;'>🎯 Accuracy  Analysis</h2>", unsafe_allow_html=True)
	        st.divider()
	        
	        # Determine drill-down level
	        h_axis = 'SUBDIVNAME' if s_sub else ('DIVNAME' if s_div else 'CIRCLENAME')
	        
	        col_left, col_right = st.columns([1, 1.2], gap="large")
	        
	        with col_left:
	            st.markdown(f"#### 🌡️ {h_axis} Heatmap")
	            heat_data = f_df.groupby([h_axis, 'STATUS'])['ACCURCY'].mean().unstack().fillna(0)
	            
	            # Use 'aspect="auto"' to let it fill the column height properly
	            fig_heat = px.imshow(
	                heat_data, 
	                text_auto=".1f", 
	                color_continuous_scale='RdYlGn',
	                labels=dict(color="Acc %")
	            )
	            fig_heat.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
	            st.plotly_chart(fig_heat, use_container_width=True)
	            
	        with col_right:
	            st.markdown("#### 📊 Department Accuracy Ranking")
	            # Sorting so the biggest problems (lowest accuracy) are at the top
	            dept_acc = f_df.groupby('DEPARTMENT_NAME')['ACCURCY'].mean().sort_values(ascending=True).reset_index()
            
	            # LIMITING THE VIEW: We show the Top/Bottom or use a scrollable height
	            fig_rank = px.bar(
	                dept_acc, 
	                y='DEPARTMENT_NAME', 
	                x='ACCURCY',
	                orientation='h',
	                color='ACCURCY',
	                color_continuous_scale='RdYlGn',
	                text=dept_acc['ACCURCY'].apply(lambda x: f'{x:.1f}%')
	            )
            
	            fig_rank.add_vline(x=100, line_dash="dot", line_color="black", annotation_text="Target")
	            
	            fig_rank.update_traces(textposition='outside', cliponaxis=False)
	            
	            # FIX: We set a fixed height (e.g., 500px) instead of a dynamic one.
	            # This forces Streamlit to create a scrollbar if the list is too long.
	            fig_rank.update_layout(
	                height=500, 
	                xaxis_title="Avg Accuracy %",
	                yaxis_title="",
	                xaxis_range=[0, 120],
	                margin=dict(l=10, r=50, t=10, b=10),
	                plot_bgcolor='white'
	            )
	            st.plotly_chart(fig_rank, use_container_width=True)

	        # OPTIONAL: Add a small "Top 5 / Bottom 5" summary table for quick visibility
	        st.divider()
	        st.markdown("#### ⚡ Accuracy Extremes")
	        low_acc = dept_acc.head(5)
	        high_acc = dept_acc.tail(5).iloc[::-1] # Reverse to show 100% first
	        
	        c1, c2 = st.columns(2)
	        c1.error("📉 **Bottom 5 Performers**")
	        c1.table(low_acc.set_index('DEPARTMENT_NAME'))
	        
	        c2.success("📈 **Top 5 Performers**")
	        c2.table(high_acc.set_index('DEPARTMENT_NAME'))
	    with tab3:
	        st.markdown("### 📋 Detailed Revenue Ledger")
	        
	        # 1. ORGANIZE COLUMNS BY YOUR REQUESTED GROUPS
	        identity_cols = ['REF_ID', 'NAME', 'ADDR1', 'ADDR2', 'TARIFFCODE', 'SAN_LOAD', 'STATUS', 'DEPARTMENT_NAME']
	        account_cols = ['BILLMONTH']
	        revenue_cols = ['OP_BAL', 'ASSESSMENT_AMNT', 'PAYMENT_NOR', 'ADJUSTOR', 'SURLEVIED']
	        result_cols = ['TOTAL_CL_BAL', 'ACCURCY']
	        location_cols = ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME']

	        # Combine into the final order
	        final_col_order = identity_cols + account_cols + revenue_cols + result_cols + location_cols
	        
	        # Ensure only existing columns are used
	        cols_to_show = [c for c in final_col_order if c in f_df.columns]

	        # 2. SEARCH & FILTER SECTION
	        search_query = st.text_input("🔍 Search by Name, Address, or 15-Digit Reference ID")
	        
	        if search_query:
	            display_df = f_df[
	                f_df['NAME'].str.contains(search_query, case=False, na=False) | 
	                f_df['REF_ID'].str.contains(search_query, na=False) |
	                f_df['ADDR1'].str.contains(search_query, case=False, na=False)
	            ]
	        else:
	            display_df = f_df

	        # 3. PROMINENT DATA TABLE (Fixed AttributeError)
	        st.dataframe(
	            display_df[cols_to_show],
	            use_container_width=True,
	            height=650,
	            column_config={
	                "REF_ID": st.column_config.TextColumn("Reference ID"),
	                "NAME": st.column_config.TextColumn("Consumer Name", width="medium"),
	                "TOTAL_CL_BAL": st.column_config.NumberColumn("Closing Balance", format="Rs %d"),
	                "ASSESSMENT_AMNT": st.column_config.NumberColumn("Assessment", format="Rs %d"),
	                "PAYMENT_NOR": st.column_config.NumberColumn("Payment", format="Rs %d"),
	                "ACCURCY": st.column_config.ProgressColumn("Accuracy %", min_value=0, max_value=100),
	                "STATUS": st.column_config.TextColumn("Status") # Fixed: Changed from SelectColumn to TextColumn
	            }
	        )

	        # 4. EXPORT OPTION
	        st.download_button(
	            label="📥 Export This View to CSV",
	            data=display_df[cols_to_show].to_csv(index=False).encode('utf-8'),
	            file_name=f"QESCO_Ledger_{datetime.now().strftime('%Y%m%d')}.csv",
	            mime="text/csv",
	        )
	else:
	
	    st.warning("🔄 System Initializing... Please verify data connections.")
	
	
	
	

