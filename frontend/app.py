from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
import streamlit as st

from backend.app.core.config import get_settings


settings = get_settings()
BACKEND_URL = f"http://{settings.backend_host}:{settings.backend_port}"
DEFAULT_DEMO_LOGIN = "acme_admin"
DEFAULT_DEMO_PASSWORD = "Password123!"

st.set_page_config(page_title="InsightHub", layout="wide", page_icon="IH")
st.title("InsightHub")
st.caption("Enterprise Research Knowledge Assistant")


def init_state() -> None:
    defaults: dict[str, Any] = {
        "auth_token": None,
        "user": None,
        "client": None,
        "projects": [],
        "selected_project_id": None,
        "selected_project": None,
        "project_stats": None,
        "project_documents": [],
        "chat_history": [],
        "workspace_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def api_request(method: str, path: str, *, json_payload: dict[str, Any] | None = None, files: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {}
    if st.session_state.auth_token:
        headers["X-Auth-Token"] = st.session_state.auth_token
    response = requests.request(
        method,
        f"{BACKEND_URL}{path}",
        headers=headers,
        json=json_payload,
        files=files,
        timeout=60,
    )
    if response.ok:
        return response.json()
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    raise RuntimeError(detail)


def refresh_workspace() -> None:
    workspace = api_request("GET", "/projects")
    st.session_state.client = workspace["client"]
    st.session_state.projects = workspace["items"]
    if st.session_state.projects and st.session_state.selected_project_id is None:
        st.session_state.selected_project_id = st.session_state.projects[0]["id"]
    sync_selected_project()


def sync_selected_project() -> None:
    selected_id = st.session_state.selected_project_id
    if not selected_id:
        st.session_state.selected_project = None
        st.session_state.project_stats = None
        st.session_state.project_documents = []
        return
    st.session_state.selected_project = api_request("GET", f"/projects/{selected_id}")
    st.session_state.project_stats = api_request("GET", f"/projects/{selected_id}/stats")
    st.session_state.project_documents = api_request("GET", f"/projects/{selected_id}/documents")["items"]


if st.session_state.auth_token and not st.session_state.projects:
    try:
        refresh_workspace()
    except Exception as exc:
        st.session_state.workspace_error = str(exc)


with st.sidebar:
    st.header("Workspace")
    st.write(BACKEND_URL)
    if st.session_state.auth_token:
        st.success(f"Signed in as {st.session_state.user['full_name']}")
        if st.session_state.client:
            st.write(f"Client: {st.session_state.client['name']}")
        if st.session_state.projects:
            project_options = {f"{project['name']}": project for project in st.session_state.projects}
            selected_label = st.selectbox(
                "Active project",
                list(project_options.keys()),
                index=0 if st.session_state.selected_project_id is None else list(project_options.keys()).index(
                    next(
                        label
                        for label, project in project_options.items()
                        if project["id"] == st.session_state.selected_project_id
                    )
                ),
            )
            selected_project = project_options[selected_label]
            if selected_project["id"] != st.session_state.selected_project_id:
                st.session_state.selected_project_id = selected_project["id"]
                sync_selected_project()
                st.rerun()
        else:
            st.info("No projects available for this account.")
        if st.button("Sign out", use_container_width=True):
            for key in [
                "auth_token",
                "user",
                "client",
                "projects",
                "selected_project_id",
                "selected_project",
                "project_stats",
                "project_documents",
                "chat_history",
                "workspace_error",
            ]:
                st.session_state[key] = None if key not in {"projects", "chat_history"} else ([] if key == "projects" else [])
            st.rerun()
    else:
        st.info("Not signed in")

if not st.session_state.auth_token:
    st.subheader("Login")
    st.caption("Demo accounts: acme_admin / Password123! or northstar_admin / Password123!")
    with st.form("login_form"):
        login = st.text_input("Username or email", value=DEFAULT_DEMO_LOGIN)
        password = st.text_input("Password", type="password", value=DEFAULT_DEMO_PASSWORD)
        submitted = st.form_submit_button("Sign in")

    if submitted:
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"login": login, "password": password},
                timeout=30,
            )
            if not response.ok:
                try:
                    st.error(response.json().get("detail", "Login failed"))
                except ValueError:
                    st.error(response.text or "Login failed")
            else:
                st.session_state.auth_token = response.json()["token"]
                st.session_state.user = response.json()
                st.session_state.projects = []
                st.session_state.client = None
                st.session_state.selected_project_id = None
                st.session_state.selected_project = None
                st.session_state.project_stats = None
                st.session_state.project_documents = []
                refresh_workspace()
                st.rerun()
        except Exception as exc:
            st.error(str(exc))
    st.stop()

