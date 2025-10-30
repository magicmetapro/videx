import streamlit as st
import tempfile
import os
import subprocess
import base64
from PIL import Image, ImageDraw, ImageFont
import io

def add_text_with_white_background(input_video_path, output_video_path, text, font_size=40, bg_opacity=0.8):
    """
    Menambahkan text dengan background putih transparan ke video menggunakan FFmpeg
    """
    try:
        # Escape text untuk FFmpeg
        escaped_text = text.replace("'", "'\\\\\\''").replace('"', '\\"')
        
        # Split text menjadi multiple lines
        words = escaped_text.split()
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
        
        # Buat FFmpeg filter complex untuk background putih transparan + text hitam
        filters = []
        
        for i, line in enumerate(lines):
            # Hitung posisi untuk setiap line
            line_height = font_size + 10
            total_text_height = len(lines) * line_height
            start_y = f"(h-{total_text_height})/2"
            
            # Background putih transparan untuk setiap line
            bg_y = f"{start_y}+{i * line_height}"
            bg_height = font_size + 5
            
            # Filter untuk background transparan
            bg_filter = f"color=white@0.8:size=iwx{font_size + 10}[bg{i}];" \
                       f"[bg{i}]format=rgba[bg_transparent{i}];" \
                       f"[0:v][bg_transparent{i}]overlay=x=(W-w)/2:y={bg_y}"
            
            filters.append(bg_filter)
            
            # Filter untuk text hitam
            text_y = f"{start_y}+{i * line_height + 5}"  # +5 untuk padding
            text_filter = f"drawtext=text='{line}':fontcolor=black:fontsize={font_size}:" \
                         f"x=(w-text_w)/2:y={text_y}:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            
            filters.append(text_filter)
        
        # Gabungkan semua filter
        filter_chain = ",".join(filters)
        
        # FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', input_video_path,
            '-filter_complex', filter_chain,
            '-c:a', 'copy',
            '-y',  # Overwrite output file
            output_video_path
        ]
        
        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback ke method yang lebih sederhana
            st.warning("Menggunakan method alternatif...")
            return add_text_simple_method(input_video_path, output_video_path, text, font_size, bg_opacity)
        
        return True
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return add_text_simple_method(input_video_path, output_video_path, text, font_size, bg_opacity)

