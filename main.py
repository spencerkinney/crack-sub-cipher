import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QWidget, QProgressBar, QShortcut, QHBoxLayout, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont, QKeySequence, QColor
from cipher_utils import CipherUtils
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Color constants
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#00b34a"
SECONDARY_COLOR = "#333333"
HOVER_COLOR = "#009940"
FINAL_TEXT_COLOR = "#90EE90"

class DecryptionThread(QThread):
    progress_signal = pyqtSignal(int, float, str)
    run_finished_signal = pyqtSignal(str, dict, float)
    all_finished_signal = pyqtSignal(str, dict, float)

    def __init__(self, ciphertext, max_iterations, restarts, num_runs):
        super().__init__()
        self.ciphertext = ciphertext
        self.max_iterations = max_iterations
        self.restarts = restarts
        self.num_runs = num_runs

    def run(self):
        best_decrypted, best_key, best_score = "", {}, float('-inf')
        cipher = CipherUtils(self.ciphertext)
        
        for run in range(self.num_runs):
            decrypted, key = cipher.decrypt(
                max_iterations=self.max_iterations,
                restarts=self.restarts,
                callback=lambda i, s, d: self.progress_signal.emit(run * self.max_iterations * self.restarts + i, s, d)
            )
            score = cipher.ngram_score(decrypted) + cipher.valid_word_percentage(decrypted)
            self.run_finished_signal.emit(decrypted, key, score)
            
            if score > best_score:
                best_decrypted, best_key, best_score = decrypted, key, score

        self.all_finished_signal.emit(best_decrypted, best_key, best_score)

class StyleCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        self.axes.set_facecolor(BACKGROUND_COLOR)
        
        self.axes.grid(True, linestyle='--', alpha=0.2, color=SECONDARY_COLOR)
        
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        
        self.axes.tick_params(axis='x', colors=TEXT_COLOR)
        self.axes.tick_params(axis='y', colors=TEXT_COLOR)
        
        self.axes.set_xlabel('Iterations', color=TEXT_COLOR)
        self.axes.set_ylabel('Score', color=TEXT_COLOR)
        self.axes.set_title('Decryption Score Progress', color=TEXT_COLOR)

        super(StyleCanvas, self).__init__(fig)
        self.setParent(parent)

class CipherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scores = []

    def initUI(self):
        self.setWindowTitle('Substitution Cipher Decryption Visualizer')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
            }}
            QTextEdit, QSpinBox {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {SECONDARY_COLOR};
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: {TEXT_COLOR};
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {ACCENT_COLOR};
            }}
            QProgressBar {{
                border: none;
                background-color: {SECONDARY_COLOR};
                text-align: center;
                border-radius: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_COLOR};
                border-radius: 10px;
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
        """)

        main_layout = QVBoxLayout()

        # Input section
        input_layout = QHBoxLayout()
        self.ciphertext_input = QTextEdit()
        self.ciphertext_input.setPlaceholderText("Enter ciphertext here...")
        input_layout.addWidget(self.ciphertext_input, 3)

        settings_layout = QVBoxLayout()
        self.iterations_input = QSpinBox()
        self.iterations_input.setRange(100, 100000)
        self.iterations_input.setValue(10000)
        settings_layout.addWidget(QLabel("Iterations per restart:"))
        settings_layout.addWidget(self.iterations_input)

        self.restarts_input = QSpinBox()
        self.restarts_input.setRange(1, 100)
        self.restarts_input.setValue(10)
        settings_layout.addWidget(QLabel("Restarts:"))
        settings_layout.addWidget(self.restarts_input)

        self.num_runs_input = QSpinBox()
        self.num_runs_input.setRange(1, 10)
        self.num_runs_input.setValue(3)
        settings_layout.addWidget(QLabel("Number of complete runs:"))
        settings_layout.addWidget(self.num_runs_input)

        self.crack_button = QPushButton('Crack Cipher')
        self.crack_button.clicked.connect(self.start_decryption)
        settings_layout.addWidget(self.crack_button)
        settings_layout.addStretch()

        input_layout.addLayout(settings_layout, 1)
        main_layout.addLayout(input_layout)

        # Progress section
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar, 4)
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label, 1)
        main_layout.addLayout(progress_layout)

        # Chart
        self.chart_canvas = StyleCanvas(self, width=5, height=3, dpi=100)
        main_layout.addWidget(self.chart_canvas)

        # Output section
        output_layout = QHBoxLayout()
        
        left_output = QVBoxLayout()
        left_output.addWidget(QLabel("Decrypted Text:"))
        self.decrypted_text = QTextEdit()
        self.decrypted_text.setReadOnly(True)
        left_output.addWidget(self.decrypted_text)
        output_layout.addLayout(left_output, 2)

        right_output = QVBoxLayout()
        right_output.addWidget(QLabel("Key Mapping:"))
        self.key_display = QTextEdit()
        self.key_display.setReadOnly(True)
        right_output.addWidget(self.key_display)
        output_layout.addLayout(right_output, 1)

        main_layout.addLayout(output_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Set Enter key to trigger the button
        shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        shortcut.activated.connect(self.start_decryption)

    def start_decryption(self):
        ciphertext = self.ciphertext_input.toPlainText()
        if not ciphertext.strip():
            return

        self.crack_button.setEnabled(False)
        self.crack_button.setText("Decrypting...")
        self.progress_bar.setValue(0)
        self.progress_label.setText("Decrypting...")
        self.scores = []
        self.decrypted_text.setStyleSheet(f"QTextEdit {{ color: {TEXT_COLOR}; }}")
        self.key_display.setStyleSheet(f"QTextEdit {{ color: {TEXT_COLOR}; }}")

        max_iterations = self.iterations_input.value()
        restarts = self.restarts_input.value()
        num_runs = self.num_runs_input.value()

        self.decryption_thread = DecryptionThread(ciphertext, max_iterations, restarts, num_runs)
        self.decryption_thread.progress_signal.connect(self.update_progress)
        self.decryption_thread.run_finished_signal.connect(self.run_finished)
        self.decryption_thread.all_finished_signal.connect(self.all_runs_finished)
        self.decryption_thread.start()

    def update_progress(self, iteration, score, decrypted):
        total_iterations = self.iterations_input.value() * self.restarts_input.value() * self.num_runs_input.value()
        progress = int((iteration / total_iterations) * 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"Progress: {progress}% (Score: {score:.2f})")
        self.decrypted_text.setText(f"Current best decryption:\n\n{decrypted}")
        
        self.scores.append(score)
        if len(self.scores) % 10 == 0:
            self.update_chart()

    def update_chart(self):
        self.chart_canvas.axes.clear()
        self.chart_canvas.axes.plot(self.scores, color=ACCENT_COLOR, linewidth=2)
        self.chart_canvas.axes.set_xlabel('Iterations', color=TEXT_COLOR)
        self.chart_canvas.axes.set_ylabel('Score', color=TEXT_COLOR)
        self.chart_canvas.axes.set_title('Decryption Score Progress', color=TEXT_COLOR)
        self.chart_canvas.axes.tick_params(axis='x', colors=TEXT_COLOR)
        self.chart_canvas.axes.tick_params(axis='y', colors=TEXT_COLOR)
        self.chart_canvas.axes.grid(True, linestyle='--', alpha=0.2, color=SECONDARY_COLOR)
        self.chart_canvas.draw()

    def run_finished(self, decrypted, key, score):
        self.decrypted_text.append(f"\n\n--- Run completed (Score: {score:.2f}) ---\n\n{decrypted}")
        self.key_display.setText("\n".join([f"{k} -> {v}" for k, v in key.items()]))

    def all_runs_finished(self, best_decrypted, best_key, best_score):
        self.decrypted_text.setText(f"Best decryption (Score: {best_score:.2f}):\n\n{best_decrypted}")
        self.key_display.setText("\n".join([f"{k} -> {v}" for k, v in best_key.items()]))
        self.crack_button.setEnabled(True)
        self.crack_button.setText("Crack Cipher")
        self.progress_label.setText(f"Decryption complete. Best score: {best_score:.2f}")

        # Immediately change the text color to green
        self.decrypted_text.setStyleSheet(f"QTextEdit {{ color: {FINAL_TEXT_COLOR}; }}")
        self.key_display.setStyleSheet(f"QTextEdit {{ color: {FINAL_TEXT_COLOR}; }}")

        # Add a flash effect
        self.flash_text_color(self.decrypted_text)
        self.flash_text_color(self.key_display)

    def flash_text_color(self, text_widget):
        original_stylesheet = text_widget.styleSheet()
        
        def flash_once():
            text_widget.setStyleSheet(f"QTextEdit {{ color: {TEXT_COLOR}; }}")
            QApplication.processEvents()
            QThread.msleep(100)
            text_widget.setStyleSheet(original_stylesheet)
        
        QTimer.singleShot(0, flash_once)
        QTimer.singleShot(200, flash_once)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CipherApp()
    ex.show()
    sys.exit(app.exec_())