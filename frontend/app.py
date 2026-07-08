from __future__ import annotations

import requests
import streamlit as st

from backend.app.core.config import get_settings


settings = get_settings()
BACKEND_URL = f"http://{settings.backend_host}:{settings.backend_port}"

st.set_page_config(page_title="InsightHub", layout="wide")
st.title("InsightHub")
st.caption("Enterprise Research Knowledge Assistant")

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
    st.session_state.user = None

with st.sidebar:
    st.header("Connection")
    st.write(BACKEND_URL)
    if st.session_state.auth_token:
        st.success(f"Signed in as {st.session_state.user['full_name']}")
    else:
        st.info("Not signed in")

if not st.session_state.auth_token:
    st.subheader("Login")
    with st.form("login_form"):
        login = st.text_input("Username or email", value="acme_admin")
        password = st.text_input("Password", type="password", value="Password123!")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"login": login, "password": password},
            timeout=10,
        )
        if response.ok:
            payload = response.json()
            st.session_state.auth_token = payload["token"]
            st.session_state.user = payload
            st.rerun()
        else:
            st.error(response.json().get("detail", "Login failed"))
else:
    st.success("Backend and frontend are connected.")
    st.write("User context:")
    st.json(st.session_state.user)
    if st.button("Sign out"):
        st.session_state.auth_token = None
        st.session_state.user = None
        st.rerun()
