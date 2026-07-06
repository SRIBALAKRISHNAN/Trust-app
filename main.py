import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time
import requests
import plotly.graph_objects as go

# ==========================================
# Database Configuration
# ==========================================
DB_HOST = st.secrets["DB_HOST"]
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]
DB_PORT = st.secrets["DB_PORT"]
DB_NAME = st.secrets["DB_NAME"]

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            database=DB_NAME,
            ssl_disabled=False
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def run_query(query, params=None):
    conn = create_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return pd.DataFrame(result)
    return pd.DataFrame()

def execute_query(query, params):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    return False

# ==========================================
# Session State & Bulletproof Pincode API
# ==========================================
if 'inc_address' not in st.session_state: st.session_state.inc_address = ""
if 'exp_address' not in st.session_state: st.session_state.exp_address = ""

def fetch_address_from_api(pincode):
    offline_pincodes = {
        "641601": "Tiruppur North, Tiruppur, Tamil Nadu",
        "641602": "Tiruppur Bazaar, Tiruppur, Tamil Nadu",
        "641603": "Tiruppur South, Tiruppur, Tamil Nadu",
        "641604": "Tiruppur Nallur, Tiruppur, Tamil Nadu",
        "641605": "Tiruppur East, Tiruppur, Tamil Nadu",
        "641606": "Tiruppur Central, Tiruppur, Tamil Nadu",
        "641652": "Somanur, Coimbatore, Tamil Nadu",
        "641001": "Coimbatore Central, Coimbatore, Tamil Nadu"
    }

    if str(pincode) in offline_pincodes:
        return f"{offline_pincodes[str(pincode)]} - {pincode}"

    if len(str(pincode)) == 6 and str(pincode).isdigit():
        try:
            response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}", timeout=3)
            data = response.json()
            if data and data[0]['Status'] == 'Success':
                po = data[0]['PostOffice'][0]
                return f"{po['Name']}, {po['District']}, {po['State']} - {pincode}"
            else:
                return "INVALID"
        except:
            return "OFFLINE"
    return "INVALID"

# ==========================================
# Streamlit UI & Custom CSS
# ==========================================
st.set_page_config(page_title="SOFWT Management", layout="wide", initial_sidebar_state="expanded")

