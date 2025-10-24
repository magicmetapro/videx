import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import io
import tempfile
import os
from pydub import AudioSegment
from pydub.effects import crossfade_inout  # Perbaikan import
import matplotlib.pyplot as plt

def create_smooth_loop(audio_data, sample_rate, target_duration_minutes, crossfade_duration=500):
    """
    Membuat loop audio yang smooth dengan crossfade
    """
    # Konversi ke AudioSegment
    audio_segment = AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio_data.dtype.itemsize,
        channels=1 if len(audio_data.shape) == 1 else audio_data.shape[1]
    )
    
    # Durasi target dalam milidetik
    target_duration_ms = target_duration_minutes * 60 * 1000
    original_duration_ms = len(audio_segment)
    
    # Hitung berapa loop yang dibutuhkan
    num_loops = int(target_duration_ms / original_duration_ms) + 1
    
    st.info(f"Original duration: {original_duration_ms/1000:.2f} seconds")
    st.info(f"Target duration: {target_duration_minutes} minutes ({target_duration_ms/1000:.2f} seconds)")
    st.info(f"Number of loops needed: {num_loops}")
    
    # Buat loop pertama
    looped_audio = audio_segment
    
    # Tambahkan loop dengan crossfade
    for i in range(1, num_loops):
        # Gunakan crossfade untuk transisi yang smooth
        looped_audio = looped_audio.append(audio_segment, crossfade=crossfade_duration)
        
        # Progress bar update
        progress = min((i + 1) / num_loops, 1.0)
        
    # Potong ke durasi yang tepat
    final_audio = looped_audio[:target_duration_ms]
    
    return final_audio

def analyze_audio_features(audio_data, sample_rate):
    """
    Analisis fitur audio untuk optimasi looping
    """
    features = {}
    
    # Hitung RMS energy untuk detect transisi yang baik
    features['rms'] = librosa.feature.rms(y=audio_data)[0]
    features['spectral_centroid'] = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
    
    # Temukan beat locations untuk transisi yang natural
    tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
    features['tempo'] = tempo
    features['beat_frames'] = beat_frames
    
    return features

def find_best_crossfade_duration(audio_features, original_duration):
    """
    Tentukan durasi crossfade optimal berdasarkan analisis audio
    """
    tempo = audio_features.get('tempo', 120)
    rms_variation = np.std(audio_features.get('rms', [1]))
    
    # Logic untuk menentukan crossfade duration
    if tempo < 80:  # Audio lambat
        crossfade = 800  # Crossfade lebih panjang
    elif tempo > 140:  # Audio cepat
        crossfade = 300  # Crossfade lebih pendek
    else:
        crossfade = 500  # Default
    
    # Adjust berdasarkan variasi energy
    if rms_variation > 0.1:  # Banyak variasi volume
        crossfade = min(crossfade + 200, 1000)
    
    return min(crossfade, original_duration * 0.1)  # Max 10% dari durasi original

