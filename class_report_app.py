import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from collections import defaultdict
from datetime import datetime
import os

# --- Streamlit UI ---
st.title("📄 Monthly Class Report Generator")
month_options = st.multiselect("Select month(s):", ["May 2025", "June 2025", "July 2025"])  # You can generate these dynamically too
generate = st.button("Generate PDF Reports")

if generate and month_options:
    # --- Connect to Google Sheets ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    #creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("pyton share sheet").sheet1
    data = sheet.get_all_records()

    # --- Prepare summaries ---
    summary = defaultdict(lambda: defaultdict(float))

    for row in data:
        student = row.get("Class registration")
        raw_date = str(row.get("Date")).strip()
        raw_hours = str(row.get("Class lenght time in hour")).strip()

        if not student or not raw_date or not raw_hours:
            continue

        try:
            hours = float(raw_hours)
        except:
            continue

        try:
            date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        except:
            try:
                date_obj = datetime.strptime(raw_date, "%d/%m/%Y")
            except:
                continue

        month_str = date_obj.strftime("%B %Y")
        summary[month_str][student] += hours

    # --- Create PDFs ---
    for month in month_options:
        if month not in summary:
            st.warning(f"No data found for {month}")
            continue

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Class Hours - {month}", ln=True, align='C')
        pdf.ln(10)

        for student, hours in summary[month].items():
            pdf.cell(200, 10, txt=f"{student}: {hours:.1f} hours", ln=True)

        today = datetime.today().strftime("%d %B %Y")
        pdf.ln(10)
        pdf.set_font("Arial", size=10, style='I')
        pdf.cell(200, 10, txt=f"Report generated on {today}", ln=True, align='R')

        filename = f"report_{month.replace(' ', '_')}.pdf"
        pdf.output(filename)
        st.success(f"✅ {filename} created")

        with open(filename, "rb") as f:
            st.download_button(label=f"⬇️ Download {month}", data=f, file_name=filename)

        os.remove(filename)  # Clean up
