import streamlit as st
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import pysrt
import os
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

processor = AutoProcessor.from_pretrained("nurenora/whisper-finetune-telugu")

model = AutoModelForSpeechSeq2Seq.from_pretrained("nurenora/whisper-finetune-telugu")
# Define the supported target languages
LANGUAGES = {
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta"
}

# Define a function to translate the subtitle
def translate_subtitle(subtitle_text, target_language):
    print(subtitle_text)
    # Load the model and tokenizer for the target language
    model_name = "nurenora/whisper-finetune-telugu"
    tokenizer = MT5Tokenizer.from_pretrained(model_name)
    model = MT5ForConditionalGeneration.from_pretrained(model_name)

    # Set the source and target languages
    src_lang = "en"
    tgt_lang = LANGUAGES[target_language]

    # Encode the input text
    input_ids = tokenizer.encode(subtitle_text, return_tensors="pt")
    vocab = tokenizer.get_vocab()
    lang_to_token_id = {}
    for lang in ["en", "te", "ta", "hi"]:
        lang_code = f"{lang}"
        if lang_code in vocab:
            token_id = vocab[lang_code]
            lang_to_token_id[lang] = token_id

    # Generate the translation
    #outputs = model.generate(input_ids=input_ids,
    #                          max_length=512,
    #                          num_beams=4,
    #                          early_stopping=True,
    #                          forced_bos_token_id=tokenizer.get_vocab()[tgt_lang])
    outputs = model.generate(input_ids=input_ids,
                                        num_beams=4,
                                        max_length=512,
                                        early_stopping=True,
                                        bos_token_id=1,
                                        decoder_start_token_id=lang_to_token_id[tgt_lang],
                                        )
    # Decode the output text
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(translated_text)
    return translated_text

# Define the Streamlit app
def app():
    st.title("Subtitle Translator")

    # Enter the subtitle file
    uploaded_file = st.file_uploader("Choose an SRT file", type=".srt")

    # Select the target language
    target_language = st.selectbox("Select the target language", list(LANGUAGES.keys()))

    # Translate the subtitle when the user clicks the button
    if uploaded_file and st.button("Translate"):
        # Create a temporary file path
        temp_file_path = os.path.join("/tmp", uploaded_file.name)

        # Save the uploaded file data to the temporary file
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load the SRT file and extract the subtitle text
        srt_file = pysrt.open(temp_file_path)
        translated_subtitle = []


        subtitle_text = "\n".join([str(sub.text) for sub in srt_file])
        # Translate the subtitle
        translated_text = translate_subtitle(subtitle_text, target_language)

        # Create a new SRT file with the translated subtitles
        '''
        translated_srt_file = pysrt.SubRipFile()
        for i, sub in enumerate(srt_file):
            translated_sub = pysrt.SubRipItem(
                        index=sub.index,
                        start=sub.start,
                        end=sub.end,
                        text=sub.text
            )
            #translated_sub = sub.__copy__()
            #translated_sub.text = translated_text.split("\n")[i]
            #translated_srt_file.append(translated_sub)
            # Translate the subtitle text
            #translated_sub.text = translated_text(sub.text, target_language)

            # Append the translated subtitle item to the list
            translated_srt_file.append(translated_sub)
        '''
        # Download the translated SRT file
        st.download_button(
            label="Download translated SRT file",
            data=translated_text.text.encode('utf-8'),
            file_name="translated.srt",
            mime="text/plain"
        )

# Run the app
if __name__ == "__main__":
    app()
