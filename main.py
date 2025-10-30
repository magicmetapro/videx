import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import base64

def add_text_to_video_moviepy(input_video_path, output_video_path, text, font_size=50, text_color='white'):
    """
    Menambahkan teks ke video menggunakan MoviePy
    """
    try:
        # Load video
        video = VideoFileClip(input_video_path)
        
        # Split text into lines
        words = text.split()
        lines = []
        current_line = []
        max_words_per_line = 4
        
        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words_per_line:
                lines.append(' '.join(current_line))
                current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Create text clips for each line
        text_clips = []
        duration = video.duration
        
        for i, line in enumerate(lines):
            txt_clip = TextClip(
                line, 
                fontsize=font_size, 
                color=text_color,
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            )
            
            # Position text in the center
            txt_clip = txt_clip.set_position(('center', f'center-{len(lines)*font_size//2 - i*font_size}'))
            txt_clip = txt_clip.set_duration(duration)
            text_clips.append(txt_clip)
        
        # Combine video and text
        final_video = CompositeVideoClip([video] + text_clips)
        
        # Write output video
        final_video.write_videofile(
            output_video_path, 
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Close clips to free memory
        video.close()
        final_video.close()
        for clip in text_clips:
            clip.close()
            
        return True
        
    except Exception as e:
        st.error(f"Error in video processing: {str(e)}")
        return False

def get_video_duration(video_path):
    """Get video duration using moviepy"""
    try:
        video = VideoFileClip(video_path)
        duration = video.duration
        video.close()
        return duration
    except:
        return 0

def main():
    st.set_page_config(
        page_title="Video Quote Generator",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Video Quote Generator")
    st.markdown("Unggah video background dan tambahkan quotes menarik!")
    
    # Sidebar untuk pengaturan
    st.sidebar.header("Pengaturan")
    
    # Upload video
    uploaded_video = st.file_uploader(
        "Pilih video background", 
        type=['mp4', 'mov', 'avi'],
        help="Unggah video yang akan dijadikan background (format MP4, MOV, AVI)"
    )
    
    # Input text
    quote_text = st.text_area(
        "Masukkan quotes Anda:",
        placeholder="Tulis quotes inspiratif di sini...",
        height=100,
        max_chars=200
    )
    
    # Pengaturan tambahan
    col1, col2 = st.columns(2)
    
    with col1:
        font_size = st.slider("Ukuran font:", 20, 100, 50)
        text_color = st.color_picker("Warna teks:", "#FFFFFF")
    
    with col2:
        st.info("💡 Tips: Gunakan quotes pendek untuk hasil terbaik")
    
    # Contoh quotes
    with st.expander("📝 Contoh Quotes"):
        example_quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens when you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt"
        ]
        for quote in example_quotes:
            if st.button(quote, key=quote):
                quote_text = quote
    
    if uploaded_video is not None and quote_text:
        # Display original video
        st.subheader("Video Original")
        st.video(uploaded_video)
        
        # Show video info
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input:
            temp_input.write(uploaded_video.read())
            temp_input_path = temp_input.name
        
        duration = get_video_duration(temp_input_path)
        if duration > 0:
            st.info(f"Durasi video: {duration:.2f} detik")
        
        # Processing button
        if st.button("🚀 Generate Video dengan Quotes", type="primary"):
            if len(quote_text.strip()) < 5:
                st.warning("Quotes terlalu pendek. Minimal 5 karakter.")
                return
            
            with st.spinner("Sedang memproses video... Ini mungkin membutuhkan beberapa saat"):
                # Create output video
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output:
                    output_path = temp_output.name
                
                try:
                    success = add_text_to_video_moviepy(
                        temp_input_path, 
                        output_path, 
                        quote_text, 
                        font_size, 
                        text_color
                    )
                    
                    if success and os.path.exists(output_path):
                        # Display result
                        st.success("✅ Video berhasil dibuat!")
                        st.subheader("Hasil Video dengan Quotes")
                        
                        # Read and display video
                        with open(output_path, 'rb') as f:
                            video_bytes = f.read()
                        
                        st.video(video_bytes)
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Video",
                            data=video_bytes,
                            file_name="video_quotes.mp4",
                            mime="video/mp4",
                            type="primary"
                        )
                    else:
                        st.error("Gagal membuat video. Silakan coba dengan video atau teks yang berbeda.")
                        
                except Exception as e:
                    st.error(f"Terjadi error: {str(e)}")
                    st.info("💡 Tips: Coba dengan video yang lebih pendek atau teks yang lebih sederhana")
                
                finally:
                    # Cleanup
                    try:
                        if os.path.exists(temp_input_path):
                            os.unlink(temp_input_path)
                        if os.path.exists(output_path):
                            os.unlink(output_path)
                    except:
                        pass
    
    elif uploaded_video is None:
        st.info("📁 Silakan unggah video background terlebih dahulu")
    
    elif not quote_text:
        st.info("✍️ Silakan masukkan quotes terlebih dahulu")

    # Footer
    st.markdown("---")
    st.markdown(
        "Dibuat dengan ❤️ menggunakan Streamlit dan MoviePy | "
        "Video Quote Generator v1.0"
    )

if __name__ == "__main__":
    main()
