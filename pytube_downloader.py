import yt_dlp
import os
import streamlit as st
import re
from urllib.parse import urlparse, parse_qs
from PIL import Image
import requests
import logging
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the main download folder and subfolders
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "youtube_downloads")
VIDEO_FOLDER = os.path.join(DOWNLOAD_FOLDER, "Videos")
AUDIO_FOLDER = os.path.join(DOWNLOAD_FOLDER, "Audio")

# Ensure the folders exist
def create_folders():
    """Creates the main download folder and subfolders if they don't exist."""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    os.makedirs(VIDEO_FOLDER, exist_ok=True)
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Function to sanitize filenames
def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F\x7F\[\],#]', '_', filename)
    sanitized = sanitized.replace(" ", "_")
    max_length = 255  # Leave room for the file extension
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized

# Function to update the progress bar
def update_progress(d, progress_bar, stop_event):
    """Update the progress bar based on download status."""
    if stop_event.is_set():
        raise Exception("Download cancelled by user.")
    if d['status'] == 'downloading' and '_percent_str' in d:
        percentage = d['_percent_str']
        cleaned_percentage = ''.join(filter(lambda x: x.isdigit() or x == '%', percentage))
        try:
            progress_value = int(cleaned_percentage.strip('%')) / 100
            progress_bar.progress(progress_value)
        except ValueError:
            progress_bar.progress(0)

