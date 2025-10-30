import streamlit as st
import tempfile
import os

def main():
    st.set_page_config(page_title="Simple Video Quote", layout="wide")
    
    st.title("🎬 Simple Video Quote Generator")
    st.info("Upload video dan text, lalu download panduan editing!")
    
    # Upload
    video = st.file_uploader("Upload Video", type=['mp4', 'mov'])
    text = st.text_area("Masukkan Quotes")
    
    if video and text:
        st.video(video)
        st.success(f"Text: **{text}**")
        
        # Download original video
        st.download_button(
            "📥 Download Video untuk Editing",
            video.getvalue(),
            "video_background.mp4"
        )
        
        st.markdown(f"""
        **🎨 Panduan Manual Editing:**
        1. Buka **CapCut** atau **InShot**
        2. Import video di atas
        3. Tambahkan **Text Layer** dengan quotes:
           ```
           {text}
           ```
        4. Atur style text:
           - **Warna**: Hitam
           - **Background**: Putih transparan
           - **Font**: Bold, size 40-50
        5. Export dan share!
        """)

if __name__ == "__main__":
    main()
