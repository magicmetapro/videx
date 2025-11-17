import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from PIL import Image

# Konfigurasi halaman
st.set_page_config(
    page_title="Video Frame Extractor",
    page_icon="🎬",
    layout="wide"
)

# Judul aplikasi
st.title("🎬 Video Frame Extractor - 4K Resolution")
st.markdown("Upload video dan ambil frame terakhir dengan kualitas 4K")

# Fungsi untuk mengambil frame terakhir
def extract_last_frame(video_path, target_resolution=(3840, 2160)):
    """
    Mengambil frame terakhir dari video dan upscale ke 4K jika diperlukan
    """
    # Buka video
    cap = cv2.VideoCapture(video_path)
    
    # Dapatkan total frame count
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        st.error("Tidak dapat membaca video atau video kosong")
        return None
    
    # Set posisi ke frame terakhir
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    
    # Baca frame terakhir
    ret, frame = cap.read()
    
    # Tutup video capture
    cap.release()
    
    if not ret:
        st.error("Gagal membaca frame terakhir")
        return None
    
    # Konversi BGR ke RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Dapatkan resolusi asli
    original_height, original_width = frame_rgb.shape[:2]
    
    # Upscale ke 4K jika resolusi lebih kecil
    if original_width < 3840 or original_height < 2160:
        # Hitung scaling factor
        scale_x = 3840 / original_width
        scale_y = 2160 / original_height
        scale_factor = min(scale_x, scale_y)
        
        # Hitung dimensi baru
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize dengan interpolasi Lanczos untuk kualitas terbaik
        frame_4k = cv2.resize(
            frame_rgb, 
            (new_width, new_height), 
            interpolation=cv2.INTER_LANCZOS4
        )
        
        # Tambahkan padding jika perlu untuk mencapai tepat 4K
        if new_width < 3840 or new_height < 2160:
            pad_top = (2160 - new_height) // 2
            pad_bottom = 2160 - new_height - pad_top
            pad_left = (3840 - new_width) // 2
            pad_right = 3840 - new_width - pad_left
            
            frame_4k = cv2.copyMakeBorder(
                frame_4k, 
                pad_top, pad_bottom, pad_left, pad_right,
                cv2.BORDER_CONSTANT, 
                value=[0, 0, 0]  # Padding hitam
            )
    else:
        # Jika resolusi sudah 4K atau lebih besar, resize ke 4K
        frame_4k = cv2.resize(
            frame_rgb, 
            (3840, 2160), 
            interpolation=cv2.INTER_LANCZOS4
        )
    
    return frame_4k, original_width, original_height

# Fungsi untuk membuat versi portrait
def create_portrait_version(frame_4k, portrait_resolution=(2160, 3840)):
    """
    Membuat versi portrait dari frame 4K landscape
    """
    # Dapatkan dimensi frame asli
    height, width = frame_4k.shape[:2]
    
    # Hitung area crop untuk portrait (ambil bagian tengah)
    crop_width = int(height * 9 / 16)  # Rasio 9:16 untuk portrait
    start_x = (width - crop_width) // 2
    
    # Crop bagian tengah untuk portrait
    portrait_frame = frame_4k[:, start_x:start_x + crop_width]
    
    # Resize ke resolusi portrait 9:16
    portrait_resized = cv2.resize(
        portrait_frame, 
        portrait_resolution, 
        interpolation=cv2.INTER_LANCZOS4
    )
    
    return portrait_resized

# Fungsi untuk membuat versi portrait dengan alternatif (jika crop tidak sesuai)
def create_portrait_alternative(frame_4k, portrait_resolution=(2160, 3840)):
    """
    Alternatif: resize dengan padding untuk mempertahankan seluruh gambar
    """
    height, width = frame_4k.shape[:2]
    
    # Hitung scaling factor untuk portrait
    scale_x = portrait_resolution[0] / width
    scale_y = portrait_resolution[1] / height
    scale_factor = min(scale_x, scale_y)
    
    # Hitung dimensi baru
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Resize gambar
    resized_frame = cv2.resize(
        frame_4k, 
        (new_width, new_height), 
        interpolation=cv2.INTER_LANCZOS4
    )
    
    # Tambahkan padding untuk mencapai resolusi portrait
    pad_top = (portrait_resolution[1] - new_height) // 2
    pad_bottom = portrait_resolution[1] - new_height - pad_top
    pad_left = (portrait_resolution[0] - new_width) // 2
    pad_right = portrait_resolution[0] - new_width - pad_left
    
    portrait_frame = cv2.copyMakeBorder(
        resized_frame, 
        pad_top, pad_bottom, pad_left, pad_right,
        cv2.BORDER_CONSTANT, 
        value=[0, 0, 0]  # Padding hitam
    )
    
    return portrait_frame