def plot_audio_waveform(original_audio, looped_audio, sample_rate):
    """
    Plot perbandingan waveform original dan hasil loop
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot original audio
    time_original = np.linspace(0, len(original_audio) / sample_rate, len(original_audio))
    ax1.plot(time_original, original_audio, alpha=0.7, color='blue')
    ax1.set_title('Original Audio Waveform')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Amplitude')
    ax1.grid(True, alpha=0.3)
    
    # Plot looped audio (sample saja untuk efisiensi)
    if len(looped_audio) > sample_rate * 60:  # Jika lebih dari 1 menit, sample
        display_audio = looped_audio[:sample_rate * 30]  # Tampilkan 30 detik pertama
    else:
        display_audio = looped_audio
        
    time_looped = np.linspace(0, len(display_audio) / sample_rate, len(display_audio))
    ax2.plot(time_looped, display_audio, alpha=0.7, color='green')
    ax2.set_title('Looped Audio Waveform (Sample)')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Amplitude')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def main():
    st.set_page_config(
        page_title="Audio Loop Master",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Audio Loop Master")
    st.markdown("""
    Ubah audio pendek menjadi panjang dengan looping yang smooth! 
    Perfect untuk ASMR, ambient sounds, atau background music.
    """)
    
    # Sidebar untuk settings
    st.sidebar.header("Settings")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload Audio File", 
        type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
        help="Upload file audio yang ingin di-loop (disarankan: ASMR, ambient sounds)"
    )
    
    target_duration = st.sidebar.slider(
        "Target Duration (minutes)",
        min_value=1,
        max_value=120,
        value=60,
        help="Durasi akhir audio yang diinginkan dalam menit"
    )
    
    auto_optimize = st.sidebar.checkbox(
        "Auto Optimize Crossfade", 
        value=True,
        help="Otomatis menentukan setting terbaik berdasarkan analisis audio"
    )
    
    if not auto_optimize:
        crossfade_duration = st.sidebar.slider(
            "Crossfade Duration (ms)",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Durasi crossfade antara loop (milidetik)"
        )
    else:
        crossfade_duration = 500  # Default
    
    # Main content
    if uploaded_file is not None:
        try:
            # Load audio file
            with st.spinner("Loading audio file..."):
                audio_bytes = uploaded_file.read()
                
                # Gunakan temp file untuk processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                
                # Load dengan librosa
                audio_data, sample_rate = librosa.load(tmp_path, sr=None, mono=True)
                duration_original = len(audio_data) / sample_rate
                
                # Cleanup temp file
                os.unlink(tmp_path)
            
            # Display original audio info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Original Duration", f"{duration_original:.2f} seconds")
            with col2:
                st.metric("Sample Rate", f"{sample_rate} Hz")
            with col3:
                st.metric("Target Duration", f"{target_duration} minutes")
            
            # Play original audio
            st.subheader("Original Audio")
            st.audio(audio_bytes, format='audio/wav')
            
            # Analyze audio features jika auto optimize
            if auto_optimize:
                with st.spinner("Analyzing audio for optimal looping..."):
                    features = analyze_audio_features(audio_data, sample_rate)
                    crossfade_duration = find_best_crossfade_duration(features, duration_original)
                    st.sidebar.info(f"Auto Crossfade: {crossfade_duration}ms")
            
            # Processing
            if st.button("🚀 Generate Smooth Loop", type="primary"):
                with st.spinner(f"Creating {target_duration} minute smooth loop..."):
                    
                    # Create smooth loop
                    looped_audio_segment = create_smooth_loop(
                        audio_data, 
                        sample_rate, 
                        target_duration,
                        crossfade_duration
                    )
                    
                    # Convert to bytes untuk Streamlit
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_output:
                        looped_audio_segment.export(tmp_output.name, format="wav")
                        
                        # Baca hasil untuk display
                        with open(tmp_output.name, 'rb') as f:
                            looped_audio_bytes = f.read()
                    
                    # Display results
                    st.success(f"✅ Successfully created {target_duration} minute loop!")
                    
                    # Tampilkan audio hasil
                    st.subheader("Looped Audio Result")
                    st.audio(looped_audio_bytes, format='audio/wav')
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Looped Audio",
                        data=looped_audio_bytes,
                        file_name=f"looped_audio_{target_duration}min.wav",
                        mime="audio/wav"
                    )
                    
                    # Visualisasi
                    st.subheader("Audio Visualization")
                    fig = plot_audio_waveform(audio_data, audio_data, sample_rate)  # Simplified for demo
                    st.pyplot(fig)
                    
                    # Cleanup
                    os.unlink(tmp_output.name)
        
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            st.info("Pastikan file audio tidak corrupt dan format didukung.")
    
    else:
        # Default state - show instructions
        st.markdown("""
        ### 🎯 Cara Menggunakan:
        
        1. *Upload Audio* - Pilih file audio pendek (disarankan 10-60 detik)
        2. *Set Duration* - Tentukan durasi akhir yang diinginkan
        3. *Auto Optimize* - Biarkan sistem menentukan setting terbaik
        4. *Generate* - Klik tombol untuk membuat loop smooth
        
        ### 💡 Tips untuk Hasil Terbaik:
        
        - Gunakan audio dengan karakteristik konsisten (ASMR hujan, white noise, dll)
        - Audio dengan fade in/out natural lebih mudah di-loop
        - Durasi original 15-30 detik biasanya ideal
        - Format WAV atau FLAC memberikan kualitas terbaik
        
        ### 🎧 Contoh Audio yang Cocok:
        - Suara hujan 🌧️
        - White noise 📻  
        - Ocean waves 🌊
        - Forest sounds 🌳
        - Ambient music 🎵
        """)
        
        # Example with demo audio
        st.subheader("Quick Demo")
        if st.button("Coba dengan audio sample (akan di-generate)"):
            st.info("Fitur demo membutuhkan integrasi dengan audio sample. Upload file Anda sendiri untuk mencoba!")

if __name__ == "__main__":  # Perbaikan typo
    main()
