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
            matches = re.findall(r'(Grc\.[\w\.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', text)
            for match in matches:
                unit_type, count, height, width, depth = match
                data.append({
                    "Type": unit_type,
                    "Count": int(count),
                    "Height": int(height),
                    "Width": int(width),
                    "Depth": int(depth),
                    "Weight": None  # Optional column
                })
    return pd.DataFrame(data)

def smart_column_mapping(df, row_index=7):
    # Updated to include fallback if detection fails
    mapping = {}
    st.markdown(f"Using row {row_index + 1} for auto-detection of column headers")
    if len(df) > row_index:
        header_row = df.iloc[row_index].astype(str).str.lower()
        for i, val in enumerate(header_row):
            if 'type' in val or 'tips' in val:
                mapping['Type'] = df.columns[i]
            elif 'count' in val or 'qty' in val or 'skaits' in val:
                mapping['Count'] = df.columns[i]
            elif 'height' in val or 'augstums' in val:
                mapping['Height'] = df.columns[i]
            elif 'width' in val or 'platums' in val or 'garums' in val:
                mapping['Width'] = df.columns[i]
            elif 'depth' in val or 'dziļums' in val:
                mapping['Depth'] = df.columns[i]
            elif 'weight' in val or 'svars' in val:
                mapping['Weight'] = df.columns[i]
    else:
        st.info("Could not detect headers in the selected row. Falling back to default column positions.")
        for field, index in [('Type', 0), ('Count', 1), ('Height', 4), ('Width', 5), ('Depth', 6), ('Weight', 2)]:
            mapping[field] = df.columns[index] if len(df.columns) > index else None
    return mapping

def extract_from_excel_or_csv(file):
    # Reverted: Load entire file from top
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file)

    # Clean whitespace from all cells
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df.columns = [str(c).strip() for c in df.columns]

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df, height=500)

    header_row_index = st.number_input("Row number to auto-detect column names from (1-based)", min_value=1, max_value=len(df), value=8) - 1
    mapping = smart_column_mapping(df, row_index=header_row_index)
    st.subheader("Adjust Column Mapping (optional)")
    type_col = st.selectbox("Column for Type", df.columns, index=df.columns.get_loc(mapping['Type']) if mapping.get('Type') in df.columns else 0)
    count_col = st.selectbox("Column for Count", df.columns, index=df.columns.get_loc(mapping['Count']) if mapping.get('Count') in df.columns else 0)
    height_col = st.selectbox("Column for Height", df.columns, index=df.columns.get_loc(mapping['Height']) if mapping.get('Height') in df.columns else 0)
    width_col = st.selectbox("Column for Width", df.columns, index=df.columns.get_loc(mapping['Width']) if mapping.get('Width') in df.columns else 0)
    depth_col = st.selectbox("Column for Depth", df.columns, index=df.columns.get_loc(mapping['Depth']) if mapping.get('Depth') in df.columns else 0)
    weight_col = st.selectbox(
        "Column for Weight (optional)",
        ["None"] + df.columns.tolist(),
        index=(df.columns.get_loc(mapping['Weight']) + 1) if mapping.get('Weight') in df.columns else 0
    )
