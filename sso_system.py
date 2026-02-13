import streamlit as st
import pandas as pd
import os
import xlsxwriter
from datetime import datetime, timedelta
from io import BytesIO
from streamlit_option_menu import option_menu

MASTER_FILE = 'SSMember.csv'
st.set_page_config(page_title="SSM System", layout="wide", page_icon="🏥")

def calculate_insurance(salary):
    base_salary = max(1650, min(salary, 17500))
    insurance = base_salary * 0.05
    remaining = salary - insurance
    return insurance, remaining

def load_data():
    if not os.path.isfile(MASTER_FILE):
        return pd.DataFrame(columns=[
            'Member_ID', 'Name', 'ID_Card', 'Gender', 'Phone', 
            'Hospital', 'Salary', 'Insurance', 'Remaining', 
            'Join_Date', 'Last_Update'
        ])
    df = pd.read_csv(MASTER_FILE, encoding='utf-8-sig', dtype={'ID_Card': str, 'Phone': str})
    df['ID_Card'] = df['ID_Card'].str.replace("'", "")
    df['Phone'] = df['Phone'].str.replace("'", "")
    return df

def save_data(df):
    df_save = df.copy()
    df_save['ID_Card'] = "'" + df_save['ID_Card'].astype(str)
    df_save['Phone'] = "'" + df_save['Phone'].astype(str)
    df_save.to_csv(MASTER_FILE, index=False, encoding='utf-8-sig')

def main():
    with st.sidebar:
        st.title("🏥")
        st.title("Social Security Management SYSTEM")
        st.markdown("---")
        choice = option_menu(
            menu_title="Main Menu",
            options=[
                "Dashboard", 
                "Register Member", 
                "Edit Information", 
                "Terminate Member", 
                "Search & Calculator", 
                "Export Report"
            ],
            icons=[
                "house", 
                "person-plus", 
                "pencil-square", 
                "person-x", 
                "search", 
                "file-earmark-arrow-down"
            ],
            menu_icon="cast", 
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "transparent"},
                "icon": {"color": "#4472C4", "font-size": "18px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin": "0px", 
                    "--hover-color": "#f0f2f6"
                },
                "nav-link-selected": {"background-color": "#4472C4"},
            }
        )
        st.markdown("---")
        st.info("Social Security Management\nVersion 1.0")
    df = load_data()
    if choice == "Dashboard":
        render_dashboard(df)
    elif choice == "Register Member":
        render_register(df)
    elif choice == "Edit Information":
        render_edit(df)
    elif choice == "Terminate Member":
        render_termination(df)
    elif choice == "Search & Calculator":
        render_search_calc(df)
    elif choice == "Export Report":
        render_export(df)

def render_dashboard(df):
    st.header("📊 Overview Dashboard")
    if not df.empty:
        # Metrics Row
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("👥 Total Members", f"{len(df):,} Person")
        col_m2.metric("💰 Total SS Fee", f"{df['Insurance'].sum():,.2f} THB")
        col_m3.metric("💵 Avg Salary", f"{df['Salary'].mean():,.2f} THB")
        
        st.markdown("---")
        
        # Charts Row
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.subheader("🏥 Hospital Distribution")
            st.bar_chart(df['Hospital'].value_counts(), color="#4472C4")
        with col_c2:
            st.subheader("🚻 Gender")
            # Simple dataframe for gender is cleaner than raw table
            gender_df = df['Gender'].value_counts().reset_index()
            gender_df.columns = ['Gender', 'Count']
            st.dataframe(gender_df, hide_index=True, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📋 Member List")
        
        # Formatted Dataframe (สวยกว่า st.table)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Salary": st.column_config.NumberColumn("Salary (THB)", format="%.2f"),
                "Insurance": st.column_config.NumberColumn("SS Fee", format="%.2f"),
                "Remaining": st.column_config.NumberColumn("Net", format="%.2f"),
                "ID_Card": st.column_config.TextColumn("ID Card"),
            }
        )
    else:
        st.info("No data available.")

