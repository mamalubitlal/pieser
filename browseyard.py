import subprocess
import sys

def install_packages():
    try:
        import PyQt5
    except ImportError:
        print("PyQt5 not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])

install_packages()

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class BarebonesBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Barebones Browser")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a vertical layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create the web view
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://mamalubitlal.github.io/pynguin/"))
        layout.addWidget(self.web_view)

        # Create the reload button
        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.reload_page)
        layout.addWidget(reload_button)

    def reload_page(self):
        self.web_view.reload()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = BarebonesBrowser()
    browser.show()
    sys.exit(app.exec_())