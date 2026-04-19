#!/bin/bash
cd /Users/kiraz/Projects/aliye
source venv/bin/activate
streamlit run aliye_dashboard.py --server.port 8504 --server.headless true