def render_register(df):
    st.header("📝 Register New Member")
    with st.form("register_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            id_card = st.text_input("ID Card (13 digits)", max_chars=13)
            name = st.text_input("Name - Surname")
            gender = st.selectbox("Gender", ["Male", "Female"])
        with col2:
            phone = st.text_input("Phone (10 digits)", max_chars=10)
            hospital = st.text_input("Hospital")
            salary = st.number_input("Salary", min_value=0.0, step=500.0)
        submitted = st.form_submit_button("Submit Registration")      
        if submitted:
            if len(id_card) != 13 or not id_card.isdigit():
                st.error("Invalid ID Card")
            elif df['ID_Card'].str.contains(id_card).any():
                st.error("This ID Card is already registered")
            elif not name or any(char.isdigit() for char in name):
                st.error("Invalid Name")
            elif salary < 1650:
                st.warning("Salary must be at least 1,650 THB")
            else:
                ins, rem = calculate_insurance(salary)
                if df.empty:
                    new_id = "S-0001"
                else:
                    last_num = int(df['Member_ID'].str.split('-').str[1].max())
                    new_id = f"S-{last_num + 1:04d}"              
                new_data = {
                    'Member_ID': new_id, 'Name': name, 'ID_Card': id_card,
                    'Gender': gender, 'Phone': phone, 'Hospital': hospital,
                    'Salary': salary, 'Insurance': ins, 'Remaining': rem,
                    'Join_Date': datetime.now().strftime("%Y-%m-%d"),
                    'Last_Update': "-"
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success(f"Registered {name} successfully!")

def render_edit(df):
    st.header("✏️ Edit Member Information")
    if df.empty:
        st.warning("No data to edit.")
        return
    
    member_to_edit = st.selectbox("Select Member to Edit", df['Member_ID'] + " - " + df['Name'])
    m_id = member_to_edit.split(" - ")[0]
    idx = df[df['Member_ID'] == m_id].index[0]
    row = df.iloc[idx]
    
    with st.form("edit_form"):
        col1, col2 = st.columns(2)
        # เพิ่มช่องแก้ไข ID Card
        new_id_card = col1.text_input("ID Card", value=row['ID_Card'], max_chars=13)
        new_name = col2.text_input("Name", value=row['Name'])
        
        new_hos = col1.text_input("Hospital", value=row['Hospital'])
        new_phone = col2.text_input("Phone", value=row['Phone'])
        
        new_sal = st.number_input("Salary", value=float(row['Salary']))
        
        if st.form_submit_button("Save Changes"):
            # ตรวจสอบว่า ID Card ถูกต้องและไม่ซ้ำ (ถ้ามีการเปลี่ยน)
            if len(new_id_card) != 13 or not new_id_card.isdigit():
                st.error("Invalid ID Card format")
            elif new_id_card != row['ID_Card'] and df['ID_Card'].isin([new_id_card]).any():
                st.error("This ID Card already exists!")
            else:
                ins, rem = calculate_insurance(new_sal)
                df.at[idx, 'ID_Card'] = new_id_card # บันทึก ID Card ใหม่
                df.at[idx, 'Name'] = new_name
                df.at[idx, 'Hospital'] = new_hos
                df.at[idx, 'Salary'] = new_sal
                df.at[idx, 'Phone'] = new_phone
                df.at[idx, 'Insurance'] = ins
                df.at[idx, 'Remaining'] = rem
                df.at[idx, 'Last_Update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(df)
                st.success("Information updated!")
                st.rerun()

def render_termination(df):
    st.header("❌ Terminate Member")
    search_id = st.text_input("Enter ID Card to search for termination")    
    if search_id:
        target = df[df['ID_Card'] == search_id]
        if not target.empty:
            st.warning(f"Are you sure you want to terminate: {target.iloc[0]['Name']}?")
            if st.button("Confirm Termination"):
                df = df[df['ID_Card'] != search_id]
                save_data(df)
                st.success("Member terminated.")
                st.rerun()
        else:
            st.error("Member not found.")

def render_search_calc(df):
    st.header("🔍 Search & Calculator")
    t1, t2 = st.tabs(["Search Member", "Quick Fee Calc"])   
    with t1:
        s_id = st.text_input("Search by ID Card", placeholder="Enter ID Card...")
        if s_id:
            res = df[df['ID_Card'] == s_id]
            if not res.empty:
                for _, row in res.iterrows():
                    with st.container(border=True):
                        st.subheader(f"👤 {row['Name']}")
                        st.caption(f"ID: {row['Member_ID']} | Joined: {row['Join_Date']}")
                        st.divider()                     
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**ID Card:** `{row['ID_Card']}`")
                        c2.markdown(f"**Phone:** `{row['Phone']}`")
                        c3.markdown(f"**Hospital:** {row['Hospital']}")
                        
                        st.markdown("### Financial Info")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Salary", f"{row['Salary']:,.2f}")
                        m2.metric("SS Fee (5%)", f"{row['Insurance']:,.2f}")
                        m3.metric("Net Receive", f"{row['Remaining']:,.2f}")
            else:
                st.warning("Member not found")             
    with t2:
        with st.container(border=True):
            q_sal = st.number_input("Input Salary", min_value=0.0, step=1000.0)
            if q_sal > 0:
                i, r = calculate_insurance(q_sal)
                st.divider()
                xc1, xc2 = st.columns(2)
                xc1.metric("SS Fee", f"{i:,.2f} THB")
                xc2.metric("Net Income", f"{r:,.2f} THB")

def render_export(df):
    st.header("📤 Export Data")
    if df.empty:
        st.info("No data to export.")
        return
    all_rows = df.to_dict('records')
    output = BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = wb.add_worksheet("SSM Data")
    fmt = {
        'head': wb.add_format({'bold': 1, 'bg_color': '#4472C4', 'color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'}),
        'text': wb.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'}),
        'cent': wb.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'}),
        'num': wb.add_format({'num_format': '#,##0.00', 'border': 1, 'valign': 'vcenter'}),
        'sum': wb.add_format({'bold': 1, 'bg_color': '#D9D9D9', 'border': 1, 'num_format': '#,##0.00', 'valign': 'vcenter'})
    }
    headers = ['ID', 'Name', 'ID Card', 'Gender', 'Phone', 'Hospital', 'Salary', 'SS Fee', 'Balance', 'Join Date', 'Last Update']
    widths = [10, 25, 18, 10, 15, 20, 15, 12, 15, 13, 20]
    for i, (h, w) in enumerate(zip(headers, widths)):
        ws.write(0, i, h, fmt['head'])
        ws.set_column(i, i, w)
    for r, row in enumerate(all_rows, 1):
        to_num = lambda k: float(str(row.get(k, 0)).replace(',', '')) if row.get(k) else 0.0
        data = [
            (row['Member_ID'], fmt['cent']),
            (row['Name'], fmt['text']),
            (str(row['ID_Card']).replace("'", ""), fmt['cent']),
            (row['Gender'], fmt['cent']),
            (str(row['Phone']).replace("'", ""), fmt['cent']),
            (row['Hospital'], fmt['text']),
            (to_num('Salary'), fmt['num']),
            (to_num('Insurance'), fmt['num']),
            (to_num('Remaining'), fmt['num']),
            (str(row.get('Join_Date', '-')), fmt['cent']),
            (str(row.get('Last_Update', '-')), fmt['cent'])
        ]
        for c, (val, f) in enumerate(data):
            ws.write(r, c, val, f)
    last_row = len(all_rows) + 1
    ws.write(last_row, 6, "TOTAL", fmt['head'])
    ws.write_formula(last_row, 7, f"=SUM(H2:H{last_row})", fmt['sum'])
    wb.close()
    th_time = datetime.utcnow() + timedelta(hours=7)
    filename = f"SSM_Report_{th_time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    st.download_button(
        label="📥 Download Excel Report",
        data=output.getvalue(),
        file_name=filename,  # ใส่ชื่อตัวแปรตรงนี้
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    ))
if __name__ == "__main__":
    main()
