import streamlit as st
import io
import contextlib

from backend_logic import (
    find_duplicates_multi_new,
    load_excel_master_dataframe,
    extract_filtered_excel_inputs
)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="ECDV Duplicate Detection Tool",
    layout="centered"
)

st.title("ECDV Duplicate Detection Tool")

st.markdown("""
### Instructions

Two input modes are available:

**Manual Mode**
- Enter new products and their ECDVs
- Enter existing products and their ECDVs

**Excel Mode**
- Upload Excel file
- Enter Code Function
- Enter New Product NFC Dates (one per line)

Each line corresponds to one product.
""")

# =========================================================
# HELPER FUNCTIONS (UI LAYER ONLY)
# =========================================================

def parse_multiline_input(text):
    """
    Converts multiline text input into clean list.
    """
    if not text:
        return []

    return [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]


# ---------------------------------------------------------
# Cache Excel loader (load once per session/day)
# ---------------------------------------------------------
@st.cache_data
def cached_load_excel(uploaded_file):
    return load_excel_master_dataframe(uploaded_file)


# =========================================================
# INPUT MODE SELECTION
# =========================================================

mode = st.radio(
    "Select Input Method",
    ["Manual Input", "Excel Extraction"]
)

st.divider()

# =========================================================
# COMMON INPUTS (NEW PARTS)
# =========================================================

st.subheader("New Products")

new_product_numbers_text = st.text_area(
    "New Product Numbers (one per line)",
    height=150
)

new_ecdvs_text = st.text_area(
    "New Product ECDVs (one per line)",
    height=200
)

new_product_numbers = parse_multiline_input(new_product_numbers_text)
new_ecdvs = parse_multiline_input(new_ecdvs_text)


# =========================================================
# MANUAL MODE
# =========================================================

if mode == "Manual Input":

    st.subheader("Existing Products")

    other_product_numbers_text = st.text_area(
        "Existing Product Numbers (one per line)",
        height=150
    )

    other_ecdvs_text = st.text_area(
        "Existing Product ECDVs (one per line)",
        height=200
    )

    other_product_numbers = parse_multiline_input(other_product_numbers_text)
    other_ecdvs = parse_multiline_input(other_ecdvs_text)

    if st.button("Run Duplicate Check"):

        if not new_product_numbers or not new_ecdvs:
            st.error("Please enter New Product data.")
            st.stop()

        if len(new_product_numbers) != len(new_ecdvs):
            st.error("Mismatch between New Product Numbers and New ECDVs.")
            st.stop()

        if len(other_product_numbers) != len(other_ecdvs):
            st.error("Mismatch between Existing Product Numbers and Existing ECDVs.")
            st.stop()

        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer):
            find_duplicates_multi_new(
                new_ecdvs,
                other_ecdvs,
                new_product_numbers,
                other_product_numbers
            )

        output = buffer.getvalue()

        st.subheader("Results")
        st.text(output)


# =========================================================
# EXCEL MODE
# =========================================================

else:

    st.subheader("Excel Extraction")

    uploaded_file = st.file_uploader(
        "Upload Excel File",
        type=["xlsx"]
    )

    code_function = st.text_input(
        "Code Function"
    )

    new_dates_text = st.text_area(
        "New Product NFC Dates (one per line, YYYY-MM-DD)",
        height=150
    )

    new_dates = parse_multiline_input(new_dates_text)

    if st.button("Run Duplicate Check"):

        if uploaded_file is None:
            st.error("Please upload Excel file.")
            st.stop()

        if not code_function:
            st.error("Enter Code Function.")
            st.stop()

        if not new_product_numbers or not new_ecdvs:
            st.error("Enter New Product data.")
            st.stop()

        if len(new_product_numbers) != len(new_ecdvs):
            st.error("Mismatch between New Product Numbers and New ECDVs.")
            st.stop()

        if len(new_product_numbers) != len(new_dates):
            st.error("Each New Product must have one NFC date.")
            st.stop()

        # ------------------------------------------
        # Load Excel (cached)
        # ------------------------------------------
        df_master = cached_load_excel(uploaded_file)

        other_product_numbers = []
        other_ecdvs = []

        # ------------------------------------------
        # Run extraction for each NFC date
        # ------------------------------------------
        for date in new_dates:

            prod_nums, ecdvs = extract_filtered_excel_inputs(
                df_master=df_master,
                code_function=code_function,
                new_product_NFCdate=date
            )

            other_product_numbers.extend(prod_nums)
            other_ecdvs.extend(ecdvs)

        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer):
            find_duplicates_multi_new(
                new_ecdvs,
                other_ecdvs,
                new_product_numbers,
                other_product_numbers
            )

        output = buffer.getvalue()

        st.subheader("Results")
        st.text(output)