import streamlit as st
from src.coach_feedback.ui_app import render_ui
st.set_page_config(page_title='Coach Feedback (Python-only)', layout='wide')
render_ui()
