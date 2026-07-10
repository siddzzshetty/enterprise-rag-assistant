from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from backend.app.core.config import get_settings


settings = get_settings()
BACKEND_URL = f"http://{settings.backend_host}:{settings.backend_port}"
DEFAULT_DEMO_LOGIN = "local_admin"
DEFAULT_DEMO_PASSWORD = "Password123!"

st.set_page_config(page_title="InsightHub", layout="wide", page_icon="IH")

st.markdown(
    """
    <style>
    .app-shell {
        padding-top: 0.5rem;
    }
    .hero {
        background: linear-gradient(135deg, rgba(19, 34, 56, 0.96), rgba(30, 58, 86, 0.95));
        color: white;
        border-radius: 1.25rem;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 18px 60px rgba(0, 0, 0, 0.18);
    }
    .card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><h1 style="margin:0;">InsightHub</h1><p style="margin:0.35rem 0 0 0;">Enterprise Research Knowledge Assistant</p></div>', unsafe_allow_html=True)


def init_state() -> None:
    defaults: dict[str, Any] = {
        "auth_token": None,
        "user": None,
        "client": None,
        "projects": [],
        "selected_project_id": None,
        "selected_project": None,
        "project_stats": None,
        "dashboard_summary": None,
        "project_documents": [],
        "chat_history": [],
        "export_files": {},
        "workspace_error": None,
        "last_synced_at": None,
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
        timeout=90,
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
    st.session_state.dashboard_summary = api_request("GET", "/dashboard")
    if st.session_state.projects and st.session_state.selected_project_id is None:
        st.session_state.selected_project_id = st.session_state.projects[0]["id"]
    sync_selected_project()
    st.session_state.last_synced_at = datetime.utcnow().isoformat(timespec="seconds")


def create_project() -> None:
    project_name = st.session_state.get("new_project_name", "").strip()
    project_description = st.session_state.get("new_project_description", "").strip()
    project_slug = st.session_state.get("new_project_slug", "").strip()
    payload: dict[str, Any] = {"name": project_name, "description": project_description}
    if project_slug:
        payload["slug"] = project_slug
    created_project = api_request("POST", "/projects", json_payload=payload)
    st.session_state.new_project_name = ""
    st.session_state.new_project_description = ""
    st.session_state.new_project_slug = ""
    refresh_workspace()
    st.session_state.selected_project_id = created_project["id"]
    sync_selected_project()


def fetch_export_file(export_kind: str) -> tuple[bytes, str]:
    selected_project = st.session_state.selected_project
    if not selected_project:
        raise RuntimeError("No project selected")
    response = requests.get(
        f"{BACKEND_URL}/projects/{selected_project['id']}/exports/{export_kind}",
        headers={"X-Auth-Token": st.session_state.auth_token},
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(response.text)
    content_disposition = response.headers.get("Content-Disposition", "")
    filename = f"{selected_project['slug']}_{export_kind}.xlsx"
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[-1].strip('"')
    return response.content, filename


def delete_project_action(project_id: int) -> None:
    """Delete a project and refresh workspace."""
    api_request("DELETE", f"/projects/{project_id}")
    st.session_state.selected_project_id = None
    st.session_state.selected_project = None
    st.session_state.project_stats = None
    st.session_state.project_documents = []
    st.session_state.chat_history = []
    refresh_workspace()


def delete_document_action(project_id: int, document_id: int) -> None:
    """Delete a document and refresh project data."""
    api_request("DELETE", f"/projects/{project_id}/documents/{document_id}")
    sync_selected_project()


def delete_client_action(client_id: int) -> None:
    """Delete a client and all associated data."""
    api_request("DELETE", f"/clients/{client_id}")
    # Sign out since our session belongs to the deleted client
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


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
    st.session_state.export_files = {}


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
        st.caption(f"Client ID: {st.session_state.client['id']}")
        st.caption(f"Last synced: {st.session_state.last_synced_at or 'never'}")
        refresh_clicked = st.button("Refresh workspace", use_container_width=True)
        if refresh_clicked:
            with st.spinner("Refreshing project data..."):
                refresh_workspace()
                st.rerun()
        if st.session_state.projects:
            project_names = [project["name"] for project in st.session_state.projects]
            current_index = 0
            if st.session_state.selected_project_id is not None:
                for index, project in enumerate(st.session_state.projects):
                    if project["id"] == st.session_state.selected_project_id:
                        current_index = index
                        break
            selected_label = st.selectbox("Active project", project_names, index=current_index)
            selected_project = next(project for project in st.session_state.projects if project["name"] == selected_label)
            if selected_project["id"] != st.session_state.selected_project_id:
                st.session_state.selected_project_id = selected_project["id"]
                sync_selected_project()
                st.rerun()
            # Delete project button
            delete_project_clicked = st.button(
                f"🗑️ Delete '{selected_project['name']}'",
                use_container_width=True,
                type="secondary",
            )
            if delete_project_clicked:
                if st.session_state.get("confirm_delete_project") != selected_project["id"]:
                    st.session_state.confirm_delete_project = selected_project["id"]
                    st.warning(f"Click again to confirm deletion of '{selected_project['name']}' and all its data.")
                    st.rerun()
                else:
                    try:
                        with st.spinner("Deleting project..."):
                            delete_project_action(selected_project["id"])
                        st.success("Project deleted successfully.")
                        st.session_state.confirm_delete_project = None
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                        st.session_state.confirm_delete_project = None
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
                "dashboard_summary",
                "project_documents",
                "chat_history",
                "export_files",
                "workspace_error",
                "last_synced_at",
            ]:
                if key == "projects":
                    st.session_state[key] = []
                elif key in {"chat_history", "export_files"}:
                    st.session_state[key] = [] if key == "chat_history" else {}
                else:
                    st.session_state[key] = None
            st.rerun()
        st.divider()
        st.subheader("Create project")
        with st.form("create_project_form", clear_on_submit=False):
            st.text_input("Project name", key="new_project_name", placeholder="My Research Project")
            st.text_input("Project slug (optional)", key="new_project_slug", placeholder="my-research-project")
            st.text_area("Description (optional)", key="new_project_description", placeholder="What this project is for")
            create_clicked = st.form_submit_button("Create project")
        if create_clicked:
            try:
                with st.spinner("Creating project..."):
                    create_project()
                st.success("Project created successfully.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        st.divider()
        st.subheader("Create new client")
        with st.form("create_client_form", clear_on_submit=False):
            st.text_input("Client name", key="new_client_name", placeholder="Acme Corp")
            st.text_input("Client slug (optional)", key="new_client_slug", placeholder="acme-corp")
            st.text_input("Admin username (optional)", key="new_client_admin", placeholder="admin", value="admin")
            st.text_input("Admin password (optional)", key="new_client_password", placeholder="Password123!", type="password")
            create_client_clicked = st.form_submit_button("Create client")
        if create_client_clicked:
            try:
                with st.spinner("Creating client..."):
                    payload = {
                        "name": st.session_state.get("new_client_name", "").strip(),
                        "slug": st.session_state.get("new_client_slug", "").strip() or None,
                        "admin_username": st.session_state.get("new_client_admin", "admin").strip(),
                        "admin_password": st.session_state.get("new_client_password") or None,
                    }
                    result = api_request("POST", "/clients", json_payload=payload)
                    st.success(result["message"])
                    st.session_state.new_client_name = ""
                    st.session_state.new_client_slug = ""
                    st.session_state.new_client_admin = "admin"
                    st.session_state.new_client_password = ""
                    st.rerun()
            except Exception as exc:
                st.error(str(exc))
    else:
        st.info("Not signed in")

if not st.session_state.auth_token:
    st.subheader("Login")
    st.caption("Use the local admin account created during database initialization.")
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
    st.info("Create a project in the sidebar, then select it to load your own documents.")
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

summary_tab, documents_tab, upload_tab, chat_tab, exports_tab = st.tabs(["Overview", "Documents", "Upload", "Chat", "Exports"])

with summary_tab:
    st.write(f"Client: **{st.session_state.client['name']}**")
    col_slug, col_del = st.columns([3, 1])
    with col_slug:
        st.write(f"Project slug: `{selected_project['slug']}`")
    with col_del:
        delete_client_key = "delete_this_client"
        if st.button(f"🗑️ Delete client '{st.session_state.client['name']}'", key=delete_client_key, type="secondary"):
            if st.session_state.get(f"confirm_{delete_client_key}") is True:
                try:
                    with st.spinner("Deleting client and all associated data..."):
                        delete_client_action(st.session_state.client["id"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            else:
                st.session_state[f"confirm_{delete_client_key}"] = True
                st.warning(f"⚠️ Click again to confirm permanent deletion of client '{st.session_state.client['name']}' and ALL its projects, documents, and data.")
    dashboard_summary = st.session_state.dashboard_summary or {}
    dashboard_metrics = st.columns(4)
    dashboard_metrics[0].metric("Total clients", dashboard_summary.get("total_clients", 0))
    dashboard_metrics[1].metric("Total projects", dashboard_summary.get("total_projects", 0))
    dashboard_metrics[2].metric("Total retrievals", dashboard_summary.get("total_retrievals", 0))
    dashboard_metrics[3].metric("Total chats", dashboard_summary.get("total_chats", 0))
    if dashboard_summary.get("category_counts"):
        category_frame = pd.DataFrame(
            [{"category": category, "count": count} for category, count in dashboard_summary["category_counts"].items()]
        )
        fig = px.bar(category_frame, x="category", y="count", title="Client category mix")
        st.plotly_chart(fig, use_container_width=True)
    if stats.get("recent_uploads"):
        st.markdown("### Recent uploads")
        st.dataframe(stats["recent_uploads"], use_container_width=True, hide_index=True)
    if dashboard_summary.get("recent_queries"):
        st.markdown("### Recent retrieval activity")
        st.dataframe(dashboard_summary["recent_queries"], use_container_width=True, hide_index=True)
    if dashboard_summary.get("projects"):
        st.markdown("### Project overview")
        st.dataframe(dashboard_summary["projects"], use_container_width=True, hide_index=True)

with documents_tab:
    st.markdown("### Indexed documents")
    if st.session_state.project_documents:
        for doc in st.session_state.project_documents:
            cols = st.columns([3, 1, 1, 1, 1])
            cols[0].write(f"**{doc['file_name']}**")
            cols[1].write(doc["category"])
            cols[2].write(doc["status"])
            cols[3].write(f"{doc['chunk_count']} chunks")
            delete_doc_key = f"delete_doc_{doc['id']}"
            if cols[4].button("🗑️", key=delete_doc_key):
                if st.session_state.get(f"confirm_{delete_doc_key}") is True:
                    try:
                        delete_document_action(selected_project["id"], doc["id"])
                        st.success(f"Deleted {doc['file_name']}")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                else:
                    st.session_state[f"confirm_{delete_doc_key}"] = True
                    st.warning(f"Click 🗑️ again to confirm deletion of '{doc['file_name']}'")
        st.caption("Click the 🗑️ button once to select, then again to confirm deletion.")
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
            with st.spinner("Extracting, chunking, and indexing document..."):
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
            with st.spinner("Retrieving and verifying grounded response..."):
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
            with st.chat_message("user"):
                st.markdown(entry.get("original_query", entry["query"]))
            with st.chat_message("assistant"):
                st.markdown(entry["answer"])
                status_label = entry.get("verification_status", "pending")
                notes = entry.get("verification_notes", "")
                st.caption(f"Verification: {status_label}" + (f" | {notes}" if notes else ""))
                if entry.get("sources"):
                    with st.expander("Sources"):
                        for source in entry["sources"]:
                            st.write(
                                f"{source['document_name']} | {source['category']} | chunk {source['chunk_index']} | score {source['score']}"
                            )
                            st.caption(source.get("snippet", ""))
    else:
        st.info("No chat history yet.")

with exports_tab:
    st.markdown("### Export project knowledge")
    export_columns = st.columns(3)
    with export_columns[0]:
        if st.button("Prepare chat export", use_container_width=True):
            try:
                st.session_state.export_files["chat"] = fetch_export_file("chat")
            except Exception as exc:
                st.error(str(exc))
        if "chat" in st.session_state.export_files:
            chat_bytes, chat_name = st.session_state.export_files["chat"]
            st.download_button(
                "Download chat export file",
                data=chat_bytes,
                file_name=chat_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with export_columns[1]:
        if st.button("Prepare summary export", use_container_width=True):
            try:
                st.session_state.export_files["summary"] = fetch_export_file("summary")
            except Exception as exc:
                st.error(str(exc))
        if "summary" in st.session_state.export_files:
            summary_bytes, summary_name = st.session_state.export_files["summary"]
            st.download_button(
                "Download summary export file",
                data=summary_bytes,
                file_name=summary_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with export_columns[2]:
        if st.button("Prepare context export", use_container_width=True):
            try:
                st.session_state.export_files["context"] = fetch_export_file("context")
            except Exception as exc:
                st.error(str(exc))
        if "context" in st.session_state.export_files:
            context_bytes, context_name = st.session_state.export_files["context"]
            st.download_button(
                "Download context export file",
                data=context_bytes,
                file_name=context_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    st.caption("Exports are generated from the selected project and include citations, summaries, or supporting context depending on the export type.")
