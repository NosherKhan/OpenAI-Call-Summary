import sys
import os
import openai
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar,
                             QPushButton, QFileDialog, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Path to store the encrypted API key
KEY_FILE = "api_key.key"
ENCRYPTED_KEY_FILE = "encrypted_api_key.bin"

def generate_key():
    return Fernet.generate_key()

def load_key():
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

def save_key(key):
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

def encrypt_api_key(key, api_key):
    cipher_suite = Fernet(key)
    ciphered_text = cipher_suite.encrypt(api_key.encode())
    with open(ENCRYPTED_KEY_FILE, "wb") as file:
        file.write(ciphered_text)

def decrypt_api_key(key):
    cipher_suite = Fernet(key)
    with open(ENCRYPTED_KEY_FILE, "rb") as file:
        ciphered_text = file.read()
    return cipher_suite.decrypt(ciphered_text).decode()

def get_api_key():
    if os.path.exists(KEY_FILE) and os.path.exists(ENCRYPTED_KEY_FILE):
        key = load_key()
        return decrypt_api_key(key)
    else:
        return prompt_for_api_key()

def prompt_for_api_key():
    api_key, ok = QInputDialog.getText(None, "API Key", "Enter your OpenAI API key:")
    if ok:
        key = generate_key()
        save_key(key)
        encrypt_api_key(key, api_key)
        return api_key
    else:
        QMessageBox.critical(None, "Error", "API key is required to proceed.")
        sys.exit(1)

class SummarizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Transcript Summarizer")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Select a text file to summarize")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)

        self.btnSelectFile = QPushButton("Select File", self)
        self.btnSelectFile.clicked.connect(self.select_file)
        layout.addWidget(self.btnSelectFile)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Text File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
            self.start_summarization(content, file_path)

    def start_summarization(self, content, file_path):
        self.label.setText("Summarizing file...")
        self.btnSelectFile.setEnabled(False)  # Disable button to prevent multiple submissions
        self.thread = SummarizationThread(content, file_path)
        self.thread.progress.connect(self.update_progress)
        self.thread.completed.connect(self.save_summary)
        self.thread.start()

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def save_summary(self, summary, file_path):
        if summary:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Summary As", f"Summary_{os.path.basename(file_path)}", "Text Files (*.txt);;All Files (*)")
            if save_path:
                with open(save_path, 'w') as file:
                    file.write(summary)
                QMessageBox.information(self, "Success", f"Summary file saved successfully")
        else:
            QMessageBox.critical(self, "Error", f"Failed to summarize the content: {file_path}")

        self.progressBar.setValue(0)  # Reset progress bar after completion
        self.btnSelectFile.setEnabled(True)  # Re-enable the file selection button

class SummarizationThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(str, str)  # Emit summary and file path on completion

    def __init__(self, content, file_path):
        super().__init__()
        self.content = content
        self.file_path = file_path

    def run(self):
        try:
            self.update_status(25, "Connecting to OpenAI API...")
            openai.api_key = get_api_key()

            self.update_status(50, "Processing response...")
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Use the desired model (e.g., "gpt-4")
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format in a concise and detailed manner, complete with sections for attendees, agenda, summaries of individual agenda points (with headings), conclusions, and action items."},
                    {"role": "user", "content": f"Please summarize the following meeting transcript:\n\n{self.content}"}
                ],
                
                max_tokens=5000,  # Adjust tokens based on the length of summary required
                n=1,
                stop=None,
                temperature=0.5
            )

            summary = response.choices[0].message['content']
            self.update_status(100, "Summary completed.")
            self.completed.emit(summary, self.file_path)
        except Exception as e:
            self.completed.emit(None, str(e))

    def update_status(self, progress, status_message):
        self.progress.emit(progress)

def main():
    app = QApplication(sys.argv)
    ex = SummarizerApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


""" 

Explanation of the Modified Script:

    PyQt5 GUI Setup:
       - QWidget is used as the main application window.
       - QVBoxLayout organizes the layout of widgets vertically.
       - QLabel displays instructions to the user.
       - QProgressBar provides visual feedback during the summarization process.
       - QPushButton allows users to trigger file selection.

    File Selection:
       - QFileDialog.getOpenFileName is used to open a file dialog for the user to select a text file.

    Worker Thread for Summarization:
       - A separate QThread class, SummarizationThread, is used to perform the summarization. This ensures the GUI remains responsive during processing.
       - The progress signal is emitted to update the progress bar.
       - The completed signal is emitted with the summary and file path once processing is finished.

    Saving the Summary:
       - Once the summary is generated, another file dialog (QFileDialog.getSaveFileName) is used to save the summary to a file.
       - QMessageBox displays success or error messages to the user.

       
Encryption and Decryption:

    The script uses the cryptography library to securely encrypt and decrypt the API key.
    If the key file exists, the API key is retrieved and decrypted.
    If the key file doesn’t exist, the user is prompted to enter their API key, which is then encrypted and saved.

Persistent Storage:

    The API key is stored in an encrypted format in a file, making it more secure than plain text.

 """