if st.session_state.workspace_error:
    st.error(st.session_state.workspace_error)

selected_project = st.session_state.selected_project
if not selected_project:
    st.info("Select a project in the sidebar to load its knowledge base.")
    st.stop()

st.subheader(selected_project["name"])
st.write(selected_project["description"])

stats = st.session_state.project_stats or {}
metric_columns = st.columns(4)
metric_columns[0].metric("Documents", stats.get("document_count", 0))
metric_columns[1].metric("Chunks", stats.get("chunk_count", 0))
metric_columns[2].metric("Chats", stats.get("chat_count", 0))
metric_columns[3].metric("Categories", len(stats.get("category_counts", {})))

if stats.get("category_counts"):
    st.caption("Document categories")
    st.write(stats["category_counts"])

overview_tab, documents_tab, upload_tab, chat_tab = st.tabs(["Overview", "Documents", "Upload", "Chat"])

with overview_tab:
    st.write(f"Client: **{st.session_state.client['name']}**")
    st.write(f"Project slug: `{selected_project['slug']}`")
    if stats.get("recent_uploads"):
        st.markdown("### Recent uploads")
        st.dataframe(stats["recent_uploads"], use_container_width=True, hide_index=True)

with documents_tab:
    st.markdown("### Indexed documents")
    if st.session_state.project_documents:
        st.dataframe(st.session_state.project_documents, use_container_width=True, hide_index=True)
    else:
        st.info("No documents uploaded yet.")

with upload_tab:
    st.markdown("### Upload research assets")
    upload_file = st.file_uploader(
        "Choose a PDF, Word, PowerPoint, Excel, CSV, text, or audio file",
        type=["pdf", "docx", "pptx", "csv", "xlsx", "xls", "txt", "md", "json", "wav", "mp3", "m4a", "ogg", "flac", "aac"],
    )
    if st.button("Process upload", disabled=upload_file is None, use_container_width=True):
        try:
            upload_result = api_request(
                "POST",
                f"/projects/{selected_project['id']}/documents/upload",
                files={"file": (upload_file.name, upload_file.getvalue(), upload_file.type or "application/octet-stream")},
            )
            st.success(f"Indexed {upload_result['file_name']} as {upload_result['category']} with {upload_result['chunk_count']} chunks.")
            sync_selected_project()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

with chat_tab:
    st.markdown("### Ask the selected project")
    question = st.text_input("Question", placeholder="What did respondents say about pricing?")
    if st.button("Ask", use_container_width=True, disabled=not question.strip()):
        try:
            response = api_request(
                "POST",
                f"/projects/{selected_project['id']}/chat/ask",
                json_payload={"question": question},
            )
            st.session_state.chat_history.insert(0, response)
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.chat_history:
        for entry in st.session_state.chat_history:
            with st.container(border=True):
                st.markdown(f"**Query:** {entry['query']}")
                st.write(entry["answer"])
                if entry.get("sources"):
                    with st.expander("Sources"):
                        for source in entry["sources"]:
                            st.write(
                                f"{source['document_name']} | {source['category']} | chunk {source['chunk_index']} | score {source['score']}"
                            )
                            st.caption(source.get("snippet", ""))
    else:
        st.info("No chat history yet.")
