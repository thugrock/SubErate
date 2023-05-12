import os
import warnings
import argparse
import ffmpeg
import streamlit as st
from typing import List, Dict
import whisper
import base64
import pytube
import time
import io
import sys
from cli import get_audio, get_subtitles

os.environ["WHISPER_MODELS_DIR"] = "./models"

# Define a function to download a file
def download_file(file_path):
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_path}">Download File</a>'
    return href

def download_video(url, resolution):
    try:
        # Create a YouTube object
        youtube = pytube.YouTube(url)

        # Get the stream with the desired resolution
        video_stream = youtube.streams.filter(progressive=True, file_extension='mp4', resolution=resolution).first()

        # Get the filename and download the video
        filename = video_stream.default_filename
        video_stream.download(output_path="./uploads")

        return filename
    except Exception as e:
        st.error(f'Error: {e}')

# Define a custom stream class that redirects writes to sys.stdout to the Streamlit app
class StreamToSt:
    def __init__(self, app):
        self.app = app

    def write(self, text):
        self.app.text(text)


def generate_subtitled_video(video_paths: List[str], model_name: str, output_dir: str, output_srt: bool, srt_only: bool, verbose: bool, task: str = "translate"):

    def transcribe_with_progress(model, audio_path,  **args):
        # Transcribe audio and update progress bar as transcription proceeds
        return model.transcribe(audio_path, **args)


    args = {
        #"model": model_name,
        #"output_dir": output_dir,
        #"output_srt": output_srt,
        #"srt_only": srt_only,
        "verbose": verbose,
        "task": task,
    }
    if model_name.endswith(".en"):
        warnings.warn(
            f"{model_name} is an English-only model, forcing English detection.")
        args["language"] = "en"


    model = whisper.load_model(model_name,  download_root=os.path.join(os.getcwd(), "models"))
    audios = get_audio(video_paths)
    subtitles = get_subtitles(
        #audios, output_srt or srt_only, output_dir, lambda audio_path: model.transcribe(audio_path, **args)
        audios, output_srt or srt_only, output_dir, lambda audio_path: transcribe_with_progress(model, audio_path, **args)
    )

    if srt_only:
        return

    for path, srt_path in subtitles.items():
        out_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(path))[0]}.mp4")

        st.write(f"Adding subtitles to {os.path.basename(path)}...")

        video = ffmpeg.input(path)
        audio = video.audio

        ffmpeg.concat(
            video.filter('subtitles', srt_path, force_style="OutlineColour=&H40000000,BorderStyle=3"), audio, v=1, a=1
        ).output(out_path).run(quiet=True, overwrite_output=True)

        st.write(f"Saved subtitled video to {os.path.abspath(out_path)}.")

        # Display the video player
        st.video(out_path)

        # Display the download button
        st.markdown(download_file(out_path), unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Subtitled Video Generator")

    st.header("Subtitled Video Generator")

    # Create input box for YouTube URL
    youtube_url = st.text_input("Enter a YouTube URL:")

    # Create select box for video resolution
    resolutions = ['360p', '480p', '720p', '1080p']
    selected_resolution = st.selectbox("Select the desired resolution:", resolutions)

    video_paths = st.file_uploader("Select video file(s)", type=["mp4", "avi", "mkv"], accept_multiple_files=True)
    video_full_paths = []
    if video_paths is not None:
        for uploaded_file in video_paths:
            # Create a temporary file path
            temp_file_path = os.path.join("/tmp", uploaded_file.name)

            # Save the uploaded file data to the temporary file
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            video_full_paths.append(temp_file_path)
    # Download YouTube video if URL is provided
    if youtube_url:
        filename = download_video(youtube_url, selected_resolution)
        video_full_paths.append(os.path.join("./uploads", filename))

    model_name = st.selectbox("Select model to use", whisper.available_models())

    output_dir = st.text_input("Output directory", ".")

    output_srt = st.checkbox("Generate .srt file")

    srt_only = st.checkbox("Generate only .srt file")

    verbose = st.checkbox("Verbose")

    task = st.selectbox("Select task", ["translate", "transcribe"])

    # Redirect stdout to the custom stream
    sys.stdout = StreamToSt(st)


    if st.button("Generate Subtitled Video"):
        if video_paths is None:
            st.error("Please select at least one video file.")
        elif not model_name:
            st.error("Please select a model.")
        elif not output_dir:
            st.error("Please enter an output directory.")
        else:
            generate_subtitled_video(video_full_paths, model_name, output_dir, output_srt, srt_only, verbose, task)

    sys.stdout = sys.__stdout__



if __name__ == "__main__":
    main()