# Upload video
uploaded_file = st.file_uploader(
    "Pilih file video", 
    type=['mp4', 'avi', 'mov', 'mkv', 'wmv'],
    help="Format yang didukung: MP4, AVI, MOV, MKV, WMV"
)

if uploaded_file is not None:
    # Tampilkan informasi file
    file_details = {
        "Nama File": uploaded_file.name,
        "Tipe File": uploaded_file.type,
        "Ukuran File": f"{uploaded_file.size / (1024*1024):.2f} MB"
    }
    
    st.write("**Informasi File:**")
    st.json(file_details)
    
    # Simpan file sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name
    
    try:
        # Ekstrak frame terakhir
        with st.spinner('Mengekstrak frame terakhir...'):
            result = extract_last_frame(temp_path)
        
        if result:
            frame_4k, original_width, original_height = result
            
            # Buat versi portrait
            with st.spinner('Membuat versi portrait...'):
                portrait_frame = create_portrait_version(frame_4k)
                portrait_alternative = create_portrait_alternative(frame_4k)
            
            # Tampilkan informasi resolusi
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Resolusi Asli", f"{original_width} x {original_height}")
            with col2:
                st.metric("Resolusi Output Landscape", "3840 x 2160 (4K)")
            with col3:
                st.metric("Resolusi Output Portrait", "2160 x 3840 (9:16)")
            
            # Tampilkan frame dalam tiga kolom
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Preview Landscape")
                # Resize untuk preview
                preview_width = 400
                preview_height = int(2160 * preview_width / 3840)
                preview_frame = cv2.resize(
                    frame_4k, 
                    (preview_width, preview_height), 
                    interpolation=cv2.INTER_AREA
                )
                st.image(preview_frame, use_column_width=True)
            
            with col2:
                st.subheader("Preview Portrait (Crop)")
                # Resize untuk preview portrait
                preview_portrait_width = 300
                preview_portrait_height = int(3840 * preview_portrait_width / 2160)
                preview_portrait = cv2.resize(
                    portrait_frame, 
                    (preview_portrait_height, preview_portrait_width), 
                    interpolation=cv2.INTER_AREA
                )
                st.image(preview_portrait, use_column_width=True)
                
            with col3:
                st.subheader("Preview Portrait (Full)")
                # Resize untuk preview portrait alternative
                preview_portrait_alt = cv2.resize(
                    portrait_alternative, 
                    (preview_portrait_height, preview_portrait_width), 
                    interpolation=cv2.INTER_AREA
                )
                st.image(preview_portrait_alt, use_column_width=True)
            
            # Section Download
            st.markdown("---")
            st.subheader("📥 Download Frame")
            
            # Buat tab untuk landscape dan portrait
            tab1, tab2, tab3 = st.tabs(["🎯 Landscape 4K", "📱 Portrait (Crop)", "📱 Portrait (Full)"])
            
            with tab1:
                st.write("**Download Frame Landscape 4K**")
                
                # Konversi ke PIL Image untuk download
                pil_image_landscape = Image.fromarray(frame_4k)
                
                # Simpan ke buffer untuk download
                from io import BytesIO
                
                # PNG Landscape
                buffer_landscape_png = BytesIO()
                pil_image_landscape.save(buffer_landscape_png, format="PNG", quality=100)
                buffer_landscape_png.seek(0)
                
                st.download_button(
                    label="📥 Download Landscape 4K (PNG)",
                    data=buffer_landscape_png,
                    file_name=f"last_frame_4k_landscape_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png",
                    help="Download frame terakhir dalam resolusi 4K landscape format PNG"
                )
                
                # JPEG Landscape
                buffer_landscape_jpeg = BytesIO()
                pil_image_landscape.save(buffer_landscape_jpeg, format="JPEG", quality=100)
                buffer_landscape_jpeg.seek(0)
                
                st.download_button(
                    label="📥 Download Landscape 4K (JPEG)",
                    data=buffer_landscape_jpeg,
                    file_name=f"last_frame_4k_landscape_{uploaded_file.name.split('.')[0]}.jpg",
                    mime="image/jpeg",
                    help="Download frame terakhir dalam resolusi 4K landscape format JPEG"
                )
            
            with tab2:
                st.write("**Download Frame Portrait (Crop Tengah)**")
                st.info("Crop bagian tengah gambar untuk rasio 9:16")
                
                # Konversi portrait frame ke PIL
                pil_image_portrait = Image.fromarray(portrait_frame)
                
                # PNG Portrait Crop
                buffer_portrait_png = BytesIO()
                pil_image_portrait.save(buffer_portrait_png, format="PNG", quality=100)
                buffer_portrait_png.seek(0)
                
                st.download_button(
                    label="📥 Download Portrait Crop (PNG)",
                    data=buffer_portrait_png,
                    file_name=f"last_frame_portrait_crop_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png",
                    help="Download frame portrait dengan crop tengah format PNG"
                )
                
                # JPEG Portrait Crop
                buffer_portrait_jpeg = BytesIO()
                pil_image_portrait.save(buffer_portrait_jpeg, format="JPEG", quality=100)
                buffer_portrait_jpeg.seek(0)
                
                st.download_button(
                    label="📥 Download Portrait Crop (JPEG)",
                    data=buffer_portrait_jpeg,
                    file_name=f"last_frame_portrait_crop_{uploaded_file.name.split('.')[0]}.jpg",
                    mime="image/jpeg",
                    help="Download frame portrait dengan crop tengah format JPEG"
                )
            
            with tab3:
                st.write("**Download Frame Portrait (Full dengan Padding)**")
                st.info("Seluruh gambar ditampilkan dengan padding hitam")
                
                # Konversi portrait alternative ke PIL
                pil_image_portrait_alt = Image.fromarray(portrait_alternative)
                
                # PNG Portrait Full
                buffer_portrait_alt_png = BytesIO()
                pil_image_portrait_alt.save(buffer_portrait_alt_png, format="PNG", quality=100)
                buffer_portrait_alt_png.seek(0)
                
                st.download_button(
                    label="📥 Download Portrait Full (PNG)",
                    data=buffer_portrait_alt_png,
                    file_name=f"last_frame_portrait_full_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png",
                    help="Download frame portrait dengan padding format PNG"
                )
                
                # JPEG Portrait Full
                buffer_portrait_alt_jpeg = BytesIO()
                pil_image_portrait_alt.save(buffer_portrait_alt_jpeg, format="JPEG", quality=100)
                buffer_portrait_alt_jpeg.seek(0)
                
                st.download_button(
                    label="📥 Download Portrait Full (JPEG)",
                    data=buffer_portrait_alt_jpeg,
                    file_name=f"last_frame_portrait_full_{uploaded_file.name.split('.')[0]}.jpg",
                    mime="image/jpeg",
                    help="Download frame portrait dengan padding format JPEG"
                )
            
            # Informasi file output
            st.info(f"""
            **Informasi Output:**
            - **Landscape:** 3840 × 2160 pixels (16:9)
            - **Portrait Crop:** 2160 × 3840 pixels (9:16) - Crop tengah
            - **Portrait Full:** 2160 × 3840 pixels (9:16) - Dengan padding
            - **Format:** PNG & JPEG
            - **Kualitas:** Maximum
            """)
    
    except Exception as e:
        st.error(f"Terjadi error: {str(e)}")
    
    finally:
        # Hapus file temporary
        if os.path.exists(temp_path):
            os.unlink(temp_path)

else:
    # Tampilkan instruksi jika belum ada file
    st.info("""
    **Instruksi Penggunaan:**
    1. Upload file video menggunakan tombol di atas
    2. Tunggu proses ekstraksi frame terakhir
    3. Preview hasil akan ditampilkan (landscape dan portrait)
    4. Download frame dalam berbagai format dan orientasi
    
    **Fitur:**
    - Support berbagai format video
    - Auto upscale ke 4K
    - Versi landscape dan portrait
    - Dua metode portrait: crop tengah dan full dengan padding
    - Kualitas gambar optimal
    - Download format PNG & JPEG
    """)

# Footer
st.markdown("---")
st.markdown(
    "Dibuat dengan ❤️ menggunakan Streamlit | "
    "Frame terakhir diekstrak dan di-upscale ke resolusi 4K Landscape & Portrait"
)
