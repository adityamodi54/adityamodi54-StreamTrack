import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import uuid

# Load credentials from Streamlit secrets
credentials_dict = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict)

# Google Sheets authentication
client = gspread.authorize(creds)

# Open the main Google Sheet (the document)
spreadsheet = client.open("Streamlit_track")

# User credentials (for demonstration purposes; replace with a secure method in production)
user_data = {
    "adit": "shruti",
    "vikram": "rikita",
    "ghanshyam": "jalpa"
}

# Simple authentication
def authenticate(username, password):
    if username in user_data and user_data[username] == password:
        return True
    return False

# Function to get or create a user-specific sheet
def get_user_sheet(username):
    try:
        # Try to open an existing sheet
        return spreadsheet.worksheet(username)
    except gspread.exceptions.WorksheetNotFound:
        # If the sheet does not exist, create it
        sheet = spreadsheet.add_worksheet(title=username, rows="1000", cols="10")
        # Initialize the sheet with headers
        sheet.append_row(["Sr No", "Reference ID", "In/Out", "Date", "Name", "Domain", "Price", "Quantity", "Total Amount", "Comments"])
        return sheet

# Function to generate a unique ID
def get_unique_id():
    return str(uuid.uuid4())

# Function to add an entry
def add_entry(username):
    sheet = get_user_sheet(username)
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

# Function to read entries
def read_entries(username):
    sheet = get_user_sheet(username)
    st.header("Entries")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    st.write(df)
    if st.button('Export to CSV'):
        df.to_csv(f'{username}_exported_data.csv', index=False)
        st.success(f"Data exported to '{username}_exported_data.csv'.")

# Function to update an entry
def update_entry(username):
    sheet = get_user_sheet(username)
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

# Function to delete an entry
def delete_entry(username):
    sheet = get_user_sheet(username)
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

# Function to generate a report
def generate_report(username):
    sheet = get_user_sheet(username)
    st.header("Monthly Report")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    monthly_report = df.groupby(['Month', 'In/Out'])['Total Amount'].sum().unstack().fillna(0)
    st.write(monthly_report)

# Main function to handle the Streamlit app
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.sidebar.header("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_button = st.sidebar.button("Login")

        if login_button:
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.sidebar.success(f"Welcome {username}")
            else:
                st.sidebar.error("Invalid username or password")

    if st.session_state.logged_in:
        st.sidebar.title(f"Welcome {st.session_state.username}")

        menu = ["Add Entry", "Read Entries", "Update Entry", "Delete Entry", "Generate Report"]
        choice = st.sidebar.selectbox("Menu", menu)

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.sidebar.success("You have been logged out.")

        if choice == "Add Entry":
            add_entry(st.session_state.username)
        elif choice == "Read Entries":
            read_entries(st.session_state.username)
        elif choice == "Update Entry":
            update_entry(st.session_state.username)
        elif choice == "Delete Entry":
            delete_entry(st.session_state.username)
        elif choice == "Generate Report":
            generate_report(st.session_state.username)

if __name__ == "__main__":
    main()
