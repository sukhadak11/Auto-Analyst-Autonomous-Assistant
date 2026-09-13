import streamlit as st


def show_sidebar():
    """Display sidebar navigation with Logout in a natural position."""

    st.sidebar.title("Auto Analyst")

    views = [
        "Dashboard",
        "New Analysis",
        "My Jobs",
        "Reports",
        "Profile",
    ]

    if st.session_state.get("is_admin", False):
        views.append("Admin Dashboard")

    if st.session_state.get("selected_job"):
        views.append("Job Details")

    for view in views:
        if st.sidebar.button(
            view,
            use_container_width=True,
            key=f"sidebar_{view}",
        ):
            st.session_state["page"] = view
            st.rerun()

    st.sidebar.write("")

    st.sidebar.divider()

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
        key="sidebar_logout",
    ):
        st.session_state.clear()
        st.rerun()