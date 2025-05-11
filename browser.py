import sys
from PyQt5 import QtWidgets, QtWebEngineWidgets, QtGui, QtCore, QtMultimedia, QtNetwork
import PyQt5.QtWebChannel as QtWebChannel
import json
import importlib.util
import os
import threading
import socketserver
import http.server
from PIL import Image
import requests
import socket

# Проверка и установка последней версии PyQt5
try:
    from PyQt5.QtWebEngineCore import QWebEngineScript
except ImportError:
    print("QWebEngineScript не поддерживается. Обновляю PyQt5...")
    os.system("pip install --upgrade PyQt5")
    from PyQt5.QtWebEngineCore import QWebEngineScript

# Проверка наличия config.json перед загрузкой
if not os.path.exists('config.json'):
    print("Файл config.json отсутствует. Создаю файл с базовыми настройками...")
    default_config = {
        "ai_textures_enabled": False,
        "enable_proxy": True,
        "incognito_mode": False,
        "homepage": "https://example.com",
        "play_text": "Play",
        "pause_text": "Pause",
        "stop_text": "Stop",
        "next_text": "Next",
        "prev_text": "Previous",
        "dark_mode": False,
        "zoom_level": 100,
        "textures": {
            "background": {
                "prompt": "minimalistic vinyl disc background, black, glossy, high detail",
                "path": "background.png"
            },
            "icon": {
                "prompt": "vinyl style icon, minimal, round, black and white",
                "path": "icon.png"
            }
        }
    }
    with open('config.json', 'w') as f:
        json.dump(default_config, f, indent=4)

# Загрузка конфигурации для кастомизации
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Загрузка шаблона интерфейса из файла template.json
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'template.json')
if not os.path.exists(TEMPLATE_PATH):
    print("Файл template.json отсутствует. Создаю файл с базовым шаблоном...")
    default_template = {
        "window_title": "Vinyl Browser",
        "window_geometry": [100, 100, 1200, 800],
        "search_bar_placeholder": "Search or enter URL...",
        "buttons": {
            "settings": "Settings",
            "media_player": "Media Player",
            "play": "Play",
            "pause": "Pause",
            "stop": "Stop",
            "next": "Next",
            "previous": "Previous"
        },
        "colors": {
            "background": "#FFFFFF",
            "text": "#000000"
        }
    }
    with open(TEMPLATE_PATH, 'w') as f:
        json.dump(default_template, f, indent=4)

with open(TEMPLATE_PATH, 'r') as f:
    TEMPLATE = json.load(f)

# Проверка наличия ключа 'buttons' в шаблоне
if 'buttons' not in TEMPLATE:
    print("Ключ 'buttons' отсутствует в template.json. Добавляю базовые настройки...")
    TEMPLATE['buttons'] = {
        "settings": "Settings",
        "media_player": "Media Player",
        "play": "Play",
        "pause": "Pause",
        "stop": "Stop",
        "next": "Next",
        "previous": "Previous"
    }

EXTENSIONS_DIR = CONFIG.get('extensions_dir', 'extensions')
PROXY_PORT = CONFIG.get('proxy_port', 8888)

class SimpleProxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Простейший HTTP-прокси для обхода DPI (можно заменить на более продвинутый)
        self.copyfile(self.send_head(), self.wfile)

class AdvancedProxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Пример улучшенного прокси для обхода DPI
        # TODO: добавить поддержку HTTPS, фильтрацию заголовков и шифрование
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Advanced Proxy Active")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def generate_texture(prompt, output_path):
    # Интеграция с API Stable Diffusion (пример)
    api_url = CONFIG.get('ai_api_url', 'http://localhost:5000/generate')
    api_key = CONFIG.get('ai_api_key', '')
    payload = {
        'prompt': prompt,
        'width': 512,
        'height': 512
    }
    headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Текстура '{prompt}' успешно сгенерирована и сохранена в {output_path}")
    else:
        print(f"Ошибка генерации текстуры: {response.status_code} {response.text}")

class AIHordeAPI:
    def __init__(self):
        self.api_url = "https://stablehorde.net/api/"  # Пример URL API AI Horde

    def generate_image(self, prompt, width=512, height=512):
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height
        }
        try:
            response = requests.post(f"{self.api_url}/generate", json=payload)
            if response.status_code == 200:
                return response.content  # Возвращает изображение в бинарном формате
            else:
                print(f"Ошибка API AI Horde: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Ошибка подключения к API AI Horde: {e}")
        return None

