import sys
import os
import openai
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar,
                             QPushButton, QFileDialog, QMessageBox, QInputDialog, QMenuBar, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Path to store the encrypted API key
KEY_FILE = "api_key.key"
ENCRYPTED_KEY_FILE = "encrypted_api_key.bin"

# Available models with their token limits
MODELS = {
    "gpt-3.5-turbo": 4096,
    "gpt-4": 8192,
    "gpt-4o": 32000  # Hypothetical token limit for gpt-4o (example)
}

DEFAULT_MODEL = "gpt-3.5-turbo"

# Function to generate a new encryption key
def generate_key():
    return Fernet.generate_key()

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

# Function to encrypt the API key
def encrypt_api_key(key, api_key):
    cipher_suite = Fernet(key)
    ciphered_text = cipher_suite.encrypt(api_key.encode())
    with open(ENCRYPTED_KEY_FILE, "wb") as file:
        file.write(ciphered_text)

# Function to decrypt the API key
def decrypt_api_key(key):
    cipher_suite = Fernet(key)
    with open(ENCRYPTED_KEY_FILE, "rb") as file:
        ciphered_text = file.read()
    return cipher_suite.decrypt(ciphered_text).decode()

# Function to get the API key, prompting the user if necessary
def get_api_key():
    key = load_key()
    if key and os.path.exists(ENCRYPTED_KEY_FILE):
        return decrypt_api_key(key)
    else:
        return prompt_for_api_key()

# Function to prompt the user to enter the API key
def prompt_for_api_key():
    api_key, ok = QInputDialog.getText(None, "API Key", "Enter your OpenAI API key:")
    if ok:
        key = generate_key()
        save_key(key)
        encrypt_api_key(key, api_key)
        return api_key
    else:
        QMessageBox.critical(None, "Error", "API key is required to proceed.")
        return None

# Function to delete the stored API key
def delete_api_key():
    if os.path.exists(KEY_FILE):
        os.remove(KEY_FILE)
    if os.path.exists(ENCRYPTED_KEY_FILE):
        os.remove(ENCRYPTED_KEY_FILE)
    QMessageBox.information(None, "Success", "API key deleted successfully.")

# Function to estimate token count
def estimate_token_count(text):
    words = text.split()
    return int(len(words) * 1.33)  # Approximation of 1.33 tokens per word

# Function to select the model based on token count
def select_model(token_count):
    for model, token_limit in MODELS.items():
        if token_count <= token_limit:
            return model
    return DEFAULT_MODEL

