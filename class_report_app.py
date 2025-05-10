import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from collections import defaultdict
from datetime import datetime
import os

# --- Setup credentials using Streamlit secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEET_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- Streamlit UI ---
st.title("📄 Monthly Class Report Generator")
month_options = st.multiselect("Select month(s):", ["May 2025", "June 2025", "July 2025"])
generate = st.button("Generate PDF Reports")

if generate and month_options:
    try:
        sheet = client.open("pyton share sheet").sheet1  # 🔁 Change to match your actual sheet name
        data = sheet.get_all_records()
        st.success(f"Loaded {len(data)} rows from Google Sheet.")
    except Exception as e:
        st.error("Failed to load sheet.")
        st.stop()

    # --- Group data: summary[month][student] = total_hours
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

    # --- Generate PDFs ---
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

        # Add generation date
        pdf.ln(10)
        today = datetime.today().strftime("%d %B %Y")
        pdf.set_font("Arial", size=10, style='I')
        pdf.cell(200, 10, txt=f"Report generated on {today}", ln=True, align='R')

        filename = f"report_{month.replace(' ', '_')}.pdf"
        pdf.output(filename)
        st.success(f"✅ {filename} created")

        with open(filename, "rb") as f:
            st.download_button(label=f"⬇️ Download {month} Report", data=f, file_name=filename)

        os.remove(filename)