# Function to download video/audio
def download_best_stream(url, format_option="bv*+ba/best", progress_bar=None, stop_event=None):
    """Downloads the best available stream (video + audio)."""
    create_folders()  # Ensure folders exist

    # Proceed with the download
    ydl_opts = {
        'outtmpl': f'{VIDEO_FOLDER}/%(title)s.%(ext)s',  # Save in Videos subfolder
        'format': format_option,
        'progress_hooks': [lambda d: update_progress(d, progress_bar, stop_event)] if progress_bar else [],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Untitled')
            video_ext = info_dict.get('ext', 'mp4')
            
            # Sanitize the video title
            sanitized_title = sanitize_filename(video_title)
            downloaded_file_path = os.path.join(VIDEO_FOLDER, f"{sanitized_title}.{video_ext}")

        logging.info(f"✅ Download completed successfully in: {VIDEO_FOLDER}")
        return downloaded_file_path  # Return the downloaded file path

    except yt_dlp.DownloadError as e:
        logging.error(f"❌ Download error: {e}")
        st.error(f"❌ Download error: {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        st.error(f"❌ Unexpected error: {e}")
        return None

# Function to download audio
def download_audio(url, progress_bar=None, stop_event=None):
    """Downloads the best available audio stream (MP3)."""
    create_folders()  # Ensure folders exist

    ydl_opts = {
        'outtmpl': f'{AUDIO_FOLDER}/%(title)s.%(ext)s',  # Save in Audio subfolder
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [lambda d: update_progress(d, progress_bar, stop_event)] if progress_bar else [],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            audio_title = info_dict.get('title', 'Untitled')
            sanitized_title = sanitize_filename(audio_title)
            downloaded_file_path = os.path.join(AUDIO_FOLDER, f"{sanitized_title}.mp3")
        logging.info(f"✅ Audio download completed successfully in: {AUDIO_FOLDER}")
        return downloaded_file_path
    except yt_dlp.DownloadError as e:
        logging.error(f"❌ Audio download error: {e}")
        st.error(f"❌ Audio download error: {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        st.error(f"❌ Unexpected error: {e}")
        return None

# Function to download playlist
def download_playlist(url, progress_bar=None, stop_event=None):
    """Downloads a YouTube playlist."""
    create_folders()  # Ensure folders exist

    ydl_opts = {
        'outtmpl': f'{VIDEO_FOLDER}/%(playlist_index)s - %(title)s.%(ext)s',  # Save in Videos subfolder
        'format': 'bv*+ba/best',
        'progress_hooks': [lambda d: update_progress(d, progress_bar, stop_event)] if progress_bar else [],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logging.info(f"✅ Playlist download completed successfully in: {VIDEO_FOLDER}")
        return VIDEO_FOLDER
    except yt_dlp.DownloadError as e:
        logging.error(f"❌ Playlist download error: {e}")
        st.error(f"❌ Playlist download error: {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        st.error(f"❌ Unexpected error: {e}")
        return None

# Function to download channel
def download_channel(url, progress_bar=None, stop_event=None):
    """Downloads videos from a YouTube channel."""
    create_folders()  # Ensure folders exist

    ydl_opts = {
        'outtmpl': f'{VIDEO_FOLDER}/%(uploader)s/%(title)s.%(ext)s',  # Save in Videos subfolder
        'format': 'bv*+ba/best',
        'progress_hooks': [lambda d: update_progress(d, progress_bar, stop_event)] if progress_bar else [],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logging.info(f"✅ Channel download completed successfully in: {VIDEO_FOLDER}")
        return VIDEO_FOLDER
    except yt_dlp.DownloadError as e:
        logging.error(f"❌ Channel download error: {e}")
        st.error(f"❌ Channel download error: {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        st.error(f"❌ Unexpected error: {e}")
        return None

# Function to get YouTube thumbnail (with caching)
thumbnail_cache = {}
def get_youtube_thumbnail(url):
    """Extracts the video ID from a YouTube URL and returns the thumbnail URL."""
    try:
        if url in thumbnail_cache:
            return thumbnail_cache[url]

        parsed_url = urlparse(url)
        if parsed_url.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']:
            if 'youtube.com' in parsed_url.netloc:
                if parsed_url.path == '/watch':
                    video_id = parse_qs(parsed_url.query)['v'][0]
                elif parsed_url.path.startswith('/shorts/'):
                    video_id = parsed_url.path.split('/')[-1]
                else:
                    return None
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path[1:]
            else:
                return None
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            thumbnail_cache[url] = thumbnail_url
            return thumbnail_url
        else:
            return None
    except:
        return None

# --- Streamlit UI Enhancements ---

# Custom CSS for styling
st.markdown("""
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stProgress>div>div>div {
        background-color: #4CAF50;
    }
    .stTextInput>div>div>input {
        padding: 10px;
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    .stMarkdown {
        font-family: 'Arial', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎥 YouTube Downloader")

# 1. Sidebar Accordion for Options
with st.sidebar:
    st.header("Download Options")
    selected_option = st.radio(
        "Choose a download type:",
        ["Download Video", "Download Audio (MP3)", "Download Video-only", "Download Playlist", "Download Channel"]
    )

    # Add quality selection for video downloads
    if selected_option in ["Download Video", "Download Video-only"]:
        quality_options = {
            "Best Quality": "bv*+ba/best",
            "1080p": "bv*[height<=1080]+ba/best",
            "720p": "bv*[height<=720]+ba/best",
            "480p": "bv*[height<=480]+ba/best",
            "360p": "bv*[height<=360]+ba/best",
            "240p": "bv*[height<=240]+ba/best",
            "144p": "bv*[height<=144]+ba/best",
        }
        selected_quality = st.selectbox("Select Video Quality", list(quality_options.keys()))
        format_option = quality_options[selected_quality]
    elif selected_option == "Download Audio (MP3)":
        format_option = "bestaudio/best"
    else:
        format_option = "bv*+ba/best"

# 2. Input Field with Placeholder and Validation
url = st.text_input("Enter the YouTube URL:", placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
if url and ("youtube.com" not in url) and ("youtu.be" not in url):
    st.warning("Please enter a valid YouTube URL.")
else:
    # Display Thumbnail
    thumbnail_url = get_youtube_thumbnail(url)
    if thumbnail_url:
        try:
            response = requests.get(thumbnail_url, stream=True)
            if response.status_code == 200:
                image = Image.open(response.raw)
                st.image(image, width=200, caption="YouTube Thumbnail")
            else:
                st.warning("Could not fetch thumbnail. Using default thumbnail.")
                # Fix the fallback thumbnail URL
                video_id = parse_qs(urlparse(url).query).get('v', [''])[0]
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/default.jpg"
                response = requests.get(thumbnail_url, stream=True)
                if response.status_code == 200:
                    image = Image.open(response.raw)
                    st.image(image, width=200, caption="YouTube Thumbnail")
        except Exception as e:
            st.warning(f"Could not display thumbnail: {e}")
    else:
        st.warning("Could not fetch thumbnail. Please check the URL.")

# 3. Download Button with Feedback
if st.button("Download"):
    if url:
        stop_event = threading.Event()  # Event to signal cancellation
        progress_bar = st.progress(0)  # Initialize progress bar
        cancel_button = st.button("Cancel Download")  # Cancel button

        with st.spinner("Downloading..."):
            try:
                # Call the appropriate download function
                if selected_option == "Download Video":
                    downloaded_file_path = download_best_stream(url, format_option=format_option, progress_bar=progress_bar, stop_event=stop_event)
                elif selected_option == "Download Audio (MP3)":
                    downloaded_file_path = download_audio(url, progress_bar=progress_bar, stop_event=stop_event)
                elif selected_option == "Download Video-only":
                    downloaded_file_path = download_best_stream(url, format_option=format_option, progress_bar=progress_bar, stop_event=stop_event)
                elif selected_option == "Download Playlist":
                    downloaded_file_path = download_playlist(url, progress_bar=progress_bar, stop_event=stop_event)
                elif selected_option == "Download Channel":
                    downloaded_file_path = download_channel(url, progress_bar=progress_bar, stop_event=stop_event)
                else:
                    downloaded_file_path = None
                    st.error("Invalid download option selected.")

                if cancel_button:
                    stop_event.set()  # Signal cancellation
                    st.warning("Download cancelled by user.")
                elif downloaded_file_path:
                    st.success("Download complete!")

                    # Display downloaded file information with a download logo
                    st.write("Downloaded File:")
                    st.write(f"**Location:** {downloaded_file_path}")
                    st.markdown(
                        f'<a href="{downloaded_file_path}" download="{os.path.basename(downloaded_file_path)}">'
                        f'<img src="https://img.icons8.com/fluency/48/000000/download.png" alt="Download" width="20" height="20"> Download File</a>',
                        unsafe_allow_html=True,
                    )

            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
    else:
        st.warning("Please enter a YouTube URL.")