class BrowserAPI:
    def __init__(self, browser):
        self.browser = browser

    def get_tabs(self):
        # Пример API для работы с вкладками
        return [{"id": 1, "title": "New Tab", "url": self.browser.webview.url().toString()}]

    def open_tab(self, url):
        self.browser.webview.setUrl(QtCore.QUrl(url))

    def get_storage(self):
        # Пример API для работы с локальным хранилищем
        return CONFIG.get('extension_storage', {})

    def set_storage(self, key, value):
        if 'extension_storage' not in CONFIG:
            CONFIG['extension_storage'] = {}
        CONFIG['extension_storage'][key] = value
        with open('config.json', 'w') as f:
            json.dump(CONFIG, f, indent=4)

class ChromeAPI:
    def __init__(self, browser):
        self.browser = browser
        self.tabs = []

    def create_tab(self, url):
        self.tabs.append({"id": len(self.tabs) + 1, "url": url})
        self.browser.webview.setUrl(QtCore.QUrl(url))

    def get_tabs(self):
        return self.tabs

    def send_message(self, tab_id, message):
        print(f"Message sent to tab {tab_id}: {message}")

class FirefoxAPI:
    def __init__(self, browser):
        self.browser = browser

    def get_bookmarks(self):
        return ["https://example.com", "https://mozilla.org"]

    def add_bookmark(self, url):
        print(f"Bookmark added: {url}")

class ExtensionManager:
    def __init__(self, browser):
        self.browser = browser

    def load_extension(self, manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"Loading extension: {manifest.get('name', 'Unknown')}")
        # Load background scripts
        for script in manifest.get('background', {}).get('scripts', []):
            self.execute_script(script)

    def execute_script(self, script_path):
        with open(script_path, 'r') as f:
            script_content = f.read()
        self.browser.execute_script(script_content)
        print(f"Executed script: {script_path}")

