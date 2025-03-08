import sys
import json
import time
import argparse
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QTextEdit, QPushButton, QSplitter, QSizePolicy
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt, QSize

from scripts.lib import ImageGenerator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stability API GUI")

        self.generator = ImageGenerator()

        # Load specifications from JSON file
        with open("info/specification.json", "r") as file:
            self.specifications = json.load(file)

        self.main_widget = QWidget(self)
        self.main_layout = QGridLayout(self.main_widget)

        # Set main_widget to change dynamically in size
        self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set minimum size to 500x500
        self.main_widget.setMinimumSize(500, 500)

        # Set application logo
        self.setWindowIcon(QIcon("data/logo.png"))

        # Create left and right layouts
        self.left_layout = LeftLayout(self.specifications, self.generator, self.main_widget)
        self.right_layout = RightLayout(self.generator, self.main_widget)

        # Create a splitter and add left and right layouts
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_layout)
        splitter.addWidget(self.right_layout)
        splitter.setSizes([400, 600])

        # Add the splitter to the main layout
        self.main_layout.addWidget(splitter, 0, 0)

        # Set main widget as central widget
        self.setCentralWidget(self.main_widget)

        # Set initial size of window
        self.resize(1000, 550)
        
        # Update image sizes time variable
        self.updatetime = 0
        
        # Readjust the size of the Right Layout's image
        self.resizeEvent(None, first=True)
        
        # Set the main Window in the Right Layout
        self.right_layout.set_main_window(self)


    def clicked_generate(self):
        print("Generate button clicked")
        
        # Retrieve and Set Values
        self.retrieve_values()

    def clicked_left(self):
        print("Left button clicked")
        
        # Look at current image index, if it's not 0, decrement it
        if self.generator.current_image_idx > 0:
            self.generator.current_image_idx -= 1
            self.generator.current_image = self.generator.image_list[self.generator.current_image_idx]
        # If it is 0, set it to the last image in the list
        else:
            self.generator.current_image_idx = len(self.generator.image_list) - 1
            self.generator.current_image = self.generator.image_list[self.generator.current_image_idx]
            
        # Update
        self.update_image_sizes()

    def clicked_right(self):
        print("Right button clicked")
        
        # Look at current image index, if it's not the last image, increment it
        if self.generator.current_image_idx < len(self.generator.image_list) - 1:
            self.generator.current_image_idx += 1
            self.generator.current_image = self.generator.image_list[self.generator.current_image_idx]
        # If it is the last image, set it to the first image in the list
        else:
            self.generator.current_image_idx = 0
            self.generator.current_image = self.generator.image_list[self.generator.current_image_idx]
        
        # Update
        self.update_image_sizes()

    def retrieve_values(self):
        api_key = self.left_layout.api_key_textbox.text()
        model = self.left_layout.model_dropdown.currentText()
        aspect = self.left_layout.aspect_dropdown.currentText()
        seed = self.left_layout.seed_textbox.text()
        use_random_seed = self.left_layout.random_seed_checkbox.isChecked()
        prompt = self.left_layout.prompt_textbox.toPlainText()
        negative_prompt = self.left_layout.negative_prompt_textbox.toPlainText()
        steps = self.left_layout.steps_textbox.text()
        cfg = self.left_layout.cfg_textbox.text()
        samples = self.left_layout.samples_textbox.text()
        use_perplexity = self.left_layout.perplexity_checkbox.isChecked()
        
        # Set the values
        self.generator.set_values(api_key, model, aspect, seed, use_random_seed, prompt, negative_prompt, steps, cfg, samples, use_perplexity)
    
        # Generate an image based on the values
        self.generator.generate_image()
        
        # Update Image
        self.update_image_sizes()
        
        # If use_random_seed is checked, update the seed_textbox with the new seed
        if use_random_seed:
            self.left_layout.seed_textbox.setText(str(self.generator.seed))
        
        # If use_perplexity is checked, update the prompt_textbox with the new prompt
        if use_perplexity:
            self.left_layout.prompt_textbox.setText(self.generator.prompt)

    def resizeEvent(self, event, first=False):
        super().resizeEvent(event)
        
        # Get current time
        current_time = time.time()
        
        # Check to see if 0.1 seconds have passed since last update. If so, update image sizes.
        if current_time - self.updatetime > 0.01:
            self.updatetime = current_time
            self.update_image_sizes()
        elif first:
            self.update_image_sizes()

    def update_image_sizes(self):
        placeholder_pixmap = QPixmap(self.generator.current_image)
        placeholder_pixmap = placeholder_pixmap.scaled(self.right_layout.size() - QSize(70, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.right_layout.placeholder_image.setPixmap(placeholder_pixmap)
        
        # Update the button heights to match
        self.right_layout.left_button.setFixedHeight(self.right_layout.placeholder_image.height())
        self.right_layout.right_button.setFixedHeight(self.right_layout.placeholder_image.height())


class LeftLayout(QWidget):
    def __init__(self, specifications, generator, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        
        self.main_window = None
        self.right_layout = None

        # First row: Title
        self.title_label = QLabel("Stability API GUI")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 16))
        self.layout.addWidget(self.title_label, 0, 0, 1, 4)

        # Second row: API Key
        self.api_key_label = QLabel("API Key:")
        self.api_key_label.setAlignment(Qt.AlignRight)
        self.api_key_textbox = QLineEdit(str(generator.api_key))
        self.layout.addWidget(self.api_key_label, 1, 0)
        self.layout.addWidget(self.api_key_textbox, 1, 1, 1, 3)

        # Third row: Model
        self.model_label = QLabel("Model:")
        self.model_label.setAlignment(Qt.AlignRight)
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(specifications["models"])
        self.layout.addWidget(self.model_label, 2, 0)
        self.layout.addWidget(self.model_dropdown, 2, 1, 1, 3)

        # Fifth row: Aspect
        self.aspect_label = QLabel("Aspect:")
        self.aspect_label.setAlignment(Qt.AlignRight)
        self.aspect_dropdown = QComboBox()
        self.aspect_dropdown.addItems(specifications["aspects"])
        self.layout.addWidget(self.aspect_label, 3, 0)
        self.layout.addWidget(self.aspect_dropdown, 3, 1, 1, 3)

        # Fourth row: Seed
        self.seed_label = QLabel("Seed:")
        self.seed_label.setAlignment(Qt.AlignRight)
        self.seed_textbox = QLineEdit("0")
        self.random_seed_checkbox = QCheckBox("Random Seed")
        self.random_seed_checkbox.setChecked(True)
        self.layout.addWidget(self.seed_label, 4, 0)
        self.layout.addWidget(self.seed_textbox, 4, 1)
        self.layout.addWidget(self.random_seed_checkbox, 4, 2, 1, 2)

        # Sixth row: Prompt
        self.prompt_label = QLabel("Prompt")
        self.prompt_label.setAlignment(Qt.AlignLeft)
        self.prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.prompt_label.setStyleSheet("text-decoration: underline;")
        self.layout.addWidget(self.prompt_label, 5, 0, 1, 4)

        # Seventh row: Prompt textbox
        self.prompt_textbox = QTextEdit()
        self.prompt_textbox.setPlaceholderText("Insert prompt here")
        self.layout.addWidget(self.prompt_textbox, 6, 0, 1, 4)

        # Eighth row: Negative Prompt
        self.negative_prompt_label = QLabel("Negative Prompt")
        self.negative_prompt_label.setAlignment(Qt.AlignLeft)
        self.negative_prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.negative_prompt_label.setStyleSheet("text-decoration: underline;")
        self.layout.addWidget(self.negative_prompt_label, 7, 0, 1, 4)

        # Ninth row: Negative Prompt textbox
        self.negative_prompt_textbox = QTextEdit()
        self.negative_prompt_textbox.setPlaceholderText("Insert negative prompt here")
        self.layout.addWidget(self.negative_prompt_textbox, 8, 0, 1, 4)

        # Tenth row: Steps and CFG
        self.steps_label = QLabel("Steps:")
        self.steps_label.setAlignment(Qt.AlignRight)
        self.steps_textbox = QLineEdit("30")
        self.cfg_label = QLabel("CFG:")
        self.cfg_label.setAlignment(Qt.AlignRight)
        self.cfg_textbox = QLineEdit("7")
        self.layout.addWidget(self.steps_label, 9, 0)
        self.layout.addWidget(self.steps_textbox, 9, 1)
        self.layout.addWidget(self.cfg_label, 9, 2)
        self.layout.addWidget(self.cfg_textbox, 9, 3)

        # Eleventh row: Samples and Perplexity
        self.samples_label = QLabel("Samples:")
        self.samples_label.setAlignment(Qt.AlignRight)
        self.samples_textbox = QLineEdit("1")
        self.perplexity_checkbox = QCheckBox("Perplexity")
        self.layout.addWidget(self.samples_label, 10, 0)
        self.layout.addWidget(self.samples_textbox, 10, 1)
        self.layout.addWidget(self.perplexity_checkbox, 10, 2, 1, 2)

        # Twelfth row: Generate button
        self.generate_button = QPushButton("Generate")
        self.layout.addWidget(self.generate_button, 11, 0, 1, 4)

        # Generate Button Click Event
        self.generate_button.clicked.connect(self.clicked_generate)

        self.generator = generator
    
    def set_right_layout(self, right_layout):
        self.right_layout = right_layout

    def clicked_generate(self):
        # Get All of the Following Values:
        # api_key, model, aspect, seed, use_random_seed, prompt, negative_prompt, steps, cfg, samples, use_perplexity
        api_key = self.api_key_textbox.text()
        model = self.model_dropdown.currentText()
        aspect = self.aspect_dropdown.currentText()
        seed = self.seed_textbox.text()
        use_random_seed = self.random_seed_checkbox.isChecked()
        prompt = self.prompt_textbox.toPlainText()
        negative_prompt = self.negative_prompt_textbox.toPlainText()
        steps = self.steps_textbox.text()
        cfg = self.cfg_textbox.text()
        samples = self.samples_textbox.text()
        use_perplexity = self.perplexity_checkbox.isChecked()
        
        # Set the values in Generator.set_values
        self.generator.set_values(api_key, model, aspect, seed, use_random_seed, prompt, negative_prompt, steps, cfg, samples, use_perplexity)
        
        print("Generate button clicked")
        self.generator.generate_image()
        
        # Update the image sizes
        self.main_window.update_image_sizes()
    
    def set_main_window(self, main_window):
        self.main_window = main_window


class RightLayout(QWidget):
    def __init__(self, generator, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)

        # Add placeholder image to top right
        self.placeholder_image = QLabel()
        self.placeholder_pixmap = QPixmap(generator.current_image)
        self.placeholder_pixmap = self.placeholder_pixmap.scaled(self.size() - QSize(70, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.placeholder_image.setPixmap(self.placeholder_pixmap)

        # Add buttons to the top right layout
        self.left_button = QPushButton("<")
        self.left_button.setFixedHeight(self.placeholder_image.height())
        self.left_button.setFixedWidth(25)
        self.left_button.clicked.connect(self.clicked_left)

        self.right_button = QPushButton(">")
        self.right_button.setFixedHeight(self.placeholder_image.height())
        self.right_button.setFixedWidth(25)
        self.right_button.clicked.connect(self.clicked_right)

        self.layout.addWidget(self.left_button, 0, 0, alignment=Qt.AlignRight)
        self.layout.addWidget(self.placeholder_image, 0, 1, Qt.AlignCenter)
        self.layout.addWidget(self.right_button, 0, 2, alignment=Qt.AlignLeft)

        self.generator = generator
        self.main_window = None
        self.left_side = None
    
    def set_left_side(self, left_side):
        self.left_side = left_side

    def set_main_window(self, main_window):
        self.main_window = main_window

    def clicked_left(self):
        print("Left button clicked")
        self.generator.current_image_idx -= 1
        if self.generator.current_image_idx < 0:
            self.generator.current_image_idx = len(self.generator.image_list) - 1
        self.generator.current_image = self.generator.image_list[self.generator.current_image_idx]
        self.main_window.update_image_sizes()

    def clicked_right(self):
        print("Right button clicked")
        self.generator.current_image_idx += 1
        if self.generator.current_image_idx >= len(self.generator.image_list):
            self.generator.current_image_idx = 0
        self.generator.current_image = self.generator.image_list[self.generator.current_image_idx]
        self.main_window.update_image_sizes()

class ArgsParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--debug", default=False, action="store_true")

    def parse(self):
        return self.parser.parse_args()


if __name__ == "__main__":
    args = ArgsParser().parse()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.resizeEvent(None, first=True)
    window.left_layout.set_main_window(window)
    window.left_layout.set_right_layout(window.right_layout)
    window.right_layout.set_main_window(window)
    window.right_layout.set_left_side(window.left_layout)
    sys.exit(app.exec())
