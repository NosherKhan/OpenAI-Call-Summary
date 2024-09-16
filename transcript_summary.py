import sys
import os
import openai
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QInputDialog
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal

# Path to store the encrypted API key
KEY_FILE = "api_key.key"
ENCRYPTED_KEY_FILE = "encrypted_api_key.bin"

# Available models with their token limits
MODELS = {
    "gpt-4": 8192,
    "gpt-4o-mini": 16384,
    "gpt-4o": 32000  # Hypothetical token limit for GPT-4o (example)
}

DEFAULT_MODEL = "gpt-4o-mini"

# Function to generate a new encryption key and save it
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
    return key

# Function to load the encryption key
def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    return None

# Function to save the encryption key
def save_key(key):
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

# Function to encrypt the API key and save it to a file
def encrypt_api_key(key, api_key):
    cipher_suite = Fernet(key)
    ciphered_text = cipher_suite.encrypt(api_key.encode())
    with open(ENCRYPTED_KEY_FILE, "wb") as file:
        file.write(ciphered_text)
    return ciphered_text  # Return the encrypted API key

# Function to decrypt the API key
def decrypt_api_key(key):
    if os.path.exists(ENCRYPTED_KEY_FILE):
        cipher_suite = Fernet(key)
        with open(ENCRYPTED_KEY_FILE, "rb") as file:
            ciphered_text = file.read()
        return cipher_suite.decrypt(ciphered_text).decode()
    return None  # Return None if the encrypted key file does not exist

# Function to get the API key without prompting the user
def get_stored_api_key():
    key = load_key()
    if key and os.path.exists(ENCRYPTED_KEY_FILE):
        return decrypt_api_key(key)
    return None

# Function to prompt the user to enter the API key
def prompt_for_api_key(parent=None):
    api_key, ok = QInputDialog.getText(parent, "API Key", "Enter your OpenAI API key:")
    if ok:
        key = generate_key()
        save_key(key)
        encrypt_api_key(key, api_key)
        return api_key
    else:
        return None

# Function to delete the stored API key
def delete_api_key():
    if os.path.exists(KEY_FILE):
        os.remove(KEY_FILE)
    if os.path.exists(ENCRYPTED_KEY_FILE):
        os.remove(ENCRYPTED_KEY_FILE)
    QMessageBox.information(None, "Success", "API key deleted successfully.")

# Main application class
class SummarizerApp(QMainWindow):
    def __init__(self):
        super(SummarizerApp, self).__init__()
        uic.loadUi("./gui/main_window.ui", self)  # Load the .ui file from the gui folder
        self.api_key = get_stored_api_key()  # Check if API key is stored
        self.gpt_model = DEFAULT_MODEL  # Default GPT model
        
        # Connect buttons and initialize UI
        self.api_key_button.clicked.connect(self.reenter_api_key)
        self.btnSelectFile.clicked.connect(self.select_file)
        self.update_api_status()

    # Update the API key status label and button state
    def update_api_status(self):
        if self.api_key:
            self.api_status_label.setText("API Key: Entered")
            self.api_status_label.setStyleSheet("color: green;")
            self.api_key_button.setEnabled(False)  # Disable if API key is already entered
        else:
            self.api_status_label.setText("API Key: Not Entered")
            self.api_status_label.setStyleSheet("color: red;")
            self.api_key_button.setEnabled(True)

    # Function to re-enter the API key
    def reenter_api_key(self):
        self.api_key = prompt_for_api_key(self)
        if self.api_key:
            QMessageBox.information(self, "Success", "API key entered successfully.")
        self.update_api_status()

    # Function to select a file
    def select_file(self):
        if not self.api_key:  # Prompt for API key if not entered
            self.reenter_api_key()
            if not self.api_key:  # If API key is still not entered, stop the process
                return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Text File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # Token counting and model selection logic goes here
            self.start_summarization(content, file_path)

    # Function to start the summarization process
    def start_summarization(self, content, file_path):
        self.btnSelectFile.setEnabled(False)  # Disable button to prevent multiple submissions
        self.thread = SummarizationThread(content, file_path, self.gpt_model)
        self.thread.progress.connect(self.update_progress)
        self.thread.completed.connect(self.save_summary)
        self.thread.start()

    # Function to update the progress bar
    def update_progress(self, value):
        self.progressBar.setValue(value)

    # Function to save the summary
    def save_summary(self, summary, file_path):
        if summary:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Summary As", f"Summary_{os.path.basename(file_path)}", "Text Files (*.txt);;All Files (*)")
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as file:
                    file.write(summary)
                QMessageBox.information(self, "Success", f"Summary saved successfully.")
            
                # Save the file with .md extension silently
                md_save_path = os.path.splitext(save_path)[0] + ".md"
                with open(md_save_path, 'w', encoding='utf-8') as md_file:
                    md_file.write(summary)
            else:
                QMessageBox.critical(self, "Error", f"Failed to summarize the content: {file_path}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to summarize the content: {file_path}")
        self.progressBar.setValue(0)  # Reset progress bar
        self.btnSelectFile.setEnabled(True)  # Re-enable the file selection button

# Summarization thread to run the OpenAI API call
class SummarizationThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(str, str)  # Emit summary and file path on completion

    def __init__(self, content, file_path, gpt_model):
        super().__init__()
        self.content = content
        self.file_path = file_path
        self.gpt_model = gpt_model

    def run(self):
        try:
            self.progress.emit(25)
            openai.api_key = get_stored_api_key()
            response = openai.ChatCompletion.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format, including sections for attendees, agenda, summaries of agenda points, conclusions, and action items, in a detailed and conversational manner."},  # The prompt passed to OpenAI
                    {"role": "user", "content": f"Please summarize the following:\n\n{self.content}"}
                ],
                max_tokens=500,
                n=1,
                stop=None,
                temperature=0.5
            )
            self.progress.emit(85)
            summary = response.choices[0].message['content']
            self.progress.emit(100)
            self.completed.emit(summary, self.file_path)
        except Exception as e:
            self.completed.emit(None, str(e))

# Main function to run the application
def main():
    app = QApplication(sys.argv)
    ex = SummarizerApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
