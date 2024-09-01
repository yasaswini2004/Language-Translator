import moviepy.editor as mp
from pytube import YouTube
import requests
from urllib.parse import urlparse
import speech_recognition as sr
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
from deep_translator import GoogleTranslator
from googletrans import Translator
from gtts import gTTS

def download_video(url):
    # Check if the URL is from YouTube
    if "youtube.com" in url or "youtu.be" in url:
        yt = YouTube(url)
        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first().download(filename="input_video.mp4")
        return "input_video.mp4"
    else:
        # For non-YouTube URLs, use requests to download the video
        response = requests.get(url)
        video_name = urlparse(url).path.split('/')[-1]
        with open(video_name, 'wb') as f:
            f.write(response.content)
        return video_name

def extract_audio(video_path):
    # Extract audio from video
    video = mp.VideoFileClip(video_path)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path)
    return audio_path

def transcribe_large_audio(path, recognizer):
    """Split audio into chunks and apply speech recognition"""
    # Open audio file with pydub
    sound = AudioSegment.from_wav(path)

    # Split audio where silence is 1 second or greater and get chunks
    chunks = split_on_silence(sound, min_silence_len=500, silence_thresh=sound.dBFS-14, keep_silence=500)
    
    # Create folder to store audio chunks
    folder_name = "audio-chunks"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    
    whole_text = ""
    # Process each chunk
    for i, audio_chunk in enumerate(chunks, start=1):
        # Export chunk and save in folder
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")

        # Recognize chunk
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = recognizer.record(source)
            # Convert to text
            try:
                text = recognizer.recognize_google(audio_listened)
            except sr.UnknownValueError as e:
                print("Error:", str(e))
            else:
                text = f"{text.capitalize()}. "
                print(chunk_filename, ":", text)
                whole_text += text

    # Return text for all chunks
    return whole_text

def translate_file(source_file, target_file, source_language='auto', target_language='te'):
    try:
        translated_text = GoogleTranslator(source=source_language, target=target_language).translate_file(source_file)
        with open(target_file, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        print("Translation to Telugu is complete. Check the '{}' file.".format(target_file))
    except Exception as e:
        print("An error occurred during translation:", e)

def translate_text(text, dest_language='te'):
    # Translate text to Telugu
    translator = Translator()
    translated_text = translator.translate(text, dest=dest_language).text
    return translated_text

def convert_text_to_audio(text_file):
    translated_text = ""
    with open(text_file, 'r', encoding='utf-8') as file:
        translated_text = file.read()
    
    translated_audio_path = 'translated_audio.mp3'
    translated_text_telugu = translate_text(translated_text)
    tts = gTTS(text=translated_text_telugu, lang='te')
    tts.save(translated_audio_path)
    
    print("Translated audio saved as:", translated_audio_path)
    return translated_audio_path

def main(video_path):
    recognizer = sr.Recognizer()  # Create a recognizer object
    
    audio_path = extract_audio(video_path)
    result = transcribe_large_audio(audio_path, recognizer)  # Pass the recognizer object
    result_file = 'result.txt'
    print(result)
    print(result, file=open(result_file, 'w'))
    translate_file(result_file, 'output_telugu.txt')
    translated_audio_path = convert_text_to_audio('output_telugu.txt')

    # Combine original video with translated audio
    video = mp.VideoFileClip(video_path)
    translated_audio = mp.AudioFileClip(translated_audio_path)
    video = video.set_audio(translated_audio)
    translated_video_path = "translated_video.mp4"
    video.write_videofile(translated_video_path)

    return translated_video_path  # return the path of the translated video

if __name__ == "__main__":
    url = input("Enter video URL: ")
    video_path = download_video(url)
    if video_path:
        translated_video_path = main(video_path)
        print("Translated video saved as:", translated_video_path)
    else:
        print("Unsupported video source.")
