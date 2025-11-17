import streamlit as st
import numpy as np
import tempfile
import os
from PIL import Image
import imageio.v3 as iio
from io import BytesIO

# Konfigurasi halaman
st.set_page_config(
    page_title="Video Frame Extractor",
    page_icon="🎬",
    layout="wide"
)

# Judul aplikasi
st.title("🎬 Video Frame Extractor - 4K Resolution")
st.markdown("Upload video dan ambil frame terakhir dengan kualitas 4K")

def extract_last_frame_with_imageio(video_path, target_resolution=(3840, 2160)):
    """
    Mengambil frame terakhir dari video menggunakan imageio
    """
    try:
        # Baca semua frame (hanya metadata untuk efisiensi)
        frames = iio.imiter(video_path)
        
        # Cari frame terakhir
        last_frame = None
        for frame in frames:
            last_frame = frame
        
        if last_frame is None:
            st.error("Tidak dapat membaca frame dari video")
            return None
        
        # Konversi ke PIL Image
        pil_image = Image.fromarray(last_frame)
        original_width, original_height = pil_image.size
        
        # Tentukan orientasi
        is_portrait = original_height > original_width
        
        if is_portrait:
            # Untuk portrait: gunakan 2160x3840 (portrait 4K)
            target_width = 2160
            target_height = 3840
        else:
            # Untuk landscape: gunakan 3840x2160 (landscape 4K)
            target_width = 3840
            target_height = 2160
        
        # Upscale ke 4K sesuai orientasi
        if original_width < target_width or original_height < target_height:
            # Hitung scaling factor
            scale_x = target_width / original_width
            scale_y = target_height / original_height
            scale_factor = min(scale_x, scale_y)
            
            # Hitung dimensi baru
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize dengan kualitas terbaik
            resized_image = pil_image.resize(
                (new_width, new_height), 
                Image.Resampling.LANCZOS
            )
            
            # Buat canvas 4K dengan background hitam
            canvas = Image.new("RGB", (target_width, target_height), (0, 0, 0))
            
            # Hitung posisi untuk center
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            # Tempel gambar ke canvas
            canvas.paste(resized_image, (x_offset, y_offset))
            final_image = canvas
            
        else:
            # Jika resolusi sudah cukup besar, resize ke 4K sesuai orientasi
            final_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        return np.array(final_image), original_width, original_height, is_portrait
        
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
        return None

def extract_last_frame_simple(video_path):
    """
    Metode sederhana untuk mengambil frame terakhir - pertahankan orientasi asli
    """
    try:
        # Baca video dengan imageio
        video_reader = iio.imiter(video_path)
        
        # Iterasi sampai frame terakhir
        last_frame = None
        frame_count = 0
        
        for frame in video_reader:
            last_frame = frame
            frame_count += 1
        
        if last_frame is None:
            st.error("Tidak dapat membaca video")
            return None
            
        # Tentukan orientasi
        original_height, original_width = last_frame.shape[:2]
        is_portrait = original_height > original_width
        
        st.success(f"Berhasil membaca {frame_count} frame")
        return last_frame, original_width, original_height, is_portrait
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

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
        # Pilih metode ekstraksi
        method = st.radio(
            "Pilih metode ekstraksi:",
            ["Simple", "4K Upscale"],
            help="Simple: Ambil frame asli | 4K Upscale: Upscale ke resolusi 4K sesuai orientasi"
        )
        
        if st.button("🎯 Ekstrak Frame Terakhir"):
            with st.spinner('Sedang memproses video...'):
                if method == "Simple":
                    result = extract_last_frame_simple(temp_path)
                else:
                    result = extract_last_frame_with_imageio(temp_path)
            
            if result:
                if method == "Simple":
                    frame, original_width, original_height, is_portrait = result
                    pil_image = Image.fromarray(frame)
                    output_width, output_height = pil_image.size
                else:
                    frame_4k, original_width, original_height, is_portrait = result
                    pil_image = Image.fromarray(frame_4k)
                    output_width, output_height = pil_image.size
                
                # Tampilkan informasi
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Resolusi Asli", f"{original_width} x {original_height}")
                with col2:
                    if method == "4K Upscale":
                        if is_portrait:
                            st.metric("Resolusi Output", "2160 x 3840 (4K Portrait)")
                        else:
                            st.metric("Resolusi Output", "3840 x 2160 (4K Landscape)")
                    else:
                        st.metric("Resolusi Output", f"{output_width} x {output_height}")
                with col3:
                    st.metric("Orientasi", "Portrait 📱" if is_portrait else "Landscape 🖥️")
                with col4:
                    st.metric("Status", "✅ Berhasil")
                
                # Tampilkan preview
                st.subheader("📷 Preview Frame")
                
                # Resize untuk preview (maksimal 600px di sisi terpanjang)
                max_preview_size = 600
                if output_width > output_height:
                    # Landscape
                    preview_width = min(max_preview_size, output_width)
                    preview_height = int(output_height * preview_width / output_width)
                else:
                    # Portrait
                    preview_height = min(max_preview_size, output_height)
                    preview_width = int(output_width * preview_height / output_height)
                
                preview_image = pil_image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
                
                st.image(preview_image, caption=f"Frame Terakhir - {preview_image.width} x {preview_image.height} ({'Portrait' if is_portrait else 'Landscape'})", use_column_width=False)
                
                # Download section
                st.subheader("📥 Download Frame")
                
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    # PNG
                    png_buffer = BytesIO()
                    pil_image.save(png_buffer, format="PNG", optimize=True)
                    png_buffer.seek(0)
                    
                    st.download_button(
                        label="💾 Download PNG (Original Quality)",
                        data=png_buffer,
                        file_name=f"last_frame_{uploaded_file.name.split('.')[0]}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                
                with col_dl2:
                    # JPEG
                    jpeg_buffer = BytesIO()
                    pil_image.save(jpeg_buffer, format="JPEG", quality=95, optimize=True)
                    jpeg_buffer.seek(0)
                    
                    st.download_button(
                        label="💾 Download JPEG (High Quality)",
                        data=jpeg_buffer,
                        file_name=f"last_frame_{uploaded_file.name.split('.')[0]}.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
                
                # Informasi tambahan
                st.info(f"""
                **📊 Informasi Output:**
                - Orientasi: **{'Portrait' if is_portrait else 'Landscape'}**
                - Resolusi Output: **{output_width} × {output_height}** pixels
                - Format: PNG (Lossless) & JPEG (High Quality)
                - Warna: RGB
                """)
    
    except Exception as e:
        st.error(f"Terjadi error: {str(e)}")
        st.info("Coba install dependency yang diperlukan: `pip install imageio[pyav]`")
    
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

else:
    # Instructions
    st.info("""
    **📋 Instruksi Penggunaan:**
    1. Upload file video menggunakan tombol di atas
    2. Pilih metode ekstraksi (Simple atau 4K Upscale)
    3. Klik tombol 'Ekstrak Frame Terakhir'
    4. Preview hasil dan download frame
    
    **🎯 Fitur:**
    - ✅ Pertahankan orientasi asli (portrait/landscape)
    - ✅ Auto detect orientasi video
    - ✅ 4K upscale sesuai orientasi
    - ✅ Preview dengan ukuran optimal
    - ✅ Download format PNG & JPEG
    
    **🛠️ Jika terjadi error:** 
    - Jalankan: `pip install imageio[pyav]`
    """)

# Footer
st.markdown("---")
st.markdown("Dibuat dengan Streamlit | Auto-orientation detection")
