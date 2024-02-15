from PyQt6.QtWidgets import (QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QHBoxLayout)

class RightUI(QWidget):
    
    content_size = None
    
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()
        self.main_window = main_window
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.top_layout = QHBoxLayout()
        
        self.top_layout.addWidget(QLabel("UI for diagrams"))
        
        self.top_layout.addStretch()
        
        # button to close the right ui
        self.close_button = QPushButton("X")
        self.close_button.clicked.connect(self.hide_ui)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("background-color: red; color: white; border: none;")
        self.top_layout.addWidget(self.close_button)
        
        self.layout.addLayout(self.top_layout)
        
        # add spacer
        self.layout.addStretch()
        
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if self.width() == 0:
            self.main_window.open_right_ui_button.show()
        else:
            self.main_window.open_right_ui_button.hide()
            
    def hide_ui(self):
        self.content_size = self.width()
        size = self.main_window.splitter.sizes()
        self.main_window.splitter.setSizes([size[0]+self.content_size//2, 
                                            size[1]+self.content_size//2, 
                                            0])
        
        self.hide()
        self.main_window.open_right_ui_button.show()
        
    def show_ui(self):
        self.show()
        self.main_window.open_right_ui_button.hide()
        
        # resize layout
        size = self.main_window.splitter.sizes()
        if self.content_size is None:
            self.content_size = self.layout.sizeHint().width()
        self.main_window.splitter.setSizes([size[0]-self.content_size//2, size[1]-self.content_size//2, self.content_size])