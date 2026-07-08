@echo off
call conda activate insight-hub
python -m streamlit run frontend\app.py --server.port 8501
