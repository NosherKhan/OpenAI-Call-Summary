import tkinter as tk
from tkinter import filedialog, messagebox
import openai
import threading
import os

# Set up OpenAI API key
openai.api_key = "sk-LRu8nLsqrRsW88-b-JqvaGphxxCPvvHgY-Pt08IU5IT3BlbkFJ-gB-pSI8OFXjKBhYAzY9b-RtcP3KxtBfr1CTudNmIA"  # Replace with your OpenAI API key

# Function to select a text file and return its content
def select_file():
    file_path = filedialog.askopenfilename(
        title="Select a Text File",
        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
    )
    if file_path:
        with open(file_path, 'r') as file:
            content = file.read()
        return content, file_path
    return None, None

# Function to summarize the content using OpenAI
def summarize_content(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the desired model (e.g., "gpt-4")
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format in a concise and detailed manner."},
                {"role": "user", "content":  f"Please summarize the following meeting transcript:\n\n{content}"}
            ],
            max_tokens=500,  # Adjust tokens based on the length of summary required
            n=1,
            stop=None,
            temperature=0.5
        )
        summary = response.choices[0].message['content']
        return summary
    except Exception as e:
        messagebox.showerror("Error", f"Failed to summarize the content: {e}")
        return None

# Function to save the summary as a text file
def save_summary(summary, original_file_path):
    save_path = filedialog.asksaveasfilename(
        title="Save Summary As",
        defaultextension=".txt",
        initialfile=f"Summary_{os.path.basename(original_file_path)}",
        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
    )
    if save_path:
        with open(save_path, 'w') as file:
            file.write(summary)
        messagebox.showinfo("Success", f"Summary saved successfully at {save_path}")

# Main function to control the GUI flow
def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Step 1: Select a file
    content, file_path = select_file()
    if not content:
        return

    # Step 2: Generate summary
    summary = summarize_content(content)
    if not summary:
        return

    # Step 3: Save the summary
    save_summary(summary, file_path)

# Run the script
if __name__ == "__main__":
    main()