def add_text_simple_method(input_video_path, output_video_path, text, font_size=40, bg_opacity=0.8):
    """
    Method alternatif yang lebih sederhana untuk menambahkan text dengan background
    """
    try:
        # Escape text
        escaped_text = text.replace("'", "'\\\\\\''").replace('"', '\\"')
        
        # Split text
        words = escaped_text.split()
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
        
        # Buat filter yang lebih sederhana
        drawtext_filters = []
        
        for i, line in enumerate(lines):
            # Background menggunakan box
            y_position = f"(h-text_h)/2-{len(lines)*font_size//2}+{i*font_size}"
            drawtext = f"drawtext=text='{line}':x=(w-text_w)/2:y={y_position}:" \
                      f"fontsize={font_size}:fontcolor=black:" \
                      f"box=1:boxcolor=white@0.8:boxborderw=10"
            
            drawtext_filters.append(drawtext)
        
        filter_chain = ",".join(drawtext_filters)
        
        cmd = [
            'ffmpeg',
            '-i', input_video_path,
            '-vf', filter_chain,
            '-c:a', 'copy',
            '-y',
            output_video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except Exception as e:
        st.error(f"Error dalam method alternatif: {str(e)}")
        return False

def create_text_preview(text, font_size=40, bg_opacity=0.8):
    """
    Membuat preview gambar dengan text hitam dan background putih transparan
    """
    # Create a transparent background
    img = Image.new('RGBA', (800, 400), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
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
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.load_default()
        except:
            font = None
    
    # Calculate total text height
    line_height = font_size + 15
    total_height = len(lines) * line_height
    
    # Draw background for each line
    for i, line in enumerate(lines):
        if font:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(line) * font_size
            text_height = font_size
        
        # Position
        x = (800 - text_width) // 2 - 10  # Padding
        y = (400 - total_height) // 2 + i * line_height
        
        # Draw white background with opacity
        bg_color = (255, 255, 255, int(255 * bg_opacity))
        draw.rectangle([x, y, x + text_width + 20, y + text_height + 10], fill=bg_color)
        
        # Draw black text
        text_x = (800 - text_width) // 2
        text_y = y + 5
        draw.text((text_x, text_y), line, fill=(0, 0, 0, 255), font=font)
    
    return img

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except:
        return False

def main():
    st.set_page_config(
        page_title="Video Quote - White BG Black Text",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Video Quote Generator")
    st.markdown("**Text hitam dengan background putih transparan** di atas video")
    
    # Check FFmpeg
    if not check_ffmpeg():
        st.warning("Menginstall FFmpeg...")
        try:
            subprocess.run(['apt-get', 'update'], capture_output=True)
            subprocess.run(['apt-get', 'install', '-y', 'ffmpeg'], capture_output=True)
        except:
            pass
    
    # Upload video
    st.header("1. Upload Video Background")
    uploaded_video = st.file_uploader(
        "Pilih video file", 
        type=['mp4', 'mov', 'avi'],
        help="Format: MP4, MOV, AVI"
    )
    
    if uploaded_video:
        st.success("✅ Video berhasil diupload!")
        col1, col2 = st.columns(2)
        with col1:
            st.video(uploaded_video)
    
    # Text input
    st.header("2. Masukkan Quotes")
    quote_text = st.text_area(
        "Tulis quotes Anda:",
        placeholder="Contoh: Success is not final, failure is not fatal...",
        height=100,
        max_chars=200
    )
    
    # Quick quotes
    st.subheader("Quotes Cepat:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💪 Motivasi", use_container_width=True):
            quote_text = "Never stop believing in yourself"
    with col2:
        if st.button("🚀 Sukses", use_container_width=True):
            quote_text = "Success is a journey not a destination"
    with col3:
        if st.button("🌟 Inspirasi", use_container_width=True):
            quote_text = "Dream big and make it happen"
    
    # Customization
    st.header("3. Customize Tampilan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        font_size = st.slider("Ukuran Font:", 20, 80, 40)
        bg_opacity = st.slider("Transparansi Background:", 0.1, 1.0, 0.8)
    
    with col2:
        st.color_picker("Warna Text:", "#000000", disabled=True)
        st.color_picker("Warna Background:", "#FFFFFF", disabled=True)
        st.info("🎨 Text: Hitam | Background: Putih transparan")
    
    # Preview
    if quote_text:
        st.header("4. Preview Text")
        preview_img = create_text_preview(quote_text, font_size, bg_opacity)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(preview_img, caption="Preview Text dengan Background Putih Transparan", use_column_width=True)
        
        with col2:
            st.markdown("""
            **Desain:**
            - ✅ Text: **Hitam**
            - ✅ Background: **Putih transparan**
            - ✅ Font size: **{}px**
            - ✅ Opacity: **{}%**
            """.format(font_size, int(bg_opacity * 100)))
    
    # Generate video
    if uploaded_video and quote_text:
        st.header("5. Generate Video")
        
        if st.button("🎬 GENERATE VIDEO", type="primary", use_container_width=True):
            with st.spinner("Sedang memproses video... Mohon tunggu 10-30 detik"):
                
                # Save uploaded video
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input:
                    temp_input.write(uploaded_video.getvalue())
                    input_path = temp_input.name
                
                # Create output
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output:
                    output_path = temp_output.name
                
                try:
                    # Process video
                    success = add_text_with_white_background(
                        input_path, 
                        output_path, 
                        quote_text, 
                        font_size, 
                        bg_opacity
                    )
                    
                    if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        st.success("✅ Video berhasil dibuat!")
                        
                        # Display result
                        st.subheader("Hasil Video:")
                        
                        with open(output_path, 'rb') as f:
                            video_bytes = f.read()
                        
                        st.video(video_bytes)
                        
                        # Download
                        st.download_button(
                            label="📥 DOWNLOAD VIDEO HASIL",
                            data=video_bytes,
                            file_name="video_quotes_white_bg.mp4",
                            mime="video/mp4",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Gagal memproses video. Coba dengan pengaturan berbeda.")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                
                finally:
                    # Cleanup
                    try:
                        if os.path.exists(input_path):
                            os.unlink(input_path)
                        if os.path.exists(output_path):
                            os.unlink(output_path)
                    except:
                        pass
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Video Quote Generator** • Text Hitam dengan Background Putih Transparan • "
        "Dibuat dengan ❤️ menggunakan FFmpeg + Streamlit"
    )

if __name__ == "__main__":
    main()
