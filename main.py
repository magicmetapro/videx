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
            
            # Tampilkan informasi resolusi
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Resolusi Asli", f"{original_width} x {original_height}")
            with col2:
                st.metric("Resolusi Output", "3840 x 2160 (4K)")
            with col3:
                st.metric("Status", "✅ Berhasil")
            
            # Tampilkan frame dalam dua kolom
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Preview Frame")
                # Resize untuk preview (maksimal 800px lebar)
                preview_width = 800
                preview_height = int(2160 * preview_width / 3840)
                preview_frame = cv2.resize(
                    frame_4k, 
                    (preview_width, preview_height), 
                    interpolation=cv2.INTER_AREA
                )
                st.image(preview_frame, use_column_width=True)
            
            with col2:
                st.subheader("Download Frame 4K")
                
                # Konversi ke PIL Image untuk download
                pil_image = Image.fromarray(frame_4k)
                
                # Simpan ke buffer untuk download
                from io import BytesIO
                buffer = BytesIO()
                pil_image.save(buffer, format="PNG", quality=100)
                buffer.seek(0)
                
                # Tombol download
                st.download_button(
                    label="📥 Download Frame 4K (PNG)",
                    data=buffer,
                    file_name=f"last_frame_4k_{uploaded_file.name.split('.')[0]}.png",
                    mime="image/png",
                    help="Download frame terakhir dalam resolusi 4K format PNG"
                )
                
                # Opsi format JPEG dengan kualitas tinggi
                buffer_jpeg = BytesIO()
                pil_image.save(buffer_jpeg, format="JPEG", quality=100)
                buffer_jpeg.seek(0)
                
                st.download_button(
                    label="📥 Download Frame 4K (JPEG)",
                    data=buffer_jpeg,
                    file_name=f"last_frame_4k_{uploaded_file.name.split('.')[0]}.jpg",
                    mime="image/jpeg",
                    help="Download frame terakhir dalam resolusi 4K format JPEG"
                )
                
                # Informasi file output
                st.info(f"""
                **Informasi Output:**
                - Format: PNG & JPEG
                - Resolusi: 3840 × 2160 pixels
                - Warna: RGB
                - Kualitas: Maximum
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
    3. Preview hasil akan ditampilkan
    4. Download frame dalam resolusi 4K
    
    **Fitur:**
    - Support berbagai format video
    - Auto upscale ke 4K
    - Kualitas gambar optimal
    - Download format PNG & JPEG
    """)

# Footer
st.markdown("---")
st.markdown(
    "Dibuat dengan ❤️ menggunakan Streamlit | "
    "Frame terakhir diekstrak dan di-upscale ke resolusi 4K"
)
