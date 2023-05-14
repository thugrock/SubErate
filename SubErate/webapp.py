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
def translate_subtitle(subtitle_path, target_lang):
    # Load subtitle file
    subs = pysrt.open(subtitle_path)
    # Initialize translator
    translator = Translator(to_lang=target_lang)
    # Translate each subtitle and update the text
    for sub in subs:
        sub.text = translator.translate(sub.text)
    # Save the translated subtitle as a new file
    output_path = f"{subtitle_path.split('.')[0]}_{target_lang}.srt"
    subs.save(output_path, encoding='utf-8')
    return output_path

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
        video_stream.download(output_path=os.getcwd()+"/uploads")

        return filename
    except Exception as e:
        st.error(f'Error: {e}')

# Define a custom stream class that redirects writes to sys.stdout to the Streamlit app
class StreamToSt:
    def __init__(self, app):
        self.app = app

    def write(self, text):
        self.app.text(text)


def generate_subtitled_video(video_paths: List[str], model_name: str, output_dir: str, output_srt: bool, srt_only: bool, verbose: bool, target_lang: str = "en", task: str = "translate"):

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
        outt_path = translate_subtitle(srt_path, target_lang) if target_lang != "en" else srt_path
        font_path = os.path.join(os.getcwd(), 'NotoSans-Regular.ttf')
        ffmpeg.concat(
            video.filter('subtitles', outt_path, force_style=f"FontName={font_path},OutlineColour=&H40000000,BorderStyle=3"), audio, v=1, a=1
        ).output(out_path).run(quiet=True, overwrite_output=True)

        st.write(f"Saved subtitled video to {os.path.abspath(out_path)}.")

        # Display the video player
        st.video(out_path)

        # Display the download button
        st.write(f"Click Below to download subbed video")
        st.markdown(download_file(out_path), unsafe_allow_html=True)
        st.write(f"Click Below to download English SRT")
        st.markdown(download_file(srt_path), unsafe_allow_html=True)
        if target_lang != "en":
            st.write(f"Click Below to download target SRT")
            st.markdown(download_file(outt_path), unsafe_allow_html=True)


def main():

    st.set_page_config(page_title="SubErate")

    st.header("Subtitled Video Translator and Transcriber")

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
            temp_file_path = os.path.join(os.getcwd(), 'uploads', uploaded_file.name)

            # Save the uploaded file data to the temporary file
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            video_full_paths.append(temp_file_path)
    # Download YouTube video if URL is provided
    if youtube_url:
        filename = download_video(youtube_url, selected_resolution)
        video_full_paths.append(os.path.join(os.getcwd(), "uploads", filename))

    model_name = st.selectbox("Select model to use", whisper.available_models())

    output_dir = st.text_input("Output directory", ".")

    output_srt = st.checkbox("Generate .srt file")

    srt_only = st.checkbox("Generate only .srt file")

    verbose = st.checkbox("Verbose")

    task = st.selectbox("Select task", ["translate", "transcribe"])

    language_dict = {"English":"en", "Telugu":"te","Hindi":"hi","Tamil":"te"}
    target_lang = st.selectbox("Select target language for subtitles", list(language_dict.keys()))
    target_lang = language_dict[target_lang]

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
            generate_subtitled_video(video_full_paths, model_name, output_dir, output_srt, srt_only, verbose, target_lang, task)

    sys.stdout = sys.__stdout__



if __name__ == "__main__":
    main()
