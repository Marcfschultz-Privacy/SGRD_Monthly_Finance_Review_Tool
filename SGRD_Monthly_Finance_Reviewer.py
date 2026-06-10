import streamlit as st
import pandas as pd

st.set_page_config(page_title="Road District Auditor", layout="wide")

st.title("🛣️ Road District Monthly Audit Tool")

uploaded_file = st.file_uploader("Upload Treasurer's Spreadsheet (.xlsx)", type="xlsx")

if uploaded_file:
    # Load all sheets into a dictionary
    xls = pd.ExcelFile(uploaded_file)
    sheet_map = {name.upper(): name for name in xls.sheet_names}
    
    # --- 1. REVENUE ANALYSIS ---
    if 'REVENUE' in sheet_map:
        st.subheader("📊 Revenue Analysis")
        df_rev = pd.read_excel(xls, sheet_name=sheet_map['REVENUE'])
        try:
            df_rev.columns = [str(c).strip() for c in df_rev.columns]
            may_data = df_rev[df_rev.iloc[:, 0].str.upper() == 'MAY'].iloc[0]
            curr_may, prev_may = may_data['2026'], may_data['2025']
            
            col1, col2 = st.columns(2)
            col1.metric("May 2026 Revenue", f"${curr_may:,.2f}", f"{((curr_may/prev_may)-1)*100:.1f}% vs last year", delta_color="inverse")
            if curr_may < (prev_may * 0.5):
                st.error("⚠️ Revenue Warning: May intake is significantly lower than May 2025.")
        except Exception:
            st.info("Revenue tab found, but could not parse 'MAY' or year columns.")

    # --- 2. FISCAL YEAR BUDGET BURN RATE ---
    if 'BUDGET' in sheet_map:
        st.subheader("🔥 Fiscal Year Burn Rate")
        df_bud = pd.read_excel(xls, sheet_name=sheet_map['BUDGET'])
        try:
            total_budget = df_bud.iloc[:, 1].sum()
            total_spent = df_bud.iloc[:, 2].sum()
            burn_pct = (total_spent / total_budget)
            
            months_elapsed = 11 
            time_elapsed_pct = months_elapsed / 12
            
            st.write(f"**Annual Budget Progress:** ${total_spent:,.2f} spent of ${total_budget:,.2f} total.")
            st.progress(min(burn_pct, 1.0))
            
            if burn_pct > time_elapsed_pct:
                st.warning(f"⚠️ **Over-Burn:** Spent {burn_pct:.1%}, but year is {time_elapsed_pct:.1%} complete.")
            else:
                st.success(f"✅ **On Track:** Spent {burn_pct:.1%} with {time_elapsed_pct:.1%} of year elapsed.")
        except Exception:
            st.info("Budget tab found, but check that columns 2 and 3 contain numeric 'Budget' and 'Actual' data.")

    # --- 3. CASH POSITION ---
    if 'CASH' in sheet_map:
        st.subheader("💰 Cash Position")
        df_cash = pd.read_excel(xls, sheet_name=sheet_map['CASH'])
        try:
            current_cash = df_cash.iloc[:, -1].iloc[-1]
            st.metric("Ending Cash Balance", f"${current_cash:,.2f}")
        except Exception:
            st.info("Cash tab found, but could not extract the final balance value.")

   # --- 4. MULTI-YEAR REVENUE TREND & BUDGET VARIANCE ---
    if 'REVENUE' in sheet_map and 'BUDGET' in sheet_map:
        st.subheader("📈 Multi-Year Revenue Trend & Budget Variance")
        
        # Reloading to ensure clean dataframes
        df_rev = pd.read_excel(xls, sheet_name=sheet_map['REVENUE'])
        df_bud = pd.read_excel(xls, sheet_name=sheet_map['BUDGET'])
        
        # --- A. Revenue Trend ---
        df_rev.columns = [str(c).strip() for c in df_rev.columns]
        target_years = ['2024', '2025', '2026']
        available = [y for y in target_years if y in df_rev.columns]
        if available:
            df_trend = df_rev.set_index(df_rev.columns[0])[available]
            # Filter rows where all years are 0 or empty
            df_trend = df_trend[(df_trend != 0).any(axis=1)].dropna(how='all')
            st.line_chart(df_trend)
        
        # --- B. Budget Performance Summary (FIXED) ---
        # Assuming the structure seen in your screenshot: 
        # Category (0), Budget 2026 (1), Actual 2026 (2), Actual 2025 (3), Actual 2024 (4)
        df_budget_data = df_bud.iloc[:, :5].copy()
        df_budget_data.columns = ['Category', 'Budget', 'Actual 2026', 'Actual 2025', 'Actual 2024']
        
        # FILTER: Remove rows where Category is 'None' or empty
        df_budget_data = df_budget_data[df_budget_data['Category'].notna()]
        df_budget_data = df_budget_data[df_budget_data['Category'] != 'None']
        
        # Clean numeric data
        cols_to_numeric = ['Budget', 'Actual 2026', 'Actual 2025', 'Actual 2024']
        for col in cols_to_numeric:
            df_budget_data[col] = pd.to_numeric(df_budget_data[col], errors='coerce').fillna(0)
            
        # Variance calculation
        df_budget_data['Variance (%)'] = ((df_budget_data['Actual 2026'] - df_budget_data['Budget']) / 
                                          df_budget_data['Budget'].replace(0, 1)) * 100
        
        st.write("### Budget Performance Summary")
        st.dataframe(df_budget_data.style.format({
            'Budget': '${:,.2f}',
            'Actual 2026': '${:,.2f}',
            'Actual 2025': '${:,.2f}',
            'Actual 2024': '${:,.2f}',
            'Variance (%)': '{:.1f}%'
        }))
    # Validate missing sheets
    missing = [tab for tab in ['REVENUE', 'BUDGET', 'CASH'] if tab not in sheet_map]
    if missing:
        st.sidebar.error(f"Missing required tabs: {', '.join(missing)}")
    else:
        st.sidebar.success("All required tabs (REVENUE, BUDGET, CASH) detected.")

else:
    st.info("Awaiting Treasurer's file...")
