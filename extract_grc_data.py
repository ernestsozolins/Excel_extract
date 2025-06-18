import streamlit as st
import pandas as pd
import pdfplumber
import re

st.title("GRC Panel Specification Extractor")

uploaded_file = st.file_uploader("Upload a PDF, Excel, or CSV file", type=["pdf", "xlsx", "xls", "csv"])

def extract_from_pdf(file):
    data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            # Regex to find lines like: Grc.L 1 175 3235 525
            matches = re.findall(r'(Grc\.[\w\.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', text)
            for match in matches:
                unit_type, count, height, width, depth = match
                data.append({
                    "Type": unit_type,
                    "Count": int(count),
                    "Height": int(height),
                    "Width": int(width),
                    "Depth": int(depth)
                })
    return pd.DataFrame(data)

def extract_from_excel_or_csv(file):
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file)
    # Try to standardize column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    # Attempt to map columns
    col_map = {}
    for col in df.columns:
        if 'type' in col or 'tips' in col:
            col_map['Type'] = col
        elif 'count' in col or 'skaits' in col:
            col_map['Count'] = col
        elif 'height' in col or 'augstums' in col:
            col_map['Height'] = col
        elif 'width' in col or 'platums' in col or 'garums' in col:
            col_map['Width'] = col
        elif 'depth' in col or 'dzi\u013cums' in col:
            col_map['Depth'] = col

    if len(col_map) < 5:
        st.error("Could not detect all necessary columns.")
        return pd.DataFrame()

    extracted = df[[col_map[k] for k in ['Type', 'Count', 'Height', 'Width', 'Depth']]]
    extracted.columns = ['Type', 'Count', 'Height', 'Width', 'Depth']
    return extracted.dropna()

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == 'pdf':
        df = extract_from_pdf(uploaded_file)
    else:
        df = extract_from_excel_or_csv(uploaded_file)

    if not df.empty:
        st.success("Data extracted successfully!")
        st.dataframe(df)
    else:
        st.warning("No data extracted or incorrect file format.")
