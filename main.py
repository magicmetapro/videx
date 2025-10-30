import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont
import io

def add_text_to_video(input_video_path, output_video_path, text, font_size=50, text_color=(255, 255, 255)):
    """
    Menambahkan teks ke video menggunakan OpenCV
    """
    # Buka video
    cap = cv2.VideoCapture(input_video_path)
    
    # Dapatkan properti video
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Split teks menjadi beberapa baris
    words = text.split()
    lines = []
    current_line = []
    
    # Membagi teks menjadi baris-baris (maksimal 5-6 kata per baris)
    max_words_per_line = 5
    for word in words:
        current_line.append(word)
        if len(current_line) >= max_words_per_line:
            lines.append(' '.join(current_line))
            current_line = []
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Tentukan posisi teks (tengah video)
    text_y_start = height // 2 - (len(lines) * font_size) // 2
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Konversi frame BGR ke RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(pil_img)
        
        try:
            # Coba gunakan font Arial, jika tidak ada gunakan font default
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Gambar setiap baris teks
        for i, line in enumerate(lines):
            # Hitung lebar teks untuk penempatan tengah
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            text_y = text_y_start + i * font_size
            
            # Tambahkan shadow untuk readability
            shadow_color = (0, 0, 0)
            draw.text((text_x+2, text_y+2), line, font=font, fill=shadow_color)
            draw.text((text_x, text_y), line, font=font, fill=text_color)
        
        # Konversi kembali ke BGR untuk OpenCV
        frame_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
    
    cap.release()
    out.release()

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
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="Unggah video yang akan dijadikan background"
    )
    
    # Input text
    quote_text = st.text_area(
        "Masukkan quotes Anda:",
        placeholder="Tulis quotes inspiratif di sini...",
        height=100
    )
    
    # Pengaturan tambahan
    col1, col2 = st.columns(2)
    
    with col1:
        font_size = st.slider("Ukuran font:", 20, 100, 50)
        text_color = st.color_picker("Warna teks:", "#FFFFFF")
    
    with col2:
        preview_frame = st.slider("Frame preview:", 0, 100, 10)
    
    # Konversi warna hex ke RGB
    rgb_color = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    if uploaded_video is not None and quote_text:
        # Simpan video uploaded ke temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input:
            temp_input.write(uploaded_video.read())
            temp_input_path = temp_input.name
        
        # Tampilkan preview
        st.subheader("Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Video Original**")
            st.video(uploaded_video)
        
        with col2:
            st.markdown("**Preview dengan Text**")
            
            # Buat preview dari satu frame
            cap = cv2.VideoCapture(temp_input_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            preview_frame_num = min(preview_frame, total_frames-1)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, preview_frame_num)
            ret, frame = cap.read()
            
            if ret:
                # Proses frame untuk preview
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                draw = ImageDraw.Draw(pil_img)
                
                # Split text untuk preview
                words = quote_text.split()
                lines = []
                current_line = []
                max_words_per_line = 5
                
                for word in words:
                    current_line.append(word)
                    if len(current_line) >= max_words_per_line:
                        lines.append(' '.join(current_line))
                        current_line = []
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                height, width = frame.shape[:2]
                text_y_start = height // 2 - (len(lines) * font_size) // 2
                
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                
                # Gambar teks pada preview
                for i, line in enumerate(lines):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_x = (width - text_width) // 2
                    text_y = text_y_start + i * font_size
                    
                    # Shadow
                    draw.text((text_x+2, text_y+2), line, font=font, fill=(0, 0, 0))
                    draw.text((text_x, text_y), line, font=font, fill=rgb_color)
                
                # Konversi kembali untuk display
                preview_frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Simpan preview sebagai image temporary
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_preview:
                    cv2.imwrite(temp_preview.name, preview_frame)
                    st.image(temp_preview.name, use_column_width=True)
                
                cap.release()
        
        # Tombol untuk memproses video
        if st.button("🚀 Generate Video dengan Quotes", type="primary"):
            with st.spinner("Sedang memproses video..."):
                # Buat output video
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output:
                    output_path = temp_output.name
                
                try:
                    add_text_to_video(temp_input_path, output_path, quote_text, font_size, rgb_color)
                    
                    # Baca output video
                    with open(output_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    # Tampilkan hasil
                    st.success("✅ Video berhasil dibuat!")
                    st.subheader("Hasil Video")
                    st.video(video_bytes)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Video",
                        data=video_bytes,
                        file_name="video_with_quotes.mp4",
                        mime="video/mp4"
                    )
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    # Cleanup
                    if os.path.exists(temp_input_path):
                        os.unlink(temp_input_path)
                    if os.path.exists(output_path):
                        os.unlink(output_path)
    
    elif uploaded_video is None:
        st.info("📁 Silakan unggah video background terlebih dahulu")
    
    elif not quote_text:
        st.info("✍️ Silakan masukkan quotes terlebih dahulu")

if __name__ == "__main__":
    main()
