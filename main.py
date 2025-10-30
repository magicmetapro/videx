import streamlit as st
import base64

def main():
    st.set_page_config(
        page_title="Simple Quote Video Maker",
        page_icon="🎬",
        layout="centered"
    )
    
    st.title("🎬 Simple Quote Video Maker")
    st.markdown("Tool sederhana untuk membantu membuat video dengan quotes")
    
    # Video upload
    uploaded_video = st.file_uploader("Upload Video Background", type=['mp4', 'mov'])
    
    if uploaded_video:
        st.video(uploaded_video)
    
    # Quote input
    quote = st.text_area("Masukkan Quotes Anda", height=100)
    
    if quote:
        st.subheader("Preview Quotes:")
        st.info(f"**{quote}**")
        
        # Style options
        st.subheader("Style Suggestions:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Font Size:** 40-60px")
        with col2:
            st.markdown("**Color:** White with black shadow")
        with col3:
            st.markdown("**Position:** Center screen")
    
    if uploaded_video and quote:
        st.success("🎉 Ready to Create!")
        
        st.download_button(
            "📥 Download Video untuk Editing",
            uploaded_video.getvalue(),
            "video_background.mp4",
            "video/mp4"
        )
        
        st.markdown("""
        **Next Steps:**
        1. Download video di atas
        2. Buka aplikasi editing video (CapCut, InShot, dll)
        3. Tambahkan text dengan quote Anda
        4. Atur style sesuai suggestion
        5. Export dan share!
        """)

if __name__ == "__main__":
    main()
