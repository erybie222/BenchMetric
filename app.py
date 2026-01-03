import streamlit as st
import tempfile
import cv2
import mediapipe as mp
import main
from main import analyze

from pose_module import PoseDetector


imgW, imgH = 1280, 720


# ... import twojej klasy PoseDetector
st.set_page_config(page_title="AI Coach", layout="wide")
st.title("Bench press analyzer - AI Coach")

uploaded_file = st.file_uploader("Upload your bench press video", type=['mp4', 'mov'])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    tfile.close()
    st.write("Analyzing your video in progress...")
    delay = st.slider("Delay", min_value=0.1, max_value=0.0, value=0.1, step=None, format=None, key=None, help=None,
              on_change=None, args=None, kwargs=None,  disabled=False, label_visibility="visible", width="stretch")
    with st.container(horizontal_alignment='center'):
        analyze(tfile.name, imgW, imgH, True, delay)