# Main application class
class SummarizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.api_key = get_api_key()
        self.gpt_model = DEFAULT_MODEL  # Default GPT model
        if self.api_key:
            self.initUI()

    # Initialize the user interface
    def initUI(self):
        self.setWindowTitle("Transcript Summarizer")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        # Menu Bar
        self.menu_bar = QMenuBar(self)

        # API key management menu
        api_menu = self.menu_bar.addMenu("API Key")
        enter_api_action = QAction("Re-enter API Key", self)
        enter_api_action.triggered.connect(self.reenter_api_key)
        api_menu.addAction(enter_api_action)

        delete_api_action = QAction("Delete API Key", self)
        delete_api_action.triggered.connect(delete_api_key)
        api_menu.addAction(delete_api_action)

        # GPT model selection menu
        self.model_menu = self.menu_bar.addMenu("Model")
        for model_name in MODELS.keys():
            action = QAction(model_name, self, checkable=True)
            action.triggered.connect(lambda checked, m=model_name: self.set_model(m))
            self.model_menu.addAction(action)

        # Label and Progress Bar
        self.label = QLabel("Select a text file to summarize")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.model_label = QLabel(f"Selected Model: {self.gpt_model}")
        self.model_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.model_label)

        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)

        # File Selection Button
        self.btnSelectFile = QPushButton("Select File", self)
        self.btnSelectFile.clicked.connect(self.select_file)
        layout.addWidget(self.btnSelectFile)

        layout.setMenuBar(self.menu_bar)
        self.setLayout(layout)

        self.update_model_menu()

    # Function to update the model menu with a checkmark for the selected model
    def update_model_menu(self):
        for action in self.model_menu.actions():
            action.setChecked(action.text() == self.gpt_model)

    # Function to re-enter the API key
    def reenter_api_key(self):
        self.api_key = prompt_for_api_key()
        if self.api_key:
            QMessageBox.information(self, "Success", "API key updated successfully.")

    # Function to set the GPT model
    def set_model(self, model_name):
        self.gpt_model = model_name
        self.model_label.setText(f"Selected Model: {model_name}")
        self.update_model_menu()
        QMessageBox.information(self, "Model Selection", f"GPT model set to {model_name}")

    # Function to select a file and estimate tokens
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Text File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
            token_count = estimate_token_count(content)
            self.gpt_model = select_model(token_count)
            self.model_label.setText(f"Selected Model: {self.gpt_model}")
            self.update_model_menu()
            self.start_summarization(content, file_path)

    # Function to start the summarization process
    def start_summarization(self, content, file_path):
        self.label.setText(f"Summarizing file... (Using {self.gpt_model})")
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
                with open(save_path, 'w') as file:
                    file.write(summary)
                QMessageBox.information(self, "Success", f"Summary saved successfully.")
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
            openai.api_key = get_api_key()
            response = openai.ChatCompletion.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format in a concise and detailed manner, complete with sections for attendees, agenda, summaries of individual agenda points (with headings), conclusions, and action items."},  # The prompt passed to OpenAI
                    {"role": "user", "content": f"Please summarize the following meeting transcript:\n\n{self.content}"}
                ],
                max_tokens=500,  # Adjust tokens based on the length of summary required
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
    if ex.api_key:  # Only show UI if API key is set
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

< 2024.09.04 >

Enhanced get_api_key and prompt_for_api_key:

    Centralized logic for handling API key retrieval and prompting the user if the key is not already stored.

UI Improvements:

    Disabled the file selection button during processing to prevent multiple submissions.
    Enhanced status messages in the SummarizationThread to provide more detailed feedback to the user.

Error Handling:

    Added error handling in the case where the user does not provide an API key.

Modularity:

    Further broke down functions for better readability and maintainability.

< 2024.09.05 >

API Key Management:

    Re-enter API Key: Option in the "API Key" menu to re-enter the OpenAI API key.
    Delete API Key: Option in the "API Key" menu to delete the stored API key.

Model Selection:

    Select GPT Model: Option in the "Model" menu to choose between different GPT models (gpt-3.5-turbo, gpt-4, etc.).

Improved Flow:

    The application no longer quits after entering the API key.
    API key prompts are handled correctly

Quitting After API Key Input: 
    The app was quitting because of the sys.exit(1) call in the prompt_for_api_key() function. Now, it returns None instead of exiting the app, allowing it to continue and let the user enter a valid key later if needed.

File Existence Check for Encryption Key: 
    I added a check for KEY_FILE existence in load_key(). If the file doesn’t exist, the app won’t attempt to load it and will instead prompt for the key.

Corrected File Path Handling: 
    If no file is selected, the program won’t crash. It now gracefully handles file operations.

API Key Management: 
    You can now delete and re-enter the API key from the menu.

General Bug Fixes: 
    Fixed various minor issues in the previous logic, including path handling and error handling.

Analyze the File: 
    Read the file, calculate the number of tokens, and select an appropriate model.

Model Selection Logic: 
    Use available models (e.g., gpt-3.5-turbo, gpt-4, gpt-4o, etc.) based on the number of tokens required. GPT models have token limits (e.g., 4096 for gpt-3.5-turbo and up to 32k for gpt-4o).

Show Selected Model: 
    Display the selected model on the screen and add a checkmark in the menu to indicate the chosen model.

 """