page_bg_css = """
<style>
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #f1f8f1 0%, #ffffff 100%); }
[data-testid="stSidebar"] { background-color: #e2efe2; border-right: 1px solid #c8e1c8; }
[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
.stButton>button { margin-top: 28px; width: 100%; border-radius: 8px; }
.splash-container {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    height: 70vh; text-align: center; animation: fadeIn 1.5s ease-in-out;
}
@keyframes fadeIn { 0% { opacity: 0; transform: translateY(-20px); } 100% { opacity: 1; transform: translateY(0); } }
.trust-title { color: #1b5e20; font-size: 4.5em; font-weight: 900; letter-spacing: 2px; margin-bottom: 0px; }
.trust-subtitle { color: #388e3c; font-size: 1.8em; font-weight: 500; margin-top: 0px; }
.loading-text { color: #666; font-size: 1.1em; margin-top: 20px; font-style: italic; }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# ==========================================
# Beautiful Splash Screen Logic
# ==========================================
if 'splash_shown' not in st.session_state:
    splash_placeholder = st.empty()
    with splash_placeholder.container():
        st.markdown(
            """
            <div class="splash-container">
                <h1 class="trust-title">SOFWT</h1>
                <h3 class="trust-subtitle">Savarangadu Ours Family Welfare Trust</h3>
                <p class="loading-text">Initializing Secure Treasurer Dashboard...</p>
            </div>
            """, unsafe_allow_html=True
        )
        with st.columns([1,2,1])[1]:
            st.progress(0, "Connecting to database...")
            time.sleep(0.8)
            st.progress(50, "Loading analytics...")
            time.sleep(0.8)
            st.progress(100, "Ready.")
            time.sleep(0.5)
            
    splash_placeholder.empty()
    st.session_state['splash_shown'] = True

# ==========================================
# Main App Header
# ==========================================
col1, col2 = st.columns([1, 4])
with col1:
    try: st.image("logo.jpg", width=120)
    except: pass
with col2:
    st.title("Savarangadu Ours Family Welfare Trust")
    st.markdown("##### Centralized Revenue, Expenditure & Member Management")

st.markdown("---")

menu = st.sidebar.radio("Navigation Menu", [
    "Dashboard Overview", 
    "Add Income / Revenue", 
    "Add Expenditure / Spend", 
    "Voter Rights & Consistency", 
    "Detailed Reports & Filters", 
    "Bank & UPI Details"
])

# ==========================================
# 1. Dashboard Module
# ==========================================
if menu == "Dashboard Overview":
    st.header("Financial Dashboard")
    
    total_inc = run_query("SELECT SUM(amount) as total FROM income")['total'][0] or 0.0
    total_exp = run_query("SELECT SUM(amount) as total FROM expenditure")['total'][0] or 0.0
    balance = float(total_inc) - float(total_exp)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income (Revenue)", f"₹ {float(total_inc):,.2f}")
    col2.metric("Total Expenditure", f"₹ {float(total_exp):,.2f}")
    col3.metric("Current Trust Balance", f"₹ {balance:,.2f}")
    
    st.markdown("---")
    st.subheader("Month-wise Financial Tally")
    
    inc_monthly = run_query("SELECT DATE_FORMAT(transaction_date, '%Y-%m') as Month, SUM(amount) as Income FROM income GROUP BY Month")
    exp_monthly = run_query("SELECT DATE_FORMAT(transaction_date, '%Y-%m') as Month, SUM(amount) as Expenditure FROM expenditure GROUP BY Month")
    
    if not inc_monthly.empty or not exp_monthly.empty:
        if inc_monthly.empty: inc_monthly = pd.DataFrame(columns=['Month', 'Income'])
        if exp_monthly.empty: exp_monthly = pd.DataFrame(columns=['Month', 'Expenditure'])
        
        df_monthly = pd.merge(inc_monthly, exp_monthly, on='Month', how='outer').fillna(0).sort_values(by='Month')
        df_monthly['Net Balance'] = df_monthly['Income'] - df_monthly['Expenditure']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_monthly['Month'], y=df_monthly['Income'], name='Income', marker_color='#2e7d32'))
        fig.add_trace(go.Bar(x=df_monthly['Month'], y=df_monthly['Expenditure'], name='Expenditure', marker_color='#d32f2f'))
        fig.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['Net Balance'], name='Net Balance', mode='lines+markers', line=dict(color='#1565c0', width=3), marker=dict(size=8)))
        
        fig.update_layout(barmode='group', hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Month", yaxis_title="Amount (₹)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for monthly trend charts.")

    st.markdown("---")
    st.subheader("Category-wise Distribution")
    
    col_pie1, col_pie2 = st.columns(2)
    
    with col_pie1:
        inc_cat = run_query("SELECT category, SUM(amount) as total FROM income GROUP BY category")
        if not inc_cat.empty:
            fig_inc_pie = go.Figure(data=[go.Pie(labels=inc_cat['category'], values=inc_cat['total'], hole=0.4, textinfo='percent', hoverinfo='label+percent+value', marker=dict(colors=['#4caf50', '#81c784', '#a5d6a7', '#c8e6c9', '#2e7d32', '#1b5e20']))])
            fig_inc_pie.update_layout(title_text="Income Sources", title_x=0.25, margin=dict(t=40, b=10, l=10, r=10), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
            st.plotly_chart(fig_inc_pie, use_container_width=True)
        else:
            st.info("No income data for category chart.")
            
    with col_pie2:
        exp_cat = run_query("SELECT category, SUM(amount) as total FROM expenditure GROUP BY category")
        if not exp_cat.empty:
            fig_exp_pie = go.Figure(data=[go.Pie(labels=exp_cat['category'], values=exp_cat['total'], hole=0.4, textinfo='percent', hoverinfo='label+percent+value', marker=dict(colors=['#f44336', '#e57373', '#ffcdd2', '#d32f2f', '#b71c1c']))])
            fig_exp_pie.update_layout(title_text="Expenditure Breakdown", title_x=0.25, margin=dict(t=40, b=10, l=10, r=10), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
            st.plotly_chart(fig_exp_pie, use_container_width=True)
        else:
            st.info("No expenditure data for category chart.")

# ==========================================
# 2. Add Income Module (With Excel Upload)
# ==========================================
elif menu == "Add Income / Revenue":
    st.header("Register New Income")
    
    tab_manual, tab_bulk = st.tabs(["✍️ Manual Entry", "📁 Bulk Excel Upload"])
    
    # --- MANUAL ENTRY TAB ---
    with tab_manual:
        col1, col2 = st.columns(2)
        date = col1.date_input("Transaction Date")
        name = col2.text_input("Name of Donor / Member")
        
        father_name = col1.text_input("Father's Name")
        pin_col, btn_col = col2.columns([3, 1])
        pincode = pin_col.text_input("Pincode", max_chars=6, key="inc_pincode")
        
        if btn_col.button("Fetch", key="btn_inc_fetch"):
            result = fetch_address_from_api(pincode)
            if result == "INVALID": st.error("Invalid Pincode.")
            elif result == "OFFLINE": st.warning("No internet. Type address manually.")
            else:
                st.session_state.inc_address = result
                st.success("Address found!")
                
        address = st.text_area("Address (Editable)", key="inc_address")
        
        col3, col4, col5 = st.columns(3)
        category = col3.selectbox("Income Category", ['Monthly subscription', 'Donation', 'Funeral fund', 'Education fund', 'Medical emergency fund', 'Poor fund'])
        amount = col4.number_input("Amount (₹)", min_value=0.0, step=100.0)
        payment_mode = col5.selectbox("Payment Mode", ['UPI/GPay/Paytm', 'Bank Transfer', 'Cash', 'Cheque'])
        
        col6, col7 = st.columns(2)
        reference_no = col6.text_input("Treasurer Ref / Cheque No. (Optional)")
        remarks = col7.text_area("Remarks", height=68)
        
        if st.button("Save Income Record", type="primary"):
            if name and amount > 0:
                query = """INSERT INTO income 
                           (transaction_date, person_name, father_name, pincode, address, category, amount, payment_mode, reference_no, remarks) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (date, name, father_name, pincode, address, category, amount, payment_mode, reference_no, remarks)
                if execute_query(query, params):
                    st.success(f"Recorded ₹{amount} from {name}. Reference: {reference_no}")
                    st.session_state.inc_address = "" 
            else: st.error("Provide a valid Name and Amount.")

    # --- BULK EXCEL UPLOAD TAB ---
    with tab_bulk:
        st.write("Upload an **Excel file (.xlsx or .xls)** to add multiple members at once. Required format: **Col 1 (Sl No), Col 2 (Name), Col 3 (Amount)**.")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        bulk_date = col_b1.date_input("Master Date for these entries")
        bulk_cat = col_b2.selectbox("Master Category", ['Monthly subscription', 'Donation', 'Funeral fund', 'Education fund', 'Medical emergency fund', 'Poor fund'], key="bulk_cat")
        bulk_mode = col_b3.selectbox("Master Payment Mode", ['UPI/GPay/Paytm', 'Bank Transfer', 'Cash', 'Cheque'], key="bulk_mode")
        
        # Changed 'csv' to 'xlsx' and 'xls'
        uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            # Read Excel instead of CSV
            try:
                df_excel = pd.read_excel(uploaded_file, header=None)
                st.write("Data Preview:")
                st.dataframe(df_excel.head(3))
                
                if st.button("Upload and Save to Database", type="primary"):
                    success_count = 0
                    for index, row in df_excel.iterrows():
                        try:
                            # Index 1 is Name, Index 2 is Amount (Ignoring Index 0 / SlNo)
                            name_val = str(row.iloc[1]).strip()
                            amount_val = float(row.iloc[2])
                            
                            # CRITICAL FIX: Ignore headers AND ignore any row where the name contains 'total'
                            if name_val and amount_val > 0 and name_val.lower() != 'name' and 'total' not in name_val.lower():
                                q_bulk = """INSERT INTO income 
                                           (transaction_date, person_name, father_name, pincode, address, category, amount, payment_mode, reference_no, remarks) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                                p_bulk = (bulk_date, name_val, "", "", "", bulk_cat, amount_val, bulk_mode, "", "Bulk Excel Upload")
                                if execute_query(q_bulk, p_bulk):
                                    success_count += 1
                        except Exception as e:
                            continue # Skip header rows, invalid data, or total rows
                            
                    st.success(f"Successfully added {success_count} records to the database! (Ignored 'Total' rows)")
            except Exception as e:
                st.error("Error reading the Excel file. Please ensure it is a valid .xlsx format.")

# ==========================================
# 3. Add Expenditure Module
# ==========================================
elif menu == "Add Expenditure / Spend":
    st.header("Register New Expenditure")
    
    col1, col2 = st.columns(2)
    date = col1.date_input("Transaction Date")
    name = col2.text_input("Recipient / Beneficiary Name")
    
    father_name = col1.text_input("Father's Name / Guardian")
    pin_col, btn_col = col2.columns([3, 1])
    pincode = pin_col.text_input("Pincode", max_chars=6, key="exp_pincode")
    
    if btn_col.button("Fetch", key="btn_exp_fetch"):
        result = fetch_address_from_api(pincode)
        if result == "INVALID": st.error("Invalid Pincode.")
        elif result == "OFFLINE": st.warning("No internet. Type address manually.")
        else:
            st.session_state.exp_address = result
            st.success("Address found!")
            
    address = st.text_area("Address (Editable)", key="exp_address")
    
    col3, col4, col5 = st.columns(3)
    category = col3.selectbox("Expenditure Category", ['Funeral fund', 'Education fund', 'Medical emergency fund', 'Poor family fund'])
    amount = col4.number_input("Amount (₹)", min_value=0.0, step=100.0)
    reference_no = col5.text_input("Treasurer Ref / Cheque No. (Required for Bank/Tally)")
    remarks = st.text_area("Detailed Reasons (Crucial for high amounts)")
    
    if st.button("Save Expenditure Record", type="primary"):
        if name and amount > 0:
            query = """INSERT INTO expenditure 
                       (transaction_date, recipient_name, father_name, pincode, address, category, amount, reference_no, remarks) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            params = (date, name, father_name, pincode, address, category, amount, reference_no, remarks)
            if execute_query(query, params):
                st.success(f"Recorded expenditure of ₹{amount} to {name}.")
                st.session_state.exp_address = ""
        else: st.error("Provide a valid Recipient Name and Amount.")

