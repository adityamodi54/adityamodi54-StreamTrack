import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import uuid

# Load credentials from Streamlit secrets
credentials_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict)

# Google Sheets authentication
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("Streamlit_track").sheet1

# The rest of your Streamlit code...
def get_unique_id():
    return str(uuid.uuid4())

def add_entry():
    with st.form(key='add_entry_form'):
        in_out = st.selectbox("In/Out", ["In", "Out"])
        date = st.date_input("Date")
        name = st.text_input("Name")
        domain = st.text_input("Domain")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        quantity = st.number_input("Quantity (leave blank if not applicable)", min_value=0.0, format="%.2f", value=1.0)
        comments = st.text_area("Comments")
        submit_button = st.form_submit_button(label='Add Entry')

        if submit_button:
            sr_no = len(sheet.get_all_records()) + 1
            reference_id = get_unique_id()
            total_amount = price * quantity
            entry = [sr_no, reference_id, in_out, date.strftime("%Y-%m-%d"), name, domain, price, quantity, total_amount, comments]
            sheet.append_row(entry)
            st.success("Entry added successfully.")

def read_entries():
    st.header("Entries")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    st.write(df)
    if st.button('Export to CSV'):
        df.to_csv('exported_data.csv', index=False)
        st.success("Data exported to 'exported_data.csv'.")

def update_entry():
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    
    ref_id = st.selectbox("Select Reference ID to update", df['Reference ID'].values)
    
    if ref_id:
        with st.form(key='update_entry_form'):
            in_out = st.selectbox("In/Out", ["In", "Out"])
            date = st.date_input("Date")
            name = st.text_input("Name")
            domain = st.text_input("Domain")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            quantity = st.number_input("Quantity (leave blank if not applicable)", min_value=0.0, format="%.2f", value=1.0)
            comments = st.text_area("Comments")
            submit_button = st.form_submit_button(label='Update Entry')

            if submit_button:
                idx = df.index[df['Reference ID'] == ref_id].tolist()[0] + 2
                total_amount = price * quantity
                entry = [idx, ref_id, in_out, date.strftime("%Y-%m-%d"), name, domain, price, quantity, total_amount, comments]
                sheet.update(f'A{idx}:J{idx}', [entry])
                st.success("Entry updated successfully.")

def delete_entry():
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    
    ref_id = st.selectbox("Select Reference ID to delete", df['Reference ID'].values)
    
    if st.button("Delete Entry"):
        if ref_id in df['Reference ID'].values:
            idx = df.index[df['Reference ID'] == ref_id].tolist()[0] + 2
            sheet.delete_row(idx)
            st.success("Entry deleted successfully.")
        else:
            st.error("Reference ID not found.")

def generate_report():
    st.header("Monthly Report")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    monthly_report = df.groupby(['Month', 'In/Out'])['Total Amount'].sum().unstack().fillna(0)
    st.write(monthly_report)

def main():
    st.title("Google Sheets Entry Manager")

    menu = ["Add Entry", "Read Entries", "Update Entry", "Delete Entry", "Generate Report"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Entry":
        add_entry()
    elif choice == "Read Entries":
        read_entries()
    elif choice == "Update Entry":
        update_entry()
    elif choice == "Delete Entry":
        delete_entry()
    elif choice == "Generate Report":
        generate_report()

if __name__ == "__main__":
    main()
