if s_dep: f_df = f_df[f_df['DEPARTMENT_NAME'].isin(s_dep)]
if status_view == "Active (0)": f_df = f_df[f_df['STATUS'] == "Active"]
elif status_view == "PDISC (1)": f_df = f_df[f_df['STATUS'] == "Disconnected"]

    # --- TOP HEADER & METRICS ---
    st.markdown("## 🏛️  Provincial Govt Departments Dashboard")
# --- TOP HEADER & METRICS ---
    st.markdown("## 🏛️ Provincial Govt Departments Dashboard")
st.divider()

    m1, m2, m3, m4,m5  = st.columns(5)
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
    m3.metric("Current Assessment", f"{f_df['ASSESSMENT_AMNT'].sum()/1e6:.2f}M")
    m4.metric("Current Payment", f"{f_df['PAYMENT_NOR'].sum()/1e6:.2f}M")
    m5.metric("Selected Records", f"{len(f_df):,}")
    m3.metric("Current Assessment", f"{total_assessment/1e6:.2f}M")
    m4.metric("Current Payment", f"{total_payment/1e6:.2f}M")
    m5.metric("Payment %", f"{pay_pct:.1f}%") # Percentage of Payment
    m6.metric("Selected Records", f"{len(f_df):,}")

# --- TABS (Enhanced Visibility & Prominence) ---
tab1, tab2, tab3 = st.tabs(["📊 Revenue Insights", "🎯 Accuracy Analysis", "📋 Master Ledger"])

@@ -323,3 +336,4 @@ def load_vibrant_data():
else:
st.warning("🔄 System Initializing... Please verify data connections.")

