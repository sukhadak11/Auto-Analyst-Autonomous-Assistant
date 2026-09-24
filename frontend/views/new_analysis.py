import streamlit as st
import pandas as pd
import requests

from components.header import show_header
from services.api_client import API_URL, get_auth_headers


def upload_analysis(uploaded_file, question, target_column=None):

    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        }

        data = {
            "question": question,
        }

        if target_column:
            data["target_column"] = target_column

        response = requests.post(
            f"{API_URL}/upload",
            headers=get_auth_headers(),
            files=files,
            data=data,
            timeout=30,
        )

        if response.status_code == 200:
            return response.json(), None

        if response.status_code == 401:
            return None, (
                "Your session has expired. Please log in again."
            )

        try:
            error = response.json().get(
                "detail",
                "Unable to start analysis."
            )
        except Exception:
            error = "Unable to start analysis."

        return None, error

    except Exception as e:
        return None, (
            f"Unable to connect to AutoAnalyst API: {str(e)}"
        )


def show_new_analysis():

    show_header(
        "New Analysis",
        "Upload your dataset and describe what you want to understand.",
    )

    # ========================================================
    # 1. UPLOAD DATASET
    # ========================================================

    st.subheader("1. Upload Dataset")

    st.caption(
        "Upload the CSV or Excel file you want AutoAnalyst to analyze."
    )

    uploaded_file = st.file_uploader(
        "Choose your dataset",
        type=["csv", "xlsx"],
        label_visibility="collapsed",
    )

    preview_df = None

    if uploaded_file:

        file_size_mb = uploaded_file.size / (1024 * 1024)

        st.success(
            f"✓ {uploaded_file.name} • {file_size_mb:.2f} MB"
        )

        try:

            if uploaded_file.name.lower().endswith(".csv"):
                preview_df = pd.read_csv(uploaded_file)
            else:
                preview_df = pd.read_excel(uploaded_file)

            # ------------------------------------------------
            # Dataset Preview
            # ------------------------------------------------

            with st.expander(
                "Preview dataset",
                expanded=False,
            ):

                st.caption(
                    f"{preview_df.shape[0]:,} rows × "
                    f"{preview_df.shape[1]:,} columns"
                )

                # Create a copy only for Streamlit display.
                # This prevents PyArrow errors caused by
                # mixed-type object columns.
                preview_display = preview_df.head(10).copy()

                for col in preview_display.columns:

                    if preview_display[col].dtype == "object":

                        preview_display[col] = (
                            preview_display[col]
                            .astype("string")
                        )

                st.dataframe(
                    preview_display,
                    width="stretch",
                    hide_index=True,
                )

        except Exception as e:

            st.warning(
                f"Unable to preview the dataset: {e}"
            )

    st.write("")

    # ========================================================
    # 2. ASK QUESTION
    # ========================================================

    st.subheader("2. Ask Your Question")

    question = st.text_area(
        "Business Question",
        placeholder=(
            "Example: What are the key factors influencing "
            "the target outcome?"
        ),
        height=150,
        label_visibility="collapsed",
    )

    st.caption(
        "You can ask about patterns, trends, relationships, "
        "comparisons, predictions, or other insights."
    )

    st.write("")

    # ========================================================
    # 3. TARGET COLUMN
    # ========================================================

    target_column = None

    if preview_df is not None:

        st.subheader("3. Target Column")

        target_options = (
            ["Auto-detect"]
            + preview_df.columns.tolist()
        )

        selected_target = st.selectbox(
            "Select target column",
            target_options,
        )

        if selected_target != "Auto-detect":
            target_column = selected_target

    st.write("")

    # ========================================================
    # START ANALYSIS
    # ========================================================

    if st.button(
        "Start Analysis",
        type="primary",
        width="stretch",
        key="start_analysis",
    ):

        # ----------------------------------------------------
        # Validate dataset
        # ----------------------------------------------------

        if uploaded_file is None:

            st.warning(
                "Please upload a dataset first."
            )

            return

        # ----------------------------------------------------
        # Validate question
        # ----------------------------------------------------

        if not question.strip():

            st.warning(
                "Please enter an analysis question."
            )

            return

        # ----------------------------------------------------
        # Start analysis
        # ----------------------------------------------------

        with st.spinner(
            "Uploading dataset and starting analysis..."
        ):

            result, error = upload_analysis(
                uploaded_file=uploaded_file,
                question=question.strip(),
                target_column=target_column,
            )

        # ----------------------------------------------------
        # Handle API error
        # ----------------------------------------------------

        if error:

            st.error(error)

            return

        # ----------------------------------------------------
        # Get Job ID
        # ----------------------------------------------------

        job_id = result.get("job_id")

        if not job_id:

            st.error(
                "Analysis started, but no job ID was returned."
            )

            return

        # ----------------------------------------------------
        # Navigate to Job Details
        # ----------------------------------------------------

        st.session_state.selected_job = job_id
        st.session_state.page = "Job Details"

        st.success(
            f"Analysis started successfully. Job ID: {job_id}"
        )

        st.rerun()