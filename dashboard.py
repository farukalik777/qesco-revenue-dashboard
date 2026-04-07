import streamlit as st
import pandas as pd

st.set_page_config(page_title="QESCO Revenue Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel('data/ALL-ENRICHED-COMBINED-Cleaned.xlsx')
    return df

df = load_data()

st.title("QESCO Revenue Dashboard - February 2026")

# ---- KPI CARDS ----
col1, col2, col3, col4 = st.columns(4)
total_assessment = df['ASSESSMENT_AMNT'].sum()
total_payment = df['PAYMENT_NOR'].sum()
total_closing = df['TOTAL_CL_BAL'].sum()
collection_pct = (total_payment / total_assessment * 100) if total_assessment > 0 else 0

with col1:
    st.metric("Total Assessment", f"PKR {total_assessment/1e6:.1f}M")
with col2:
    st.metric("Total Collection", f"PKR {total_payment/1e6:.1f}M")
with col3:
    st.metric("Total Closing Balance", f"PKR {total_closing/1e6:.1f}M")
with col4:
    st.metric("Collection %", f"{collection_pct:.1f}%")

st.divider()

# ---- FILTERS ----
st.subheader("Filters")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    selected_circle = st.selectbox("Circle", ["All"] + sorted(df['CIRCLENAME'].dropna().unique().tolist()))

with filter_col2:
    if selected_circle != "All":
        divisions = df[df['CIRCLENAME'] == selected_circle]['DIVNAME'].dropna().unique()
    else:
        divisions = df['DIVNAME'].dropna().unique()
    selected_division = st.selectbox("Division", ["All"] + sorted(divisions.tolist()))

with filter_col3:
    if selected_division != "All":
        subdivs = df[df['DIVNAME'] == selected_division]['SUBDIVNAME'].dropna().unique()
    else:
        subdivs = df['SUBDIVNAME'].dropna().unique()
    selected_subdiv = st.selectbox("Sub Division", ["All"] + sorted(subdivs.tolist()))

with filter_col4:
    if selected_subdiv != "All":
        depts = df[df['SUBDIVNAME'] == selected_subdiv]['DEPARTMENT_NAME'].dropna().unique()
    elif selected_division != "All":
        depts = df[df['DIVNAME'] == selected_division]['DEPARTMENT_NAME'].dropna().unique()
    elif selected_circle != "All":
        depts = df[df['CIRCLENAME'] == selected_circle]['DEPARTMENT_NAME'].dropna().unique()
    else:
        depts = df['DEPARTMENT_NAME'].dropna().unique()
    selected_dept = st.selectbox("Department", ["All"] + sorted(depts.tolist()))

# Apply filters
filtered = df.copy()
if selected_circle != "All":
    filtered = filtered[filtered['CIRCLENAME'] == selected_circle]
if selected_division != "All":
    filtered = filtered[filtered['DIVNAME'] == selected_division]
if selected_subdiv != "All":
    filtered = filtered[filtered['SUBDIVNAME'] == selected_subdiv]
if selected_dept != "All":
    filtered = filtered[filtered['DEPARTMENT_NAME'] == selected_dept]

st.divider()

# ---- ACCURACY ANALYSIS ----
st.subheader("Accuracy Analysis")

acc_col1, acc_col2, acc_col3, acc_col4 = st.columns(4)

total_acc = filtered['ACCURCY'].sum()
total_all = filtered['ALL'].sum()
match_count = filtered['MATCH'].sum()
not_match_count = filtered['NOT MATCH'].sum()
accuracy_pct = (match_count / total_all * 100) if total_all > 0 else 0

with acc_col1:
    st.metric("Accuracy %", f"{accuracy_pct:.1f}%")
with acc_col2:
    st.metric("Match Count", f"{match_count:,.0f}")
with acc_col3:
    st.metric("Not Match Count", f"{not_match_count:,.0f}")
with acc_col4:
    st.metric("Total Records", f"{total_all:,.0f}")

# Accuracy by Department
st.markdown("**Accuracy by Department**")
acc_dept = filtered.groupby('DEPARTMENT_NAME').agg({
    'MATCH': 'sum',
    'NOT MATCH': 'sum',
    'ALL': 'sum'
}).reset_index()
acc_dept['ACCURACY%'] = (acc_dept['MATCH'] / acc_dept['ALL'] * 100).round(1)
acc_dept = acc_dept.sort_values('ALL', ascending=False).head(15)
st.dataframe(acc_dept, use_container_width=True)

st.divider()

# ---- CLOSING BALANCE ANALYSIS ----
st.subheader("Closing Balance Analysis")

cl_col1, cl_col2, cl_col3, cl_col4 = st.columns(4)
total_cl_bal = filtered['TOTAL_CL_BAL'].sum()
avg_cl_bal = filtered['TOTAL_CL_BAL'].mean()
max_cl_bal = filtered['TOTAL_CL_BAL'].max()
min_cl_bal = filtered['TOTAL_CL_BAL'].min()

with cl_col1:
    st.metric("Total Closing Balance", f"PKR {total_cl_bal/1e6:.1f}M")
with cl_col2:
    st.metric("Average Closing Bal", f"PKR {avg_cl_bal:,.0f}")
with cl_col3:
    st.metric("Max Closing Bal", f"PKR {max_cl_bal:,.0f}")
with cl_col4:
    st.metric("Min Closing Bal", f"PKR {min_cl_bal:,.0f}")

# Closing Balance by Department
st.markdown("**Closing Balance by Department**")
cl_dept = filtered.groupby('DEPARTMENT_NAME').agg({
    'TOTAL_CL_BAL': 'sum',
    'ASSESSMENT_AMNT': 'sum'
}).reset_index()
cl_dept['CL_BAL_PCT'] = (cl_dept['TOTAL_CL_BAL'] / cl_dept['ASSESSMENT_AMNT'] * 100).round(1)
cl_dept = cl_dept.sort_values('TOTAL_CL_BAL', ascending=False).head(15)
st.dataframe(cl_dept, use_container_width=True)

st.divider()

# ---- ARREARS ANALYSIS ----
st.subheader("Arrears Analysis")

ar_col1, ar_col2, ar_col3, ar_col4 = st.columns(4)

# Arrears = Assessment - Payment collected
arrears = filtered['ASSESSMENT_AMNT'] - filtered['PAYMENT_NOR']
arrears_total = arrears.sum()
arrears_count = (arrears > 0).sum()
avg_arrears = arrears[arrears > 0].mean() if arrears_count > 0 else 0
max_arrears = arrears.max()

with ar_col1:
    st.metric("Total Arrears", f"PKR {arrears_total/1e6:.1f}M")
with ar_col2:
    st.metric("Accounts in Arrears", f"{arrears_count:,}")
with ar_col3:
    st.metric("Avg Arrears per Account", f"PKR {avg_arrears:,.0f}")
with ar_col4:
    st.metric("Max Single Arrear", f"PKR {max_arrears:,.0f}")

# Arrears by Department
st.markdown("**Arrears by Department**")
ar_dept = filtered.groupby('DEPARTMENT_NAME').agg({
    'ASSESSMENT_AMNT': 'sum',
    'PAYMENT_NOR': 'sum'
}).reset_index()
ar_dept['ARREARS'] = ar_dept['ASSESSMENT_AMNT'] - ar_dept['PAYMENT_NOR']
ar_dept['ARREARS_PCT'] = (ar_dept['ARREARS'] / ar_dept['ASSESSMENT_AMNT'] * 100).round(1)
ar_dept = ar_dept.sort_values('ARREARS', ascending=False).head(15)
ar_dept.columns = ['Department', 'Assessment', 'Payment', 'Arrears', 'Arrears%']
st.dataframe(ar_dept, use_container_width=True)

st.divider()

# ---- CIRCLE/DIVISION/SUBDIV BREAKDOWN ----
st.subheader("Location Breakdown")

loc_tabs = st.tabs(["By Circle", "By Division", "By Sub Division"])

with loc_tabs[0]:
    circle_df = filtered.groupby('CIRCLENAME').agg({
        'ASSESSMENT_AMNT': 'sum',
        'PAYMENT_NOR': 'sum',
        'TOTAL_CL_BAL': 'sum',
        'CONSNO': 'count'
    }).reset_index()
    circle_df.columns = ['Circle', 'Assessment', 'Payment', 'Closing Balance', 'Consumers']
    circle_df['Arrears'] = circle_df['Assessment'] - circle_df['Payment']
    circle_df['Collection%'] = (circle_df['Payment'] / circle_df['Assessment'] * 100).round(1)
    st.dataframe(circle_df.sort_values('Assessment', ascending=False), use_container_width=True)

with loc_tabs[1]:
    div_df = filtered.groupby('DIVNAME').agg({
        'ASSESSMENT_AMNT': 'sum',
        'PAYMENT_NOR': 'sum',
        'TOTAL_CL_BAL': 'sum',
        'CONSNO': 'count'
    }).reset_index()
    div_df.columns = ['Division', 'Assessment', 'Payment', 'Closing Balance', 'Consumers']
    div_df['Arrears'] = div_df['Assessment'] - div_df['Payment']
    div_df['Collection%'] = (div_df['Payment'] / div_df['Assessment'] * 100).round(1)
    st.dataframe(div_df.sort_values('Assessment', ascending=False), use_container_width=True)

with loc_tabs[2]:
    subdiv_df = filtered.groupby(['SUBDIVNAME', 'SDNAME']).agg({
        'ASSESSMENT_AMNT': 'sum',
        'PAYMENT_NOR': 'sum',
        'TOTAL_CL_BAL': 'sum',
        'CONSNO': 'count'
    }).reset_index()
    subdiv_df.columns = ['Sub Division', 'SD Name', 'Assessment', 'Payment', 'Closing Balance', 'Consumers']
    subdiv_df['Arrears'] = subdiv_df['Assessment'] - subdiv_df['Payment']
    subdiv_df['Collection%'] = (subdiv_df['Payment'] / subdiv_df['Assessment'] * 100).round(1)
    st.dataframe(subdiv_df.sort_values('Assessment', ascending=False), use_container_width=True)

st.divider()

# ---- RAW DATA ----
with st.expander("View Raw Data"):
    st.dataframe(filtered.head(100), use_container_width=True)
