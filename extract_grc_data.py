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

def smart_column_mapping(df):
    mapping = {}
    lower_cols = {col.lower(): col for col in df.columns}
    mapping['Type'] = next((lower_cols[c] for c in lower_cols if 'type' in c or 'tips' in c), None)
    mapping['Count'] = next((lower_cols[c] for c in lower_cols if 'count' in c or 'skaits' in c), None)
    mapping['Height'] = next((lower_cols[c] for c in lower_cols if 'height' in c or 'augstums' in c), None)
    mapping['Width'] = next((lower_cols[c] for c in lower_cols if 'width' in c or 'platums' in c or 'garums' in c), None)
    mapping['Depth'] = next((lower_cols[c] for c in lower_cols if 'depth' in c or 'dziļums' in c), None)
    mapping['Weight'] = next((lower_cols[c] for c in lower_cols if 'weight' in c or 'svars' in c), None)
    return mapping

def extract_from_excel_or_csv(file):
    START_ROW = 8  # Data starts at Excel row 9 (0-indexed as 8)  # Skip metadata and header rows, assuming data starts from Excel row 8 (index 7)
    try:
        df = pd.read_excel(file, skiprows=START_ROW)
    except:
        df = pd.read_csv(file, skiprows=START_ROW)

    # Clean whitespace from all cells
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df.columns = [str(c).strip() for c in df.columns]

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df, height=500)

    mapping = smart_column_mapping(df)
    st.subheader("Adjust Column Mapping (optional)")
    type_col = st.selectbox("Column for Type", df.columns, index=df.columns.get_loc(mapping['Type']) if mapping['Type'] and mapping['Type'] in df.columns else 0)
    count_col = st.selectbox("Column for Count", df.columns, index=df.columns.get_loc(mapping['Count']) if mapping['Count'] and mapping['Count'] in df.columns else 0)
    height_col = st.selectbox("Column for Height", df.columns, index=df.columns.get_loc(mapping['Height']) if mapping['Height'] and mapping['Height'] in df.columns else 0)
    width_col = st.selectbox("Column for Width", df.columns, index=df.columns.get_loc(mapping['Width']) if mapping['Width'] and mapping['Width'] in df.columns else 0)
    depth_col = st.selectbox("Column for Depth", df.columns, index=df.columns.get_loc(mapping['Depth']) if mapping['Depth'] and mapping['Depth'] in df.columns else 0)
    weight_col = st.selectbox("Column for Weight (optional)", ["None"] + df.columns.tolist(), index=df.columns.get_loc(mapping['Weight']) + 1 if mapping['Weight'] and mapping['Weight'] in df.columns else 0)

    selected_cols = [type_col, count_col, height_col, width_col, depth_col]
    new_names = ['Type', 'Count', 'Height', 'Width', 'Depth']
    if weight_col != "None":
        selected_cols.append(weight_col)
        new_names.append('Weight')

    try:
        extracted = df[selected_cols]
        extracted.columns = new_names

        # Clean whitespace from selected columns
        extracted = extracted.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Drop fully or partially empty rows and remove rows that are actually headers
        extracted.replace("", pd.NA, inplace=True)
        extracted = extracted.dropna(how='any')

        # Drop rows that contain column-like labels
        extracted = extracted[~extracted.apply(lambda row: all(isinstance(val, str) and any(label.lower() in val.lower() for label in ['type', 'qty', 'height', 'width', 'depth', 'weight']) for val in row), axis=1)]

        # Validate numeric columns
        for col in ['Count', 'Height', 'Width', 'Depth']:
            if not pd.api.types.is_numeric_dtype(extracted[col]):
                st.warning(f"Column '{col}' contains non-numeric values. Please check your data.")

        return extracted
    except Exception as e:
        st.error(f"Failed to extract data using smart column mapping. Error: {e}")
        return pd.DataFrame()

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == 'pdf':
        df = extract_from_pdf(uploaded_file)
    else:
        df = extract_from_excel_or_csv(uploaded_file)

    if not df.empty:
        st.success("Data extracted successfully!")

        # Show full extracted data
        st.subheader("Extracted GRC Panel Data")
        st.dataframe(df)

        # Show total count
        if 'Count' in df.columns:
            total = df['Count'].sum()
            st.markdown(f"**Total Panel Count:** {total}")

        # Allow CSV download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Extracted Data as CSV",
            data=csv,
            file_name='extracted_grc_panels.csv',
            mime='text/csv'
        )
    else:
        st.warning("No data extracted or incorrect file format.")
