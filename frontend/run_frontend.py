import streamlit.web.cli as stcli


if __name__ == "__main__":
    stcli.main([
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port=8501",
    ])
