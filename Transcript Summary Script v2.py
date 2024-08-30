import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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
def summarize_content(content, progress_var, root):
    try:
        # Update progress bar (set to 25% initially)
        progress_var.set(25)
        root.update_idletasks()
        
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the desired model (e.g., "gpt-4")
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format in a concise and detailed manner, complete with sections for attendees, agenda, summaries of individual points, conclusions, and action items."},
                {"role": "user", "content": f"Please summarize the following meeting transcript:\n\n{content}"}
            ],
            max_tokens=2500,  # Adjust tokens based on the length of summary required
            n=1,
            stop=None,
            temperature=0.5
        )
        
        # Update progress bar (set to 85% during processing)
        progress_var.set(85)
        root.update_idletasks()
        
        summary = response.choices[0].message['content']
        
        # Final update to progress bar (set to 100% when done)
        progress_var.set(100)
        root.update_idletasks()
        
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

# Function to handle the summarization process in a separate thread
def handle_summarization(content, file_path, progress_var, root, progress_window):
    summary = summarize_content(content, progress_var, root)
    if summary:
        save_summary(summary, file_path)
    progress_var.set(100)  # Set progress to 100% on completion
    progress_window.destroy()  # Close the progress window after the process is done
    root.quit()  # Quit the main loop to terminate the program

# Main function to control the GUI flow
def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Step 1: Select a file
    content, file_path = select_file()
    if not content:
        return
    
    # Create a new window for progress indication
    progress_window = tk.Toplevel(root)
    progress_window.title("Processing...")
    progress_window.geometry("300x100")
    
    # Create a label
    label = tk.Label(progress_window, text="Generating Summary...")
    label.pack(pady=10)
    
    # Create a progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
    progress_bar.pack(pady=10, padx=20, fill=tk.X)
    
    # Step 2: Generate summary in a separate thread to keep the GUI responsive
    threading.Thread(target=handle_summarization, args=(content, file_path, progress_var, root, progress_window)).start()

    # Keep the window open until the process is finished
    root.mainloop()

# Run the script
if __name__ == "__main__":
    main()
