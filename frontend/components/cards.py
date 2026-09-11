import streamlit as st


def metric_card(title, value, description):
    with st.container(border=True):
        st.caption(title)
        st.metric(label="", value=value)
        st.caption(description)