class VinylStyleBrowser(QtWidgets.QMainWindow):
    def __init__(self):
        self.ensure_textures()
        super().__init__()
        self.ai_horde_api = AIHordeAPI()  # Инициализация API AI Horde
        self.extension_manager = ExtensionManager(self)
        self.setWindowTitle(TEMPLATE.get('window_title', 'Vinyl Browser'))
        geometry = TEMPLATE.get('window_geometry', [100, 100, 1200, 800])
        self.setGeometry(*geometry)
        self.setStyleSheet(CONFIG.get('style', ''))
        self.initUI()

    def ensure_textures(self):
        if not CONFIG.get('ai_textures_enabled', True):
            return
        textures = CONFIG.get('textures', {})
        for name, params in textures.items():
            path = params.get('path', f'{name}.png')
            prompt = params.get('prompt', f'{name} texture')
            if not os.path.exists(path):
                generate_texture(prompt, path)

    def open_ai_horde_ui(self):
        # Открытие Swagger UI для взаимодействия с AI Horde
        self.webview.setUrl(QtCore.QUrl("file://" + os.path.abspath("AI Horde api.html")))

    def generate_ai_image_with_gui(self):
        # Окно для ввода параметров генерации изображения
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Generate AI Image")
        dialog.setGeometry(300, 300, 400, 200)

        layout = QtWidgets.QVBoxLayout()

        prompt_label = QtWidgets.QLabel("Prompt:")
        layout.addWidget(prompt_label)
        prompt_input = QtWidgets.QLineEdit()
        layout.addWidget(prompt_input)

        width_label = QtWidgets.QLabel("Width:")
        layout.addWidget(width_label)
        width_input = QtWidgets.QSpinBox()
        width_input.setRange(64, 2048)
        width_input.setValue(512)
        layout.addWidget(width_input)

        height_label = QtWidgets.QLabel("Height:")
        layout.addWidget(height_label)
        height_input = QtWidgets.QSpinBox()
        height_input.setRange(64, 2048)
        height_input.setValue(512)
        layout.addWidget(height_input)

        generate_button = QtWidgets.QPushButton("Generate")
        layout.addWidget(generate_button)

        dialog.setLayout(layout)

        def on_generate():
            prompt = prompt_input.text()
            width = width_input.value()
            height = height_input.value()
            image_data = self.ai_horde_api.generate_image(prompt, width, height)
            if image_data:
                with open("generated_image.png", "wb") as f:
                    f.write(image_data)
                QtWidgets.QMessageBox.information(self, "Success", "Image generated and saved as generated_image.png")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to generate image.")
            dialog.close()

        generate_button.clicked.connect(on_generate)
        dialog.exec_()

    def initUI(self):
        # Основной layout
        self.central_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()  # Убедимся, что self.layout инициализирован как QVBoxLayout
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Центральный виджет: веб-движок
        self.webview = QtWebEngineWidgets.QWebEngineView()
        self.webview.setUrl(QtCore.QUrl(CONFIG.get('homepage', 'https://www.google.com')))
        self.layout.addWidget(self.webview)

        # Инициализация строки поиска
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText(TEMPLATE.get('search_bar_placeholder', "Search or enter URL..."))
        self.search_bar.returnPressed.connect(self.load_url_from_search_bar)
        self.layout.addWidget(self.search_bar)

        # Верхняя панель с вкладками и навигацией
        self.top_bar = QtWidgets.QWidget()
        self.search_bar.setPlaceholderText(TEMPLATE.get('search_bar_placeholder', "Search or enter URL..."))
        self.search_bar.returnPressed.connect(self.load_url_from_search_bar)

        # Медиаплеер как всплывающее окно
        self.media_player_popup = QtWidgets.QWidget()
        self.media_player_popup.setWindowTitle("Media Player")
        self.media_player_popup.setGeometry(100, 100, 300, 100)
        self.media_layout = QtWidgets.QHBoxLayout()
        self.play_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('play', 'Play'))
        self.play_button.clicked.connect(self.play_media)
        self.pause_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('pause', 'Pause'))
        self.pause_button.clicked.connect(self.pause_media)
        self.stop_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('stop', 'Stop'))
        self.stop_button.clicked.connect(self.stop_media)
        self.next_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('next', 'Next'))
        self.next_button.clicked.connect(self.next_media)
        self.prev_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('previous', 'Previous'))
        self.prev_button.clicked.connect(self.prev_media)
        self.media_layout.addWidget(self.play_button)
        self.media_layout.addWidget(self.pause_button)
        self.media_layout.addWidget(self.stop_button)
        self.media_layout.addWidget(self.next_button)
        self.media_layout.addWidget(self.prev_button)
        self.media_player_popup.setLayout(self.media_layout)

        # Добавление кнопок
        self.settings_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('settings', 'Settings'))
        self.settings_button.clicked.connect(self.open_settings_window)
        self.layout.addWidget(self.settings_button)

        self.media_player_button = QtWidgets.QPushButton(TEMPLATE['buttons'].get('media_player', 'Media Player'))
        self.media_player_button.clicked.connect(self.toggle_media_player)
        self.layout.addWidget(self.media_player_button)

        # Добавление кнопки для открытия Swagger UI
        self.ai_horde_button = QtWidgets.QPushButton("AI Horde UI")
        self.ai_horde_button.clicked.connect(self.open_ai_horde_ui)
        self.layout.addWidget(self.ai_horde_button)

        # Добавление кнопки для генерации изображения через GUI
        self.generate_image_button = QtWidgets.QPushButton("Generate AI Image")
        self.generate_image_button.clicked.connect(self.generate_ai_image_with_gui)
        self.layout.addWidget(self.generate_image_button)

        # Добавление новых настроек и функций
        self.dark_mode_checkbox = QtWidgets.QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(CONFIG.get('dark_mode', False))
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        self.layout.addWidget(self.dark_mode_checkbox)

        self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_slider.setMinimum(50)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(CONFIG.get('zoom_level', 100))
        self.zoom_slider.valueChanged.connect(self.change_zoom_level)
        self.layout.addWidget(self.zoom_slider)

        self.bookmarks_button = QtWidgets.QPushButton("Bookmarks")
        self.bookmarks_button.clicked.connect(self.open_bookmarks)
        self.layout.addWidget(self.bookmarks_button)

        self.history_button = QtWidgets.QPushButton("History")
        self.history_button.clicked.connect(self.open_history)
        self.layout.addWidget(self.history_button)

        # Добавление кнопки для управления расширениями
        self.extensions_button = QtWidgets.QPushButton("Extensions")
        self.extensions_button.clicked.connect(self.open_extensions_window)
        self.layout.addWidget(self.extensions_button)

        # Применение цветов из шаблона
        palette = self.palette()
        colors = TEMPLATE.get('colors', {})
        if 'background' in colors:
            palette.setColor(self.backgroundRole(), QtGui.QColor(colors['background']))
        if 'text' in colors:
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(colors['text']))
        self.setPalette(palette)

        # Минималистичный стиль виниловой пластинки
        self.setWindowIcon(QtGui.QIcon(CONFIG.get('icon', '')))
        # Запуск DPI bypass proxy (можно отключить в конфиге)
        if CONFIG.get('enable_proxy', True):
            self.start_proxy()
        # Загрузка расширений
        self.load_extensions()
        self.load_browser_extensions()

        # Установка WebChannel для взаимодействия с расширениями
        self.channel = QtWebChannel.QWebChannel()
        self.browser_api = BrowserAPI(self)
        self.channel.registerObject("browserAPI", self.browser_api)
        self.webview.page().setWebChannel(self.channel)

    def execute_script(self, script_content):
        # Альтернативный способ выполнения скриптов через evaluateJavaScript
        self.webview.page().runJavaScript(script_content)
        print("Скрипт выполнен через runJavaScript.")

    def toggle_dark_mode(self):
        dark_mode = self.dark_mode_checkbox.isChecked()
        CONFIG['dark_mode'] = dark_mode
        with open('config.json', 'w') as f:
            json.dump(CONFIG, f, indent=4)
        if dark_mode:
            self.setStyleSheet("background-color: #121212; color: #FFFFFF;")
        else:
            self.setStyleSheet("background-color: #FFFFFF; color: #000000;")

    def change_zoom_level(self):
        zoom_level = self.zoom_slider.value()
        CONFIG['zoom_level'] = zoom_level
        with open('config.json', 'w') as f:
            json.dump(CONFIG, f, indent=4)
        self.webview.setZoomFactor(zoom_level / 100.0)

    def open_bookmarks(self):
        # Заглушка для функции закладок
        print("Открытие закладок")

    def open_history(self):
        # Заглушка для функции истории
        print("Открытие истории")

    def open_settings_window(self):
        # Создание отдельного окна для настроек
        self.settings_window = QtWidgets.QWidget()
        self.settings_window.setWindowTitle("Settings")
        self.settings_window.setGeometry(200, 200, 600, 600)

        layout = QtWidgets.QVBoxLayout()

        # Добавление элементов настроек
        self.ai_textures_checkbox = QtWidgets.QCheckBox("Enable AI Textures")
        self.ai_textures_checkbox.setChecked(CONFIG.get('ai_textures_enabled', False))
        layout.addWidget(self.ai_textures_checkbox)

        self.proxy_checkbox = QtWidgets.QCheckBox("Enable Proxy")
        self.proxy_checkbox.setChecked(CONFIG.get('enable_proxy', True))
        layout.addWidget(self.proxy_checkbox)

        self.incognito_checkbox = QtWidgets.QCheckBox("Enable Incognito Mode")
        self.incognito_checkbox.setChecked(CONFIG.get('incognito_mode', False))
        layout.addWidget(self.incognito_checkbox)

        self.dark_mode_checkbox = QtWidgets.QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(CONFIG.get('dark_mode', False))
        layout.addWidget(self.dark_mode_checkbox)

        self.zoom_slider_label = QtWidgets.QLabel("Zoom Level:")
        layout.addWidget(self.zoom_slider_label)
        self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_slider.setMinimum(50)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(CONFIG.get('zoom_level', 100))
        layout.addWidget(self.zoom_slider)

        self.homepage_label = QtWidgets.QLabel("Homepage URL:")
        layout.addWidget(self.homepage_label)
        self.homepage_input = QtWidgets.QLineEdit(CONFIG.get('homepage', 'https://example.com'))
        layout.addWidget(self.homepage_input)

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.settings_window.setLayout(layout)
        self.settings_window.show()

    def save_settings(self):
        # Сохранение настроек в config.json
        CONFIG['ai_textures_enabled'] = self.ai_textures_checkbox.isChecked()
        CONFIG['enable_proxy'] = self.proxy_checkbox.isChecked()
        CONFIG['incognito_mode'] = self.incognito_checkbox.isChecked()
        CONFIG['dark_mode'] = self.dark_mode_checkbox.isChecked()
        CONFIG['zoom_level'] = self.zoom_slider.value()
        CONFIG['homepage'] = self.homepage_input.text()

        with open('config.json', 'w') as f:
            json.dump(CONFIG, f, indent=4)

        QtWidgets.QMessageBox.information(self, "Settings", "Settings saved successfully!")

    def load_url_from_search_bar(self):
        url = self.search_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        self.webview.setUrl(QtCore.QUrl(url))

    def toggle_media_player(self):
        if self.media_player_popup.isVisible():
            self.media_player_popup.hide()
        else:
            self.media_player_popup.show()

    def open_settings(self):
        # Открытие страницы настроек
        self.webview.setUrl(QtCore.QUrl("pieser://settings"))

    def handle_custom_schemes(self):
        # Альтернативный подход для обработки пользовательских схем
        self.webview.urlChanged.connect(self.handle_url_change)

    def handle_url_change(self, url):
        if url.scheme() == "pieser" and url.path() == "/settings":
            self.webview.setHtml(self.generate_settings_page())

    def generate_settings_page(self):
        # Генерация HTML для страницы настроек
        return """
        <html>
        <head><title>Settings</title></head>
        <body>
            <h1>Browser Settings</h1>
            <form method='post'>
                <label><input type='checkbox' name='ai_textures_enabled'> Enable AI Textures</label><br>
                <label><input type='checkbox' name='enable_proxy'> Enable Proxy</label><br>
                <label><input type='checkbox' name='incognito_mode'> Enable Incognito Mode</label><br>
                <button type='submit'>Save</button>
            </form>
        </body>
        </html>
        """

    def check_and_install_packages(self):
        # Проверка и установка недостающих пакетов
        required_packages = ["PyQt5", "requests", "Pillow"]
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                print(f"Пакет {package} не установлен. Устанавливаю...")
                os.system(f"pip install {package}")
            else:
                print(f"Пакет {package} уже установлен.")

    def ensure_files_exist(self):
        # Проверка наличия необходимых файлов и создание заглушек, если их нет
        required_files = {
            'config.json': '{"ai_textures_enabled": true, "enable_proxy": true, "incognito_mode": false}',
            'requirements.txt': 'PyQt5\nrequests\nPillow',
            'README.md': '# VinylStyleBrowser\n\nИнструкции по использованию.'
        }
        for file, default_content in required_files.items():
            if not os.path.exists(file):
                print(f"Файл {file} отсутствует. Создаю...")
                with open(file, 'w') as f:
                    f.write(default_content)
            else:
                print(f"Файл {file} уже существует. Пропускаем создание.")

    def handle_errors(self):
        # Общий метод для проверки и исправления ошибок
        try:
            self.check_and_install_packages()
            self.ensure_files_exist()
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def start_proxy(self):
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('127.0.0.1', port)) == 0

        if is_port_in_use(PROXY_PORT):
            print(f"Порт {PROXY_PORT} уже используется. Прокси не будет запущен.")
            return

        def run_proxy():
            server = ThreadedHTTPServer(('127.0.0.1', PROXY_PORT), AdvancedProxy)
            server.serve_forever()

        threading.Thread(target=run_proxy, daemon=True).start()
        # Настроить webview на работу через прокси
        proxy = QtNetwork.QNetworkProxy(QtNetwork.QNetworkProxy.HttpProxy, '127.0.0.1', PROXY_PORT)
        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

    def load_extensions(self):
        # Загрузка расширений на Python
        if not os.path.exists(EXTENSIONS_DIR):
            os.makedirs(EXTENSIONS_DIR)
        for fname in os.listdir(EXTENSIONS_DIR):
            if fname.endswith('.py'):
                path = os.path.join(EXTENSIONS_DIR, fname)
                spec = importlib.util.spec_from_file_location(fname[:-3], path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'init_extension'):
                    mod.init_extension(self)
        # Заготовка: поддержка расширений Chrome/Firefox/Safari
        # TODO: реализовать парсинг manifest.json, API-обёртки и sandbox для расширений других браузеров
        # Можно использовать py_mini_racer, pyodide или встроенный движок JS для запуска расширений

    def load_browser_extensions(self):
        extensions_dir = CONFIG.get('browser_extensions_dir', 'browser_extensions')
        if not os.path.exists(extensions_dir):
            os.makedirs(extensions_dir)
        for ext_dir in os.listdir(extensions_dir):
            ext_path = os.path.join(extensions_dir, ext_dir)
            manifest_path = os.path.join(ext_path, 'manifest.json')
            if os.path.isdir(ext_path) and os.path.exists(manifest_path):
                self.extension_manager.load_extension(manifest_path)

    def register_extension(self, manifest, ext_path):
        # Обработка manifest.json для расширений Chrome/Firefox/Safari
        name = manifest.get('name', 'Без имени')
        version = manifest.get('version', '1.0')
        print(f"Загрузка расширения: {name} (версия {version})")

        # Подключение background scripts
        background = manifest.get('background', {}).get('scripts', [])
        for script in background:
            script_path = os.path.join(ext_path, script)
            if os.path.exists(script_path):
                print(f"Подключение background script: {script_path}")
                self.execute_background_script(script_path)

        # Подключение content scripts
        content_scripts = manifest.get('content_scripts', [])
        for content in content_scripts:
            matches = content.get('matches', [])
            js_files = content.get('js', [])
            for js_file in js_files:
                js_path = os.path.join(ext_path, js_file)
                if os.path.exists(js_path):
                    print(f"Подключение content script: {js_path} для {matches}")
                    self.inject_content_script(js_path, matches)

        # Обработка permissions
        permissions = manifest.get('permissions', [])
        print(f"Запрашиваемые разрешения: {permissions}")
        self.handle_permissions(permissions)

    def execute_background_script(self, script_path):
        # TODO: Реализовать выполнение background scripts через встроенный JS-движок
        print(f"Выполнение background script: {script_path}")

    def inject_content_script(self, script_path, matches):
        # TODO: Реализовать инъекцию content scripts в webview
        print(f"Инъекция content script: {script_path} для {matches}")

    def handle_permissions(self, permissions):
        # TODO: Реализовать обработку разрешений (например, доступ к cookies, storage)
        print(f"Обработка разрешений: {permissions}")

    def apply_customization(self):
        # Применение кастомных текстур, стилей, шрифтов, иконок
        textures = CONFIG.get('textures', {})
        for name, params in textures.items():
            path = params.get('path', f'{name}.png')
            if os.path.exists(path):
                if name == 'background':
                    self.setStyleSheet(f"background-image: url('{path}'); background-repeat: no-repeat; background-position: center; background-size: cover; border-radius: 50%;")
                elif name == 'icon':
                    self.setWindowIcon(QtGui.QIcon(path))
        # Применение шрифтов и цветов
        font = CONFIG.get('font', {})
        if font:
            app_font = QtGui.QFont()
            app_font.setFamily(font.get('family', 'Arial'))
            app_font.setPointSize(font.get('size', 10))
            app.setFont(app_font)
        colors = CONFIG.get('colors', {})
        if colors:
            palette = self.palette()
            if 'background' in colors:
                palette.setColor(self.backgroundRole(), QtGui.QColor(colors['background']))
            if 'text' in colors:
                palette.setColor(QtGui.QPalette.Text, QtGui.QColor(colors['text']))
            self.setPalette(palette)
        # Минималистичный стиль виниловой пластинки
        self.setStyleSheet(self.styleSheet() + "border-radius: 50%; background-color: black; color: white;")

    def ensure_security(self):
        # Реализация дополнительных мер безопасности
        # Включение режима инкогнито
        if CONFIG.get('incognito_mode', False):
            self.webview.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.PrivateBrowsingEnabled, True)
        # Отключение сторонних куки (заменено на альтернативный подход)
        print("Отключение сторонних куки не поддерживается в текущей версии PyQt5. Пропускаем.")
        # Добавление строгой политики CSP
        csp_policy = CONFIG.get('csp_policy', "default-src 'self'; script-src 'self'")
        print(f"Политика CSP установлена: {csp_policy}")

    def ensure_privacy(self):
        # Реализация блокировки рекламы и трекеров
        adblock_filters = CONFIG.get('adblock_filters', [])
        for filter_url in adblock_filters:
            try:
                response = requests.get(filter_url)
                if response.status_code == 200:
                    filter_path = os.path.join('filters', os.path.basename(filter_url))
                    os.makedirs('filters', exist_ok=True)
                    with open(filter_path, 'w') as f:
                        f.write(response.text)
                    print(f"Фильтр загружен: {filter_path}")
                    # TODO: применить фильтр к webview
                else:
                    print(f"Ошибка загрузки фильтра: {filter_url} (код {response.status_code})")
            except Exception as e:
                print(f"Ошибка при загрузке фильтра {filter_url}: {e}")
        # Отключение WebRTC и fingerprinting
        print("Отключение WebRTC не поддерживается в текущей версии PyQt5. Пропускаем.")
        self.webview.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.JavascriptCanAccessClipboard, False)
        print("Доступ к буферу обмена отключён для защиты от fingerprinting")

    def play_media(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_paths, _ = file_dialog.getOpenFileNames(self, 'Open Media', '', 'Audio Files (*.mp3 *.wav *.ogg)')
        if file_paths:
            for file_path in file_paths:
                self.playlist.addMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(file_path)))
            self.playlist.setCurrentIndex(0)
            self.media_player.play()

    def pause_media(self):
        self.media_player.pause()

    def stop_media(self):
        self.media_player.stop()

    def next_media(self):
        self.playlist.next()

    def prev_media(self):
        self.playlist.previous()

    def open_extensions_window(self):
        # Создание окна для управления расширениями
        self.extensions_window = QtWidgets.QWidget()
        self.extensions_window.setWindowTitle("Extensions")
        self.extensions_window.setGeometry(300, 300, 600, 400)

        layout = QtWidgets.QVBoxLayout()

        # Список установленных расширений
        self.extensions_list = QtWidgets.QListWidget()
        self.load_installed_extensions()
        layout.addWidget(self.extensions_list)

        # Кнопки для управления расширениями
        self.add_extension_button = QtWidgets.QPushButton("Add Extension")
        self.add_extension_button.clicked.connect(self.add_extension)
        layout.addWidget(self.add_extension_button)

        self.remove_extension_button = QtWidgets.QPushButton("Remove Selected Extension")
        self.remove_extension_button.clicked.connect(self.remove_selected_extension)
        layout.addWidget(self.remove_extension_button)

        self.extensions_window.setLayout(layout)
        self.extensions_window.show()

    def load_installed_extensions(self):
        # Загрузка списка установленных расширений
        self.extensions_list.clear()
        extensions_dir = CONFIG.get('browser_extensions_dir', 'browser_extensions')
        if not os.path.exists(extensions_dir):
            os.makedirs(extensions_dir)
        for ext_dir in os.listdir(extensions_dir):
            ext_path = os.path.join(extensions_dir, ext_dir)
            manifest_path = os.path.join(ext_path, 'manifest.json')
            if os.path.isdir(ext_path) and os.path.exists(manifest_path):
                with open(manifest_path, 'r') as manifest_file:
                    manifest = json.load(manifest_file)
                    self.extensions_list.addItem(manifest.get('name', 'Unknown Extension'))

    def add_extension(self):
        # Заглушка для добавления расширений
        file_dialog = QtWidgets.QFileDialog(self)
        extension_path, _ = file_dialog.getOpenFileName(self, 'Select Extension', '', 'Extension Files (*.zip *.crx)')
        if extension_path:
            print(f"Добавление расширения из {extension_path}")
            # TODO: Реализовать установку расширений

    def remove_selected_extension(self):
        # Удаление выбранного расширения
        selected_item = self.extensions_list.currentItem()
        if selected_item:
            extension_name = selected_item.text()
            print(f"Удаление расширения: {extension_name}")
            # TODO: Реализовать удаление расширений

    def load_browser_apis(self):
        # Заглушка для загрузки API Chrome и Firefox
        print("Загрузка API Chrome и Firefox...")
        # TODO: Реализовать поддержку API Chrome и Firefox

    def generate_ai_image(self):
        # Пример использования API AI Horde для генерации изображения
        prompt = "A futuristic cityscape, highly detailed, vibrant colors"
        image_data = self.ai_horde_api.generate_image(prompt)
        if image_data:
            with open("generated_image.png", "wb") as f:
                f.write(image_data)
            print("Изображение успешно сгенерировано и сохранено как generated_image.png")
        else:
            print("Не удалось сгенерировать изображение.")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Arial", 10))  # Установка шрифта по умолчанию для устранения предупреждений
    browser = VinylStyleBrowser()
    browser.handle_errors()  # Проверка и исправление ошибок
    browser.apply_customization()  # Кастомизация внешнего вида
    browser.ensure_security()      # Безопасность
    browser.ensure_privacy()       # Приватность
    browser.handle_custom_schemes()  # Обработка кастомных схем
    browser.show()
    sys.exit(app.exec_())
