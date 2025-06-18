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

def extract_from_excel_or_csv(file):
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file)

    # Clean whitespace from all cells
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    df.columns = [str(c).strip() for c in df.columns]
    st.write("Detected columns:", df.columns.tolist())

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df, height=500)

    st.subheader("Map Columns to Fields")
    type_col = st.selectbox("Select column for Type", df.columns)
    count_col = st.selectbox("Select column for Count", df.columns)
    height_col = st.selectbox("Select column for Height", df.columns)
    width_col = st.selectbox("Select column for Width", df.columns)
    depth_col = st.selectbox("Select column for Depth", df.columns)
    weight_col = st.selectbox("Select column for Weight (optional)", ["None"] + df.columns.tolist())

    try:
        selected_cols = [type_col, count_col, height_col, width_col, depth_col]
        new_names = ['Type', 'Count', 'Height', 'Width', 'Depth']

        if weight_col != "None":
            selected_cols.append(weight_col)
            new_names.append('Weight')

        extracted = df[selected_cols]
        extracted.columns = new_names

        # Clean whitespace from selected columns
        extracted = extracted.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Drop fully or partially empty rows
        extracted.replace("", pd.NA, inplace=True)
        extracted = extracted.dropna(how='any')

        # Validate numeric columns
        for col in ['Count', 'Height', 'Width', 'Depth']:
            if not pd.api.types.is_numeric_dtype(extracted[col]):
                st.warning(f"Column '{col}' contains non-numeric values. Please check your mapping.")

        return extracted
    except:
        st.error("Failed to extract data using selected columns.")
        return pd.DataFrame()

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == 'pdf':
        df = extract_from_pdf(uploaded_file)
    else:
        df = extract_from_excel_or_csv(uploaded_file)

    if not df.empty:
        st.success("Data extracted successfully!")
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
