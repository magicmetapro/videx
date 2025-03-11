import streamlit as st
import cv2
import os
import zipfile
import tempfile
import numpy as np
from io import BytesIO

def extract_frames(video_path, output_dir, frame_interval=30):
    cap = cv2.VideoCapture(video_path)
    count = 0
    frame_count = 0
    frames_info = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if count % frame_interval == 0:
            frame_filename = os.path.join(output_dir, f"frame_{frame_count:04d}.png")
            cv2.imwrite(frame_filename, frame)
            
            # Generate a simple description based on image properties
            avg_color = np.mean(frame, axis=(0, 1))
            frame_description = f"Frame {frame_count}: A scene with predominant colors ({avg_color[2]:.0f} red, {avg_color[1]:.0f} green, {avg_color[0]:.0f} blue)."
            frames_info.append(frame_description)
            
            frame_count += 1
        
        count += 1
    
    cap.release()
    return frame_count, frames_info

def create_zip_from_frames(output_dir):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    zip_buffer.seek(0)
    return zip_buffer

def generate_detailed_prompt(frames_info):
    prompt = "This video consists of the following scenes:\n\n"
    for info in frames_info:
        prompt += f"- {info}\n"
    prompt += "\nUse this description to generate a realistic and detailed text-to-video AI reconstruction."
    return prompt

st.title("Video Frame Extractor and Prompt Generator")
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "mpeg", "mpg"])
frame_interval = st.number_input("Frame Interval", min_value=1, value=30, step=1)

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_video:
        temp_video.write(uploaded_file.read())
        temp_video_path = temp_video.name
    
    with tempfile.TemporaryDirectory() as output_dir:
        frame_count, frames_info = extract_frames(temp_video_path, output_dir, frame_interval)
        
        if frame_count > 0:
            zip_buffer = create_zip_from_frames(output_dir)
            prompt_text = generate_detailed_prompt(frames_info)
            
            st.success(f"Extraction complete! {frame_count} frames extracted.")
            st.download_button("Download ZIP", zip_buffer, file_name="frames.zip", mime="application/zip")
            
            st.subheader("Generated Prompt for AI Video Generation:")
            st.text_area("Detailed Prompt", prompt_text, height=200)
        else:
            st.error("No frames extracted. Try a different interval or video file.")
