import streamlit as st
import pandas as pd

st.set_page_config(page_title="Road District Auditor", layout="wide")

st.title("🛣️ Road District Monthly Audit Tool")

uploaded_file = st.file_uploader("Upload Treasurer's Spreadsheet (.xlsx)", type="xlsx")

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    st.sidebar.write("Found tabs:", sheets)

    # --- 1. DYNAMIC REVENUE ANALYSIS ---
    # Looks for 'REVENUE' tab (matches your screenshot)
    rev_tab = next((s for s in sheets if 'REVENUE' in s.upper()), None)
    if rev_tab:
        st.subheader("📊 Revenue Analysis")
        df_rev = pd.read_excel(xls, sheet_name=rev_tab)
        # Assuming the structure from your previous image: Months are rows, Years are columns
        # Let's find 'MAY' in the first column
        try:
            df_rev.columns = [str(c).strip() for c in df_rev.columns]
            may_data = df_rev[df_rev.iloc[:, 0].str.upper() == 'MAY'].iloc[0]
            
            curr_may = may_data['2026']
            prev_may = may_data['2025']
            
            col1, col2 = st.columns(2)
            col1.metric("May 2026 Revenue", f"${curr_may:,.2f}", f"{((curr_may/prev_may)-1)*100:.1f}% vs last year", delta_color="inverse")
            
            if curr_may < (prev_may * 0.5):
                st.error(f"⚠️ Revenue Warning: May intake is significantly lower than May 2025 ($ {prev_may:,.2f}).")
        except:
            st.info("Note: Could not calculate Revenue delta. Ensure columns are labeled 2025, 2026, etc.")

    # --- 2. MEANINGFUL BURN RATE ---
    # Looks for 'BUDGET' tab (matches your '2026 budget')
    bud_tab = next((s for s in sheets if 'BUDGET' in s.upper()), None)
    if bud_tab:
        st.subheader("🔥 Fiscal Year Burn Rate")
        df_bud = pd.read_excel(xls, sheet_name=bud_tab)
        
        # LOGIC: We look for a row that says 'TOTAL' and columns for 'Budget' and 'Actual'
        # Adjust these strings if the Treasurer uses different headers
        try:
            # Simple logic: sum the columns that look like currency
            total_budget = df_bud.iloc[:, 1].sum() # Assumes col 2 is Budget
            total_spent = df_bud.iloc[:, 2].sum()  # Assumes col 3 is Actual
            
            burn_pct = (total_spent / total_budget)
            
            # The "Meaningful" Part: Compare spending to time elapsed
            # We are in May (Month 11 of a July-June Fiscal Year)
            months_elapsed = 11 
            time_elapsed_pct = months_elapsed / 12
            
            st.write(f"**Annual Budget Progress:** ${total_spent:,.2f} spent of ${total_budget:,.2f} total.")
            st.progress(min(burn_pct, 1.0))
            
            if burn_pct > time_elapsed_pct:
                st.warning(f"⚠️ **Over-Burn:** You have spent {burn_pct:.1%}, but the year is only {time_elapsed_pct:.1%} complete.")
            else:
                st.success(f"✅ **On Track:** You have spent {burn_pct:.1%} with {time_elapsed_pct:.1%} of the year elapsed.")
        except:
            st.info("To see Burn Rate math, ensure the Budget tab has 'Budget' and 'Actual' columns.")

    # --- 3. CASH RECONCILIATION ---
    cash_tab = next((s for s in sheets if 'CASH' in s.upper()), None)
    if cash_tab:
        st.subheader("💰 Cash Position")
        df_cash = pd.read_excel(xls, sheet_name=cash_tab)
        # Pull the last value in the column that looks like a balance
        try:
            current_cash = df_cash.iloc[:, -1].iloc[-1] 
            st.metric("Ending Cash Balance", f"${current_cash:,.2f}")
        except:
            st.write("Upload the spreadsheet to see reconciled cash position.")

else:
    st.info("Awaiting Treasurer's file...")