# ==========================================
# 4. Consistency & Voter Rights Module
# ==========================================
elif menu == "Voter Rights & Consistency":
    st.header("Member Consistency & Voting Rights")
    st.write("Automatically determines active status based on consecutive or multiple month contributions.")
    
    consistency_threshold = st.slider("Months required for Voting Rights:", min_value=1, max_value=36, value=2)
    
    query = """
    SELECT 
        person_name as 'Member Name',
        COUNT(DISTINCT DATE_FORMAT(transaction_date, '%Y-%m')) as 'Months Active',
        SUM(amount) as 'Total Contributed',
        MAX(transaction_date) as 'Last Payment Date'
    FROM income
    GROUP BY person_name
    ORDER BY 'Months Active' DESC, 'Total Contributed' DESC
    """
    df = run_query(query)
    
    if not df.empty:
        df['Voter Rights'] = df['Months Active'].apply(lambda x: '✅ Eligible' if x >= consistency_threshold else '🔴 Pending')
        total_eligible = len(df[df['Voter Rights'] == '✅ Eligible'])
        st.metric("Total Eligible Voters", total_eligible)
        
        # FIX: Changed 'applymap' to 'map' to support the newest version of Pandas in the Cloud
        st.dataframe(df.style.map(lambda x: 'color: green; font-weight:bold' if x == '✅ Eligible' else 'color: red', subset=['Voter Rights']), use_container_width=True)
    else:
        st.info("No income records found to calculate consistency.")

