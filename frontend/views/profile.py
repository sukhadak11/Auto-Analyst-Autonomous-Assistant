import streamlit as st

from components.header import show_header


def show_profile():

    show_header(
        "Profile",
        "View your account information and access settings.",
    )

    st.subheader("Account Information")

    with st.container(border=True):

        st.text_input(
            "Email",
            value=st.session_state.user_email,
            disabled=True,
        )

        st.text_input(
            "Role",
            value=st.session_state.user_role.title(),
            disabled=True,
        )

    st.write("")

    st.subheader("Access & Permissions")

    with st.container(border=True):

        if st.session_state.user_role == "admin":

            st.markdown("###  Administrator")

            st.write(
                "You have administrator access."
            )

        else:

            st.markdown("### User")

            st.write(
                "You have standard user access."
            )