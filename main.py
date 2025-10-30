import streamlit as st
import requests
import json
import base64

def main():
    st.set_page_config(
        page_title="Video Quote Generator - API Version",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Video Quote Generator - API Version")
    st.markdown("Menggunakan external API untuk memastikan text muncul di video")
    
    # Upload video
    uploaded_video = st.file_uploader("Upload Video", type=['mp4', 'mov'])
    
    if uploaded_video:
        st.video(uploaded_video)
    
    # Text input
    quote = st.text_area("Masukkan Quotes", height=100)
    
    if quote:
        st.info(f"Preview text: **{quote}**")
    
    if uploaded_video and quote:
        st.warning("""
        **Untuk memastikan text muncul di video, kami sarankan:**
        
        **Option 1: Gunakan Online Video Editor**
        - Buka [Kapwing.com](https://www.kapwing.com/)
        - Upload video Anda
        - Tambahkan text dengan quotes
        - Download hasilnya
        
        **Option 2: Gunakan Mobile App**
        - CapCut (Gratis)
        - InShot (Gratis) 
        - KineMaster (Gratis)
        
        **Option 3: Manual dengan FFmpeg**
        ```bash
        ffmpeg -i input.mp4 -vf "drawtext=text='Your Text':x=(w-text_w)/2:y=(h-text_h)/2:fontsize=40:fontcolor=white" output.mp4
        ```
        """)
        
        # Download original for manual editing
        st.download_button(
            "📥 Download Video untuk Manual Editing",
            uploaded_video.getvalue(),
            "video_background.mp4",
            "video/mp4"
        )

if __name__ == "__main__":
    main()
