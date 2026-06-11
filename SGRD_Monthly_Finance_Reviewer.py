
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Road District Auditor", layout="wide")
st.title("🛣️ Road District Monthly Audit Tool")

uploaded_file = st.file_uploader("Upload Treasurer's Spreadsheet (.xlsx)", type="xlsx")

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    st.sidebar.write("Found tabs:", sheets)

    # --- 1. ROBUST REVENUE ANALYSIS ---
    rev_tab = next((s for s in sheets if 'REVENUE' in s.upper()), None)
    if rev_tab:
        st.subheader("📊 Revenue Analysis")
        # Load the sheet without headers first to find the table
        df_raw = pd.read_excel(xls, sheet_name=rev_tab, header=None)
        
        try:
            # Search for the row containing month names (e.g., 'JULY')
            header_row_index = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains('JULY', case=False).any(), axis=1)].index[0]
            
            # Reload with the correct header row
            df_rev = pd.read_excel(xls, sheet_name=rev_tab, skiprows=header_row_index)
            df_rev.columns = [str(c).strip() for c in df_rev.columns] # Clean column names
            
            # Find the row for 'MAY'
            # We look in the first column (index 0)
            may_row = df_rev[df_rev.iloc[:, 0].astype(str).str.strip().str.upper() == 'MAY']
            
            if not may_row.empty:
                curr_may = may_row['2026'].values[0]
                prev_may = may_row['2025'].values[0]
                
                col1, col2 = st.columns(2)
                # Calculate % change
                change = ((curr_may / prev_may) - 1) * 100 if prev_may != 0 else 0
                
                col1.metric("May 2026 Revenue", f"${curr_may:,.2f}", f"{change:.1f}% vs 2025", delta_color="normal")
                col2.metric("May 2025 (Ref)", f"${prev_may:,.2f}")

                if curr_may < (prev_may * 0.5):
                    st.error(f"⚠️ **Revenue Anomaly:** May 2026 revenue is less than half of May 2025. This should be discussed.")
                else:
                    st.success("May revenue is within expected historical range.")
            else:
                st.warning("Could not find a row labeled 'MAY' in the Revenue sheet.")
        except Exception as e:
            st.error(f"Error parsing Revenue: {e}")
            st.info("Check if the Revenue sheet has columns labeled '2025' and '2026'.")

    # --- 2. IMPROVED BURN RATE ---
    bud_tab = next((s for s in sheets if 'BUDGET' in s.upper()), None)
    if bud_tab:
        st.subheader("🔥 Fiscal Year Burn Rate")
        df_bud = pd.read_excel(xls, sheet_name=bud_tab)
        
        # Try to find a 'TOTAL' row or just sum numeric columns
        try:
            # We assume Col 1 is 'Budgeted Amount' and Col 2 is 'Actual Spent'
            # Looking for common header names
            budget_col = [c for c in df_bud.columns if 'BUDGET' in str(c).upper()][0]
            actual_col = [c for c in df_bud.columns if 'ACTUAL' in str(c).upper() or 'SPENT' in str(c).upper()][0]
            
            total_budget = df_bud[budget_col].sum()
            total_spent = df_bud[actual_col].sum()
            
            burn_pct = (total_spent / total_budget) if total_budget != 0 else 0
            
            # Since you are in May (Month 11 of July-June cycle)
            months_elapsed = 11 
            time_elapsed_pct = months_elapsed / 12
            
            st.write(f"**Annual Budget Status:** Spent ${total_spent:,.2f} out of ${total_budget:,.2f}")
            st.progress(min(burn_pct, 1.0))
            
            if burn_pct > (time_elapsed_pct + 0.05): # 5% buffer
                st.warning(f"⚠️ **Overspending:** You've used {burn_pct:.1%} of budget, but only {time_elapsed_pct:.1%} of the year has passed.")
            else:
                st.success(f"✅ **On Track:** Budget use ({burn_pct:.1%}) is appropriate for Month 11 ({time_elapsed_pct:.1%}).")
        except:
            st.info("Ensure the Budget tab has columns labeled 'Budget' and 'Actual'.")

    # --- 3. CASH POSITION ---
    cash_tab = next((s for s in sheets if 'CASH' in s.upper()), None)
    if cash_tab:
        st.subheader("💰 Cash Position")
        df_cash = pd.read_excel(xls, sheet_name=cash_tab)
        try:
            # Look for a value in the last row, last column
            current_cash = df_cash.iloc[:, -1].dropna().iloc[-1]
            st.metric("Reported Cash on Hand", f"${current_cash:,.2f}")
        except:
            st.write("Could not pull cash balance. Check formatting of Cash tab.")

else:
    st.info("Please upload the spreadsheet (e.g., 'MAY FY26.xlsx') to begin.")
