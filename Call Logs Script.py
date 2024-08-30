# !pip install git+https://github.com/openai/whisper.git
# !pip install openai==0.28.0
# !pip install ffmpeg-python

import os
import tkinter as tk
from tkinter import filedialog
import openai
openai.api_key = "sk-LRu8nLsqrRsW88-b-JqvaGphxxCPvvHgY-Pt08IU5IT3BlbkFJ-gB-pSI8OFXjKBhYAzY9b-RtcP3KxtBfr1CTudNmIA"

def transcribe_audio(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcript_text = transcript["text"]

        # Save the transcript to a .txt file
        base_name = os.path.splitext(audio_file_path)[0]
        transcript_file = base_name + ".txt"

        with open(transcript_file, "w") as txt_file:
            txt_file.write(transcript_text)
        
        print(f"Transcript audio saved to {transcript_file}")
        return transcript_text

def select_audio_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select an audio file", filetypes=[("Audio Files", "*.mp3;*.wav;*.m4a")])
      
# audio_file_path = "C:\\Users\\nokhan\\Downloads\\A Guide For the Recovering Avoidant.m4a"
# transcribe_audio(audio_file_path)

def summarize_transcript(filename):
    with open(filename, 'r') as f:
        transcript = f.read()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format in a concise and detailed manner."},
            {"role": "user", "content": f"Please summarize the following meeting transcript:\n\n{transcript}"}
        ]
    )

    summary = response['choices'][0]['message']['content']
    return summary


if __name__ == "__main__":
    audio_file_path = select_audio_file()

    if audio_file_path:
        transcript_file = transcribe_audio(audio_file_path)
    
    # Assuming you want to summarize after transcription
    summary = summarize_transcript(transcript_file)
    print(summary)
    
    with open("summary.txt", 'w') as f:
        f.write(summary)