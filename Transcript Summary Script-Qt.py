import sys
import os
import openai
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Set up OpenAI API key
openai.api_key = "sk-LRu8nLsqrRsW88-b-JqvaGphxxCPvvHgY-Pt08IU5IT3BlbkFJ-gB-pSI8OFXjKBhYAzY9b-RtcP3KxtBfr1CTudNmIA"  # Replace with your OpenAI API key

# Worker thread to perform the summarization
class SummarizationThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(str, str)  # Emit summary and file path on completion

    def __init__(self, content, file_path):
        super().__init__()
        self.content = content
        self.file_path = file_path

    def run(self):
        try:
            self.progress.emit(25)
            
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Use the desired model (e.g., "gpt-4")
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts in a Minutes of the Meeting format in a concise and detailed manner, complete with sections for attendees, agenda, summaries of individual agenda points (with headings), conclusions, and action items."},
                {"role": "user", "content": f"Please summarize the following meeting transcript:\n\n{self.content}"}
                ],
                
                max_tokens=2500,  # Adjust tokens based on the length of summary required
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

# Main application window
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
        self.label = QLabel("Summarizing file...")
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

# Main function to run the application
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
 """