# ==========================================
# 5. Detailed Reports Module (With EDIT/DELETE Function)
# ==========================================
elif menu == "Detailed Reports & Filters":
    st.header("Advanced Reports & Analytics")
    tab1, tab2 = st.tabs(["📊 Income Tally & Search", "🧾 Expenditure Management"])
    
    # ------------------ INCOME TAB ------------------
    with tab1:
        st.subheader("Filter Income Records")
        colA, colB, colC = st.columns(3)
        
        inc_df = run_query("SELECT * FROM income ORDER BY transaction_date DESC")
        if not inc_df.empty:
            people_list = ["All"] + list(inc_df['person_name'].unique())
            sel_person = colA.selectbox("Filter by Person", people_list, key="inc_p")
            
            cat_list = ["All"] + list(inc_df['category'].unique())
            sel_cat = colB.selectbox("Filter by Category", cat_list, key="inc_c")
            
            inc_df['Month'] = pd.to_datetime(inc_df['transaction_date']).dt.strftime('%Y-%m')
            month_list = ["All"] + list(inc_df['Month'].unique())
            sel_month = colC.selectbox("Filter by Month", month_list, key="inc_m")
            
            filtered_inc = inc_df.copy()
            if sel_person != "All": filtered_inc = filtered_inc[filtered_inc['person_name'] == sel_person]
            if sel_cat != "All": filtered_inc = filtered_inc[filtered_inc['category'] == sel_cat]
            if sel_month != "All": filtered_inc = filtered_inc[filtered_inc['Month'] == sel_month]
            
            filtered_inc_display = filtered_inc.drop(columns=['Month'])
            st.dataframe(filtered_inc_display, use_container_width=True)
            st.markdown(f"**Filtered Total: ₹ {filtered_inc['amount'].sum():,.2f}**")
            
            # --- Edit / Delete Section for Income ---
            with st.expander("✏️ Manage Records (Edit / Delete)"):
                if not filtered_inc.empty:
                    inc_options = {row['id']: f"ID: {row['id']} | {row['person_name']} | ₹{row['amount']} | Date: {row['transaction_date']}" for index, row in filtered_inc.iterrows()}
                    selected_inc_id = st.selectbox("Select Record", options=list(inc_options.keys()), format_func=lambda x: inc_options[x], key="edit_inc_select")
                    
                    if selected_inc_id:
                        sel_row = filtered_inc[filtered_inc['id'] == selected_inc_id].iloc[0]
                        
                        with st.form("edit_inc_form"):
                            st.write("Modify Details Below:")
                            e_col1, e_col2 = st.columns(2)
                            e_date = e_col1.date_input("Date", pd.to_datetime(sel_row['transaction_date']))
                            e_name = e_col2.text_input("Name", str(sel_row['person_name']))
                            
                            cats = ['Monthly subscription', 'Donation', 'Funeral fund', 'Education fund', 'Medical emergency fund', 'Poor fund']
                            e_cat = e_col1.selectbox("Category", cats, index=cats.index(sel_row['category']) if sel_row['category'] in cats else 0)
                            e_amt = e_col2.number_input("Amount", value=float(sel_row['amount']))
                            
                            modes = ['UPI/GPay/Paytm', 'Bank Transfer', 'Cash', 'Cheque']
                            e_mode = e_col1.selectbox("Payment Mode", modes, index=modes.index(sel_row['payment_mode']) if sel_row['payment_mode'] in modes else 0)
                            e_ref = e_col2.text_input("Ref/Cheque No", str(sel_row['reference_no']) if pd.notnull(sel_row['reference_no']) else "")
                            
                            if st.form_submit_button("Update Record", type="primary"):
                                q_upd = """UPDATE income SET transaction_date=%s, person_name=%s, category=%s, amount=%s, payment_mode=%s, reference_no=%s WHERE id=%s"""
                                if execute_query(q_upd, (e_date, e_name, e_cat, e_amt, e_mode, e_ref, selected_inc_id)):
                                    st.success("Record Updated!")
                                    time.sleep(1)
                                    st.rerun()

                        st.markdown("---")
                        if st.button("Delete Selected Income Record", type="primary"):
                            if execute_query("DELETE FROM income WHERE id = %s", (selected_inc_id,)):
                                st.success(f"Record Deleted!")
                                time.sleep(1) 
                                st.rerun() 
        else: st.info("No Income Data.")

    # ------------------ EXPENDITURE TAB ------------------
    with tab2:
        st.subheader("Filter Expenditure & High-Value Grants")
        colX, colY, colZ = st.columns(3)
        
        exp_df = run_query("SELECT * FROM expenditure ORDER BY transaction_date DESC")
        if not exp_df.empty:
            recip_list = ["All"] + list(exp_df['recipient_name'].unique())
            sel_recip = colX.selectbox("Filter by Recipient Name", recip_list, key="exp_r")
            
            cat_list_exp = ["All"] + list(exp_df['category'].unique())
            sel_cat_exp = colY.selectbox("Filter by Category", cat_list_exp, key="exp_c")
            
            high_value_limit = colZ.number_input("Minimum Amount Filter (₹)", min_value=0, value=0, step=1000)
            
            filtered_exp = exp_df.copy()
            if sel_recip != "All": filtered_exp = filtered_exp[filtered_exp['recipient_name'] == sel_recip]
            if sel_cat_exp != "All": filtered_exp = filtered_exp[filtered_exp['category'] == sel_cat_exp]
            if high_value_limit > 0: filtered_exp = filtered_exp[filtered_exp['amount'] >= high_value_limit]
            
            st.dataframe(filtered_exp, use_container_width=True)
            st.markdown(f"**Filtered Total Spend: ₹ {filtered_exp['amount'].sum():,.2f}**")
            
            # --- Edit / Delete Section for Expenditure ---
            with st.expander("✏️ Manage Records (Edit / Delete)"):
                if not filtered_exp.empty:
                    exp_options = {row['id']: f"ID: {row['id']} | {row['recipient_name']} | ₹{row['amount']} | Date: {row['transaction_date']}" for index, row in filtered_exp.iterrows()}
                    selected_exp_id = st.selectbox("Select Record", options=list(exp_options.keys()), format_func=lambda x: exp_options[x], key="edit_exp_select")
                    
                    if selected_exp_id:
                        sel_exp_row = filtered_exp[filtered_exp['id'] == selected_exp_id].iloc[0]
                        
                        with st.form("edit_exp_form"):
                            st.write("Modify Details Below:")
                            ex_col1, ex_col2 = st.columns(2)
                            ex_date = ex_col1.date_input("Date", pd.to_datetime(sel_exp_row['transaction_date']))
                            ex_name = ex_col2.text_input("Name", str(sel_exp_row['recipient_name']))
                            
                            exp_cats = ['Funeral fund', 'Education fund', 'Medical emergency fund', 'Poor family fund']
                            ex_cat = ex_col1.selectbox("Category", exp_cats, index=exp_cats.index(sel_exp_row['category']) if sel_exp_row['category'] in exp_cats else 0)
                            ex_amt = ex_col2.number_input("Amount", value=float(sel_exp_row['amount']))
                            
                            ex_ref = ex_col1.text_input("Ref/Cheque No", str(sel_exp_row['reference_no']) if pd.notnull(sel_exp_row['reference_no']) else "")
                            
                            if st.form_submit_button("Update Record", type="primary"):
                                q_upd_exp = """UPDATE expenditure SET transaction_date=%s, recipient_name=%s, category=%s, amount=%s, reference_no=%s WHERE id=%s"""
                                if execute_query(q_upd_exp, (ex_date, ex_name, ex_cat, ex_amt, ex_ref, selected_exp_id)):
                                    st.success("Record Updated!")
                                    time.sleep(1)
                                    st.rerun()

                        st.markdown("---")
                        if st.button("Delete Selected Expenditure Record", type="primary"):
                            if execute_query("DELETE FROM expenditure WHERE id = %s", (selected_exp_id,)):
                                st.success(f"Record Deleted!")
                                time.sleep(1) 
                                st.rerun() 
        else: st.info("No Expenditure Data.")

# ==========================================
# 6. Bank Details Module
# ==========================================
elif menu == "Bank & UPI Details":
    st.header("Trust Official Bank & Payment Details")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### Bank Account Details
        * **Trust Name**: Savarangadu Ours Family Welfare Trust (SOFWT)
        * **Bank Name**: CANARA BANK
        * **Account No**: `120023738121`
        * **IFSC Code**: `CNRB0005918`
        * **Branch**: TIRUPPUR NALLUR
        """)
    with col2:
        st.markdown("""
        ### UPI / Digital Payments
        * **Google Pay / PhonePe No**: `98946 27299`
        * **Paytm UPI ID**: `9894627299@pthdfc`
        * **Account Name**: Savarangadu Ours Fam
        """)
