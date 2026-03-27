import sys
import os
import json
import storage
import keyboard
import subprocess
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QPushButton,
    QLineEdit, QTabBar, QStackedWidget,
    QLabel, QInputDialog, QMessageBox,
    QDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon


app = QApplication(sys.argv)
view = QWebEngineView()

settings = view.settings()
settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

profile = QWebEngineProfile.defaultProfile()
profile.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

window = QMainWindow()
window.setWindowTitle("Scribble Browser")
window.setWindowIcon(QIcon('images/player.png'))
window.setMinimumSize(1200, 750)
window.resize(1400, 900)

window.setStyleSheet("""
    QMainWindow {
        background-color: #0d0d0f;
    }
    QScrollBar:vertical {
        background: #0d0d0f;
        width: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical {
        background: #2a2a35;
        border-radius: 3px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #6c63ff;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: #0d0d0f;
        height: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal {
        background: #2a2a35;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #6c63ff;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }
""")

central = QWidget()
window.setCentralWidget(central)

main_layout = QVBoxLayout(central)
main_layout.setContentsMargins(0, 0, 0, 0)
main_layout.setSpacing(0)

toolbar = QWidget()
toolbar.setFixedHeight(45)
toolbar.setStyleSheet("""
    QWidget {
        background-color: #1a1a1f;
        border-bottom: 1px solid #2a2a35;
    }
""")

toolbar_layout = QHBoxLayout(toolbar)
toolbar_layout.setContentsMargins(8, 0, 8, 0)
toolbar_layout.setSpacing(4)

button_style = """
    QPushButton {
        background-color: transparent;
        color: #6b6b80;
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 18px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2a2a35;
        color: #e8e8f0;
    }
    QPushButton:pressed {
        background-color: #3a3a45;
        color: #6c63ff;
    }
"""

btn_back    = QPushButton("←")
btn_forward = QPushButton("→")
btn_reload  = QPushButton("⟳")
btn_new_tab = QPushButton("+")

btn_back.setStyleSheet(button_style)
btn_forward.setStyleSheet(button_style)
btn_reload.setStyleSheet(button_style)
btn_new_tab.setStyleSheet(button_style)

address_bar = QLineEdit()
address_bar.setPlaceholderText("Search or enter address...")
address_bar.setStyleSheet("""
    QLineEdit {
        background-color: #1e1e28;
        color: #e8e8f0;
        border: 1.5px solid #2a2a35;
        border-radius: 20px;
        padding: 5px 16px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 1.5px solid #6c63ff;
        background-color: #16161e;
    }
""")

btn_bookmark = QPushButton("♟")
btn_bookmark.setStyleSheet(button_style)

btn_waffle = QPushButton("⊞")
btn_waffle.setStyleSheet(button_style)

toolbar_layout.addWidget(btn_back)
toolbar_layout.addWidget(btn_forward)
toolbar_layout.addWidget(btn_reload)
toolbar_layout.addWidget(address_bar)
toolbar_layout.addWidget(btn_bookmark)
toolbar_layout.addWidget(btn_waffle)
toolbar_layout.addWidget(btn_new_tab)

tab_bar = QTabBar()
tab_bar.setTabsClosable(True)
tab_bar.setMovable(True)
tab_bar.setExpanding(False)
tab_bar.setStyleSheet("""
    QTabBar {
        background-color: transparent;
    }
    QTabBar::tab {
        background-color: #1a1a1f;
        color: #6b6b80;
        padding: 8px 20px;
        border: none;
        border-right: 1px solid #2a2a35;
        font-size: 13px;
        min-width: 100px;
        border-radius: 8px 8px 0px 0px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #1e1e28;
        color: #e8e8f0;
        border-bottom: 2px solid #6c63ff;
    }
    QTabBar::tab:hover:!selected {
        background-color: #18181f;
        color: #aaaacc;
    }
""")

stack = QStackedWidget()

waffle_overlay = None

def show_waffle_menu():
    global waffle_overlay
    if waffle_overlay and waffle_overlay.isVisible():
        waffle_overlay.hide()
        return

    waffle_overlay = QWidget(window)
    waffle_overlay.setObjectName("wafflePanel")
    waffle_overlay.setStyleSheet("""
        QWidget#wafflePanel {
            background-color: #16161e;
            border: 1px solid #2a2a35;
            border-radius: 16px;
        }
    """)
    waffle_overlay.setFixedSize(330, 410)

    btn_pos = btn_waffle.mapTo(window, btn_waffle.rect().bottomRight())
    x = btn_pos.x() - 310
    y = btn_pos.y() + 6
    waffle_overlay.move(x, y)

    grid_layout = QVBoxLayout(waffle_overlay)
    grid_layout.setContentsMargins(14, 10, 14, 14)
    grid_layout.setSpacing(6)

    header = QWidget()
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(2, 0, 2, 0)

    title_lbl = QLabel("Apps")
    title_lbl.setStyleSheet("color: #6b6b80; font-size: 26px; letter-spacing: 1px; background: transparent;")

    close_btn = QPushButton("✕")
    close_btn.setFixedSize(24, 24)
    close_btn.setStyleSheet("""
        QPushButton {
            background-color: #2a2a35;
            color: #6b6b80;
            border: none;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #f87171;
            color: #ffffff;
        }
    """)
    close_btn.clicked.connect(waffle_overlay.hide)

    header_layout.addWidget(title_lbl)
    header_layout.addStretch()
    header_layout.addWidget(close_btn)
    grid_layout.addWidget(header)

    tools = [
        ("📊", "Sheets",     open_sheets),
        ("📝", "Docs",       open_docs),
        ("📑", "Slides",     open_slides),
        ("💻", "Code",       open_code),
        ("🧮", "Calc",       open_calc),
        ("📓", "Notepad",    open_notepad),
        ("🌤", "Weather",    open_weather),
        ("🎨", "Paint",      open_paint),
        ("🗺", "Map",        open_map),
        ("🍅", "Pomodoro",   open_pomodoro),
        ("📁", "Files",      open_filemanager),
        ("🚀", "Store",      open_store),
        ("📈", "Stocks",     open_stocks),
        ("🎯", "Goals",      open_goals),
        ("🧠", "Learn",      open_learn),
        ("✈️", "Plane Sim.",      open_plane),
        ("💻", "Proxy",      open_proxy)
    ]

    waffle_btn_style = """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 10px;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #2a2a3d;
        }
        QPushButton:pressed {
            background-color: #6c63ff;
        }
    """

    cols = 5
    row_widget = None
    row_layout = None

    for i, (icon, label, func) in enumerate(tools):
        if i % cols == 0:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            grid_layout.addWidget(row_widget)

        def make_action(f):
            def action():
                waffle_overlay.hide()
                f()
            return action

        btn = QPushButton()
        btn.setFixedSize(56, 66)
        btn.setStyleSheet(waffle_btn_style)
        btn.clicked.connect(make_action(func))

        btn_inner = QVBoxLayout(btn)
        btn_inner.setContentsMargins(0, 6, 0, 4)
        btn_inner.setSpacing(2)

        emoji_lbl = QLabel(icon)
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_lbl.setStyleSheet("font-size: 26px; background: transparent;")
        emoji_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        text_lbl = QLabel(label)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_lbl.setStyleSheet("font-size: 10px; color: #c8c8e0; background: transparent;")
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        btn_inner.addWidget(emoji_lbl)
        btn_inner.addWidget(text_lbl)

        row_layout.addWidget(btn)

    remainder = len(tools) % cols
    if remainder:
        for _ in range(cols - remainder):
            filler = QWidget()
            filler.setFixedSize(52, 56)
            row_layout.addWidget(filler)

    waffle_overlay.raise_()
    waffle_overlay.show()

btn_waffle.clicked.connect(show_waffle_menu)

def save_sheet_data(data):
    sheets = json.loads(data)
    storage.save_sheets(sheets)

def open_sheets():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SAVE:'):
                print("FILES:", msg[:80])
                save_sheet_data(msg[5:])
            elif msg.startswith('SAVESHEET:'):
                parts = msg[10:].split(':', 1)
                if len(parts) == 2:
                    sheet_id = parts[0]
                    data = parts[1]
                    storage.save_sheet_cells(sheet_id, data)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("📊 Sheets")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sheets_path = os.path.join(base_dir, "sheets_home.html")

    def on_load_finished(ok=True):
        if ok:
            sheets = storage.load_sheets()
            sheets_json = json.dumps(sheets)
            js = f"""
            function waitForLoad() {{
                if (typeof loadSheets === 'function') {{
                    loadSheets({sheets_json});
                }} else if (typeof loadGridData === 'function') {{
                    var sheets = {sheets_json};
                    var params = new URLSearchParams(window.location.search);
                    var id = params.get('id');
                    var sheet = sheets.find(function(s) {{ return s.id === id; }});
                    if (sheet) loadGridData(sheet.data);
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(sheets_path))

def open_docs():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SAVEDOC:'):
                docs = json.loads(msg[8:])
                storage.save_docs(docs)
            elif msg.startswith('SAVEDOCCONTENT:'):
                parts = msg[15:].split(':', 1)
                if len(parts) == 2:
                    storage.save_doc_content(parts[0], parts[1])

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("📝 Docs")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(base_dir, "docs_home.html")

    def on_load_finished(ok=True):
        if ok:
            docs = storage.load_docs()
            docs_json = json.dumps(docs)
            js = f"""
            function waitForLoad() {{
                if (typeof loadDocs === 'function') {{
                    loadDocs({docs_json});
                }} else if (typeof loadContent === 'function') {{
                    var docs = {docs_json};
                    var params = new URLSearchParams(window.location.search);
                    var id = params.get('id');
                    var doc = docs.find(function(d) {{ return d.id === id; }});
                    if (doc && doc.content) loadContent(doc.content);
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(docs_path))

def open_slides():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            print("SLIDES:", msg[:80])
            if msg.startswith('SAVESLIDES:'):
                slides = json.loads(msg[11:])
                storage.save_slides(slides)
            elif msg.startswith('SAVESLIDECONTENT:'):
                parts = msg[17:].split(':', 1)
                if len(parts) == 2:
                    pres_id = parts[0]
                    content = parts[1]
                    storage.save_slide_content(pres_id, content)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("📑 Slides")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    slides_path = os.path.join(base_dir, "slides_home.html")

    def on_load_finished(ok=True):
        if ok:
            current_url = webview.url().toString()
            slides = storage.load_slides()
            slides_json = json.dumps(slides)

            if 'slides_editor.html' in current_url:
                js = f"""
                function waitForLoad() {{
                    if (typeof loadSlideContent === 'function') {{
                        var slides = {slides_json};
                        var params = new URLSearchParams(window.location.search);
                        var id = params.get('id');
                        var pres = slides.find(function(s) {{ return s.id === id; }});
                        if (pres) loadSlideContent(pres.content);
                    }} else {{
                        setTimeout(waitForLoad, 100);
                    }}
                }}
                waitForLoad();
                """
            else:
                js = f"""
                function waitForLoad() {{
                    if (typeof loadSlides === 'function') {{
                        loadSlides({slides_json});
                    }} else {{
                        setTimeout(waitForLoad, 100);
                    }}
                }}
                waitForLoad();
                """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(slides_path))

def run_code(language, code, webview):
    import subprocess
    import tempfile

    try:
        if language == 'python':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                result = subprocess.run(
                    ['python', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout or result.stderr
                is_error = bool(result.stderr)

        elif language == 'javascript':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                f.flush()
                result = subprocess.run(
                    ['node', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout or result.stderr
                is_error = bool(result.stderr)

        elif language == 'html':
            output = 'HTML preview not supported yet'
            is_error = False

        else:
            output = 'Language not supported'
            is_error = True

    except subprocess.TimeoutExpired:
        output = 'Error: Code took too long to run'
        is_error = True
    except Exception as e:
        output = f'Error: {str(e)}'
        is_error = True

    output_js = json.dumps(output)
    webview.page().runJavaScript(f"showOutput({output_js}, {'true' if is_error else 'false'})")

def open_code():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SAVECODE:'):
                codes = json.loads(msg[9:])
                storage.save_codes(codes)
            elif msg.startswith('SAVECODECONTENT:'):
                parts = msg[16:].split(':', 1)
                if len(parts) == 2:
                    storage.save_code_content(parts[0], parts[1])
            elif msg.startswith('RUNCODE:'):
                parts = msg[8:].split(':', 1)
                if len(parts) == 2:
                    language = parts[0]
                    code = parts[1]
                    run_code(language, code, webview)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("💻 Code")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    code_path = os.path.join(base_dir, "code_home.html")

    def on_load_finished(ok=True):
        if ok:
            current_url = webview.url().toString()
            codes = storage.load_codes()
            codes_json = json.dumps(codes)

            if 'code_editor.html' in current_url:
                js = f"""
                function waitForLoad() {{
                    if (typeof loadContent === 'function') {{
                        var codes = {codes_json};
                        var params = new URLSearchParams(window.location.search);
                        var id = params.get('id');
                        var code = codes.find(function(c) {{ return c.id === id; }});
                        if (code && code.content) loadContent(code.content);
                    }} else {{
                        setTimeout(waitForLoad, 100);
                    }}
                }}
                waitForLoad();
                """
            else:
                js = f"""
                function waitForLoad() {{
                    if (typeof loadCodes === 'function') {{
                        loadCodes({codes_json});
                    }} else {{
                        setTimeout(waitForLoad, 100);
                    }}
                }}
                waitForLoad();
                """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(code_path))

def open_calc():
    webview = QWebEngineView()

    index = stack.addWidget(webview)
    tab_bar.addTab("🧮 Calculator")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    calc_path = os.path.join(base_dir, "calculator.html")
    webview.load(QUrl.fromLocalFile(calc_path))

def open_notepad():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SAVENOTEPAD:'):
                storage.save_notepad(msg[12:])

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("📓 Notepad")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    notepad_path = os.path.join(base_dir, "notepad.html")

    def on_load_finished(ok=True):
        if ok:
            content = storage.load_notepad()
            content_json = json.dumps(content)
            js = f"""
            function waitForLoad() {{
                if (typeof loadContent === 'function') {{
                    loadContent({content_json});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(notepad_path))

def open_weather():
    from PyQt6.QtCore import QObject, pyqtSignal

    class WeatherWorker(QObject):
        result_ready = pyqtSignal(str)
        error = pyqtSignal()

        def fetch(self, city):
            import threading
            def run():
                try:
                    import urllib.request
                    geo_url = f'https://nominatim.openstreetmap.org/search?q={urllib.request.quote(city)}&format=json&limit=1'
                    req = urllib.request.Request(geo_url, headers={'User-Agent': 'ScribbleBrowser/1.0'})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        geo_data = json.loads(r.read().decode('utf-8', errors='ignore'))

                    if not geo_data:
                        self.error.emit()
                        return

                    lat = geo_data[0]['lat']
                    lon = geo_data[0]['lon']
                    city_name = geo_data[0]['display_name'].split(',')[0]

                    weather_url = (
                        f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
                        f'&current=temperature_2m,apparent_temperature,relative_humidity_2m,'
                        f'wind_speed_10m,weather_code,visibility'
                        f'&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto'
                    )
                    req2 = urllib.request.Request(weather_url, headers={'User-Agent': 'ScribbleBrowser/1.0'})
                    with urllib.request.urlopen(req2, timeout=10) as r:
                        weather_data = json.loads(r.read().decode('utf-8', errors='ignore'))

                    current = weather_data['current']
                    result = {
                        'city': city_name,
                        'temp': current['temperature_2m'],
                        'feelsLike': current['apparent_temperature'],
                        'humidity': current['relative_humidity_2m'],
                        'wind': current['wind_speed_10m'],
                        'weatherCode': current['weather_code'],
                        'visibility': current.get('visibility')
                    }
                    self.result_ready.emit(json.dumps(result))

                except Exception as e:
                    print('Weather error:', e)
                    self.error.emit()

            threading.Thread(target=run, daemon=True).start()

    webview = QWebEngineView()
    worker = WeatherWorker()
    worker.result_ready.connect(lambda data: webview.page().runJavaScript(f'showWeather({data})'))
    worker.error.connect(lambda: webview.page().runJavaScript('showError()'))

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SEARCHWEATHER:'):
                city = msg[14:]
                worker.fetch(city)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("🌤 Weather")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    weather_path = os.path.join(base_dir, "weather.html")
    webview.load(QUrl.fromLocalFile(weather_path))

def open_paint():
    webview = QWebEngineView()

    index = stack.addWidget(webview)
    tab_bar.addTab("🎨 Paint")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    paint_path = os.path.join(base_dir, "paint.html")
    webview.load(QUrl.fromLocalFile(paint_path))

def open_map():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SAVEMAP:'):
                data = json.loads(msg[8:])
                storage.save_map(data)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("🗺 Map")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(base_dir, "map.html")

    def on_load_finished(ok=True):
        if ok:
            data = storage.load_map()
            data_json = json.dumps(data)
            js = f"""
            function waitForLoad() {{
                if (typeof loadContent === 'function') {{
                    loadContent({data_json});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(map_path))

def open_portal():
    webview = QWebEngineView()

    index = stack.addWidget(webview)
    tab_bar.addTab("𖣯 Chess")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    portal_path = os.path.join(base_dir, "chess.html")
    webview.load(QUrl.fromLocalFile(portal_path))

def open_pomodoro():
    webview = QWebEngineView()

    index = stack.addWidget(webview)
    tab_bar.addTab("🍅 Pomodoro")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    pomodoro_path = os.path.join(base_dir, "pomodoro.html")
    webview.load(QUrl.fromLocalFile(pomodoro_path))

def open_filemanager():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            print("FILES:", msg[:80])
            if msg.startswith('NAVIGATE:'):
                path = msg[9:]
                if not os.path.isabs(path):
                    path = storage.get_special_folder(path)
                data = storage.get_files(path)
                data_json = json.dumps(data)
                webview.page().runJavaScript(f'loadFiles({data_json})')

            elif msg.startswith('NAVIGATEUP:'):
                path = msg[11:]
                parent = os.path.dirname(path)
                if parent == path:
                    return
                data = storage.get_files(parent)
                data_json = json.dumps(data)
                webview.page().runJavaScript(f'loadFiles({data_json})')

            elif msg.startswith('NEWFOLDER:'):
                parts = msg[10:].split('|', 1)
                if len(parts) == 2:
                    new_path = os.path.join(parts[0], parts[1])
                    try:
                        os.makedirs(new_path)
                    except Exception as e:
                        print('Error:', e)
                    data = storage.get_files(parts[0])
                    webview.page().runJavaScript(f'loadFiles({json.dumps(data)})')

            elif msg.startswith('RENAME:'):
                parts = msg[7:].split('|', 1)
                if len(parts) == 2:
                    old_path = parts[0]
                    new_name = parts[1]
                    new_path = os.path.join(os.path.dirname(old_path), new_name)
                    try:
                        os.rename(old_path, new_path)
                    except Exception as e:
                        print('Error:', e)
                    data = storage.get_files(os.path.dirname(old_path))
                    webview.page().runJavaScript(f'loadFiles({json.dumps(data)})')

            elif msg.startswith('DELETE:'):
                path = msg[7:]
                try:
                    if os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    print('Error:', e)
                data = storage.get_files(os.path.dirname(path))
                webview.page().runJavaScript(f'loadFiles({json.dumps(data)})')

            elif msg.startswith('PASTE:'):
                parts = msg[6:].split('|', 1)
                if len(parts) == 2:
                    src = parts[0]
                    dst = os.path.join(parts[1], os.path.basename(src))
                    try:
                        if os.path.isdir(src):
                            import shutil
                            shutil.copytree(src, dst)
                        else:
                            import shutil
                            shutil.copy2(src, dst)
                    except Exception as e:
                        print('Error:', e)
                    data = storage.get_files(parts[1])
                    webview.page().runJavaScript(f'loadFiles({json.dumps(data)})')

            elif msg.startswith('OPENFILE:'):
                path = msg[9:]
                try:
                    os.startfile(path)
                except Exception as e:
                    print('Error:', e)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("📁 Files")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    fm_path = os.path.join(base_dir, "filemanager.html")

    def on_load_finished(ok=True):
        print("FILE MANAGER LOADED:", ok)
        if ok:
            home = os.path.expanduser('~')
            data = storage.get_files(home)
            data_json = json.dumps(data)
            js = f"""
            function waitForLoad() {{
                if (typeof loadFiles === 'function') {{
                    loadFiles({data_json});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(fm_path))

def parse_winget_search(output):
    apps = []
    lines = output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('-') or line.startswith('Name') or line.startswith('\\') or line.startswith('/') or line.startswith('|'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            app_id = None
            for part in parts:
                if '.' in part and not part.startswith('-'):
                    app_id = part
                    break
            if not app_id:
                continue
            id_index = parts.index(app_id)
            name = ' '.join(parts[:id_index])
            version = parts[id_index + 1] if len(parts) > id_index + 1 else ''
            if name:
                apps.append({'name': name, 'id': app_id, 'version': version, 'desc': ''})
    return apps[:20]

def open_store():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SEARCH:'):
                query = msg[7:]
                import subprocess
                result = subprocess.run(
                    ['winget', 'search', query, '--accept-source-agreements'],
                    capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore'
                )
                apps = parse_winget_search(result.stdout)
                print("Search results:", apps[:3])
                webview.page().runJavaScript(f'loadSearchResults({json.dumps(apps)})')

            elif msg.startswith('INSTALL:'):
                parts = msg[8:].split(':', 1)
                if len(parts) == 2:
                    app_id = parts[0]
                    app_name = parts[1]
                    import subprocess, threading
                    def do_install():
                        print("Starting install:", app_id)
                        result = subprocess.run(
                            ['winget', 'install', '--id', app_id, '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'],
                            capture_output=True, text=True, encoding='utf-8', errors='ignore'
                        )
                        print("Winget stdout:", result.stdout)
                        print("Winget stderr:", result.stderr)
                        installed = storage.load_store()
                        installed.append({'id': app_id, 'name': app_name})
                        storage.save_store(installed)
                        webview.page().runJavaScript(f'installComplete({json.dumps(app_id)})')
                        webview.page().runJavaScript(f'loadInstalledApps({json.dumps(installed)})')
                    threading.Thread(target=do_install, daemon=True).start()

            elif msg.startswith('OPENAPP:'):
                app_id = msg[8:]
                import subprocess
                subprocess.Popen(['winget', 'install', '--id', app_id, '--accept-package-agreements', '--accept-source-agreements'])

            elif msg.startswith('UNINSTALL:'):
                app_id = msg[10:]
                import subprocess, threading
                def do_uninstall():
                    subprocess.run(
                        ['winget', 'uninstall', '--id', app_id, '--accept-source-agreements'],
                        capture_output=True, text=True
                    )
                    installed = storage.load_store()
                    installed = [a for a in installed if a['id'] != app_id]
                    storage.save_store(installed)
                    webview.page().runJavaScript(f'loadInstalledApps({json.dumps(installed)})')
                threading.Thread(target=do_uninstall, daemon=True).start()

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("🏪 Store")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    store_path = os.path.join(base_dir, "store.html")

    def on_load_finished(ok=True):
        if ok:
            installed = storage.load_store()
            js = f"""
            function waitForLoad() {{
                if (typeof loadInstalledApps === 'function') {{
                    loadInstalledApps({json.dumps(installed)});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(store_path))

def open_stocks():
    webview = QWebEngineView()

    class StocksPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            print("STOCKS MSG:", msg[:80])
            if msg.startswith('SEARCHSTOCK:'):
                query = msg[12:]
                self.do_search(query)
            elif msg.startswith('FETCHSTOCKS:'):
                tickers = msg[12:]
                self.do_fetch(tickers)
            elif msg.startswith('SAVEWATCHLIST:'):
                data = json.loads(msg[14:])
                storage.save_watchlist(data)

        def do_search(self, query):
            try:
                import urllib.request
                url = f'https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6&newsCount=0'
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                })
                with urllib.request.urlopen(req, timeout=10) as r:
                    raw = r.read().decode('utf-8', errors='ignore')
                data = json.loads(raw)
                results = []
                for q in data.get('quotes', []):
                    if q.get('symbol'):
                        results.append({
                            'ticker': q['symbol'],
                            'name': q.get('longname') or q.get('shortname') or q['symbol']
                        })
                results_json = json.dumps(results, ensure_ascii=True)
                webview.page().runJavaScript(f'showSearchResults({results_json})')
            except Exception as e:
                print('Search error:', type(e).__name__, str(e))

        def do_fetch(self, tickers):
            print("Fetching tickers:", tickers)
            try:
                import urllib.request
                ticker_list = tickers.split(',')
                results = []
                for ticker in ticker_list:
                    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d'
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                    })
                    with urllib.request.urlopen(req, timeout=10) as r:
                        raw = r.read().decode('utf-8', errors='ignore')
                    data = json.loads(raw)
                    meta = data['chart']['result'][0]['meta']
                    price = meta.get('regularMarketPrice')
                    prev_close = meta.get('previousClose') or meta.get('chartPreviousClose')
                    change = price - prev_close if price and prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close else 0
                    results.append({
                        'ticker': ticker,
                        'name': meta.get('symbol'),
                        'price': price,
                        'change': change,
                        'changePct': change_pct
                    })
                results_json = json.dumps(results, ensure_ascii=True)
                print("Results:", results_json[:100])
                webview.page().runJavaScript(f'updateStockData({results_json})')
            except Exception as e:
                print('Fetch error:', type(e).__name__, str(e))
    webview.setPage(StocksPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("📈 Stocks")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    stocks_path = os.path.join(base_dir, "stocks.html")

    def on_load_finished(ok=True):
        if ok:
            data = storage.load_watchlist()
            js = f"""
            function waitForLoad() {{
                if (typeof loadWatchlist === 'function') {{
                    loadWatchlist({json.dumps(data)});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(stocks_path))

def open_goals():
    webview = QWebEngineView()

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('SAVEGOALS:'):
                data = json.loads(msg[10:])
                storage.save_goals(data)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("🎯 Goals")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    goals_path = os.path.join(base_dir, "goals.html")

    def on_load_finished(ok=True):
        if ok:
            data = storage.load_goals()
            js = f"""
            function waitForLoad() {{
                if (typeof loadGoals === 'function') {{
                    loadGoals({json.dumps(data)});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(goals_path))

def open_learn():
    from PyQt6.QtCore import QObject, pyqtSignal

    with open("config.json", "r") as f:
        CONFIG = json.load(f)
        print(f"DEBUG: Using URL -> {CONFIG['api']['url']}")
        print(f"DEBUG: Using Model -> {CONFIG['model']['name']}")

    class LearnWorker(QObject):
        path_ready = pyqtSignal(str)
        lesson_ready = pyqtSignal(str, int, str)
        quiz_ready = pyqtSignal(str, int, str)
        error = pyqtSignal(str)

        def generate_path(self, topic):
            import threading
            def run():
                try:
                    import urllib.request
                    prompt = f"""Create a learning path for: {topic}

Return ONLY valid JSON in this exact format, nothing else:
{{
  "topic": "{topic}",
  "modules": [
    {{"title": "Module Title", "desc": "One sentence description"}},
    {{"title": "Module Title", "desc": "One sentence description"}}
  ]
}}

Create how many modules you think are needed that progress from beginner to advanced. Return only JSON."""

                    data = json.dumps({
                        "model": CONFIG["model"]["name"],
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }).encode()

                    req = urllib.request.Request(
                        CONFIG["api"]["url"],
                        data=data,
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=CONFIG["api"]["timeout"]) as r:
                        result = json.loads(r.read().decode('utf-8'))

                    response = result['message']['content'].strip()
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    if start == -1:
                        self.error.emit('Could not generate learning path')
                        return
                    parsed = json.loads(response[start:end])
                    self.path_ready.emit(json.dumps(parsed))

                except Exception as e:
                    print('Path error:', e)
                    self.error.emit(str(e))

            threading.Thread(target=run, daemon=True).start()

        def generate_lesson(self, course_id, module_index, topic, module_title):
            import threading
            def run():
                try:
                    import urllib.request
                    prompt = f"""Act as an expert educator. Your task is to draft a comprehensive for the students which is easy-to-follow lesson  for the module "{module_title}," which is a component of the broader topic "{topic}."

Follow these structural guidelines for the lesson:
    1. Concept Explanation: Define the core idea of {module_title} using simple, relatable language. Explain why this concept is important within the context of {topic}. 
    2. Practical Examples: Provide 2-3 distinct examples that illustrate the concept in action. 
    3. Key Takeaways: List the essential points the student must remember to master this module. 
    4. Practice Assignment: Create a short homework task that allows the student to apply what they just learned.
    5. Make sure the lesson is filled with content for the student.

Output Requirements:

    -Tone: Encouraging, professional, and clear. Make it sound like you are teaching them.

    -Format: Use plain text only. Do not use Markdown, bolding, or special symbols.

    -Audience: Write for a student who is new to this specific module, but make sure this is loaded with teachings.
"""

                    data = json.dumps({
                        "model": CONFIG["model"]["name"],
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }).encode()

                    req = urllib.request.Request(
                        CONFIG["api"]["url"],
                        data=data,
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=CONFIG["api"]["timeout"]) as r:
                        result = json.loads(r.read().decode('utf-8'))

                    lesson = result['message']['content'].strip()
                    self.lesson_ready.emit(course_id, module_index, lesson)

                except Exception as e:
                    print('Lesson error:', type(e).__name__, str(e))
                    self.error.emit(str(e))

            threading.Thread(target=run, daemon=True).start()

        def generate_quiz(self, course_id, module_index, topic, module_title):
            import threading
            def run():
                try:
                    import urllib.request
                    prompt = f"""Create a quiz about "{module_title}" from the topic "{topic}".

Rules:
- Every question must have one clearly and objectively correct answer
- The correct answer must be factually accurate
- Wrong answers should be plausible but clearly incorrect
- Do not use trick questions or subjective answers
- Base all questions strictly on established facts about the topic
- All answers must be able to be found in content you have given from {module_title}.

Return ONLY valid JSON in this exact format, nothing else:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0
  }}
]

The "answer" field is the index (0-3) of the correct option.
Create exactly 4 questions. Return only the JSON array."""

                    data = json.dumps({
                        "model": CONFIG["model"]["name"],
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }).encode()

                    req = urllib.request.Request(
                        CONFIG["api"]["url"],
                        data=data,
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=CONFIG["api"]["timeout"]) as r:
                        result = json.loads(r.read().decode('utf-8'))

                    response = result['message']['content'].strip()
                    start = response.find('[')
                    end = response.rfind(']') + 1
                    if start == -1:
                        self.error.emit('Could not generate quiz')
                        return

                    raw = " ".join(response[start:end].split())
                    quiz = json.loads(response[start:end])
                    self.quiz_ready.emit(course_id, module_index, json.dumps(quiz))

                except Exception as e:
                    print('Quiz error:', e)
                    self.error.emit(str(e))

            threading.Thread(target=run, daemon=True).start()

    webview = QWebEngineView()
    worker = LearnWorker()

    worker.path_ready.connect(lambda data: webview.page().runJavaScript(f'pathGenerated({data})'))
    worker.lesson_ready.connect(lambda cid, mi, lesson: webview.page().runJavaScript(
        f'lessonGenerated({json.dumps(cid)}, {mi}, {json.dumps(lesson)})'))
    worker.quiz_ready.connect(lambda cid, mi, quiz: webview.page().runJavaScript(
        f'quizGenerated({json.dumps(cid)}, {mi}, {quiz})'))
    worker.error.connect(lambda msg: webview.page().runJavaScript(f'showError({json.dumps(msg)})'))

    class CustomPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, source):
            if msg.startswith('GENERATEPATH:'):
                topic = msg[13:]
                worker.generate_path(topic)
            elif msg.startswith('GENERATELESSON:'):
                parts = msg[15:].split(':', 3)
                if len(parts) == 4:
                    worker.generate_lesson(parts[0], int(parts[1]), parts[2], parts[3])
            elif msg.startswith('GENERATEQUIZ:'):
                parts = msg[13:].split(':', 3)
                if len(parts) == 4:
                    worker.generate_quiz(parts[0], int(parts[1]), parts[2], parts[3])
            elif msg.startswith('SAVECOURSES:'):
                data = json.loads(msg[12:])
                storage.save_courses(data)

    webview.setPage(CustomPage(webview))

    index = stack.addWidget(webview)
    tab_bar.addTab("🧠 Learn")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    learn_path = os.path.join(base_dir, "learn.html")

    def on_load_finished(ok=True):
        if ok:
            data = storage.load_courses()
            js = f"""
            function waitForLoad() {{
                if (typeof loadCourses === 'function') {{
                    loadCourses({json.dumps(data)});
                }} else {{
                    setTimeout(waitForLoad, 100);
                }}
            }}
            waitForLoad();
            """
            webview.page().runJavaScript(js)

    webview.loadFinished.connect(on_load_finished)
    webview.load(QUrl.fromLocalFile(learn_path))

def open_plane():

    import subprocess
    subprocess.Popen(['python', 'plane.py'])

def open_proxy():

    import subprocess
    subprocess.Popen(['python', 'proxy.py'])

def game1():
    import subprocess
    subprocess.Popen(['python', 'game1.py'])

def add_new_tab(url="scribble://home"):
    webview = QWebEngineView()

    s = webview.settings()
    s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
    s.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

    index = stack.addWidget(webview)
    tab_bar.addTab("New Tab")
    tab_bar.setCurrentIndex(index)
    stack.setCurrentIndex(index)

    webview.titleChanged.connect(
        lambda title: tab_bar.setTabText(index, title[:20])
    )

    webview.urlChanged.connect(
        lambda q: address_bar.setText(q.toString())
    )

    if url == "scribble://home":
        load_home_page(webview)
    else:
        webview.setUrl(QUrl(url))

def load_home_page(webview):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: linear-gradient(135deg, #0d0d0f 0%, #1a0a2e 50%, #0d0d0f 100%);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                font-family: 'Segoe UI', sans-serif;
            }
            h1 {
                font-size: 72px;
                font-weight: 800;
                background: linear-gradient(135deg, #6c63ff, #a78bfa);
                -webkit-background-clip: text;
                background-clip: text;
                -webkit-text-fill-color: transparent;
                color: transparent;
                margin-bottom: 10px;
                letter-spacing: -2px;
            }
            p {
                color: #6b6b80;
                font-size: 16px;
                margin-bottom: 40px;
                padding-left: 2em;
            }
            input {
                width: 500px;
                padding: 14px 24px;
                border-radius: 30px;
                border: 1.5px solid #2a2a35;
                background: #1e1e28;
                color: #e8e8f0;
                font-size: 16px;
                outline: none;
                text-align: center;
            }
            input:focus {
                border-color: #6c63ff;
            }
        </style>
    </head>
    <body>
        <h1>Scribble</h1>
        <p> Your thoughts, your web.
        </p>
        <input type="text" placeholder="Type b127 OR platformer..."
               onkeydown="if(event.key==='Enter') window.location.href='https://www.google.com/search?q='+this.value"/>
    </body>
    </html>
    """
    webview.setHtml(html)

def navigate():
    url = address_bar.text()
    if " " in url or "." not in url:
        url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
    elif not url.startswith("http"):
        url = "https://" + url
    current_webview = stack.currentWidget()
    current_webview.setUrl(QUrl(url))

def go_back():
    stack.currentWidget().back()

def go_forward():
    stack.currentWidget().forward()

def go_reload():
    stack.currentWidget().reload()

def close_tab(index):
    if tab_bar.count() == 1:
        return
    widget = stack.widget(index)
    stack.removeWidget(widget)
    tab_bar.removeTab(index)

def update_address_bar(index):
    webview = stack.widget(index)
    if webview:
        address_bar.setText(webview.url().toString())

def switch_tab(index):
    stack.setCurrentIndex(index)
    update_address_bar(index)

address_bar.returnPressed.connect(navigate)
btn_back.clicked.connect(go_back)
btn_forward.clicked.connect(go_forward)
btn_reload.clicked.connect(go_reload)
btn_new_tab.clicked.connect(lambda: add_new_tab())
btn_bookmark.clicked.connect(open_portal)
tab_bar.tabCloseRequested.connect(close_tab)
tab_bar.currentChanged.connect(switch_tab)

content = QWidget()
content_layout = QVBoxLayout(content)
content_layout.setContentsMargins(0, 0, 0, 0)
content_layout.setSpacing(0)
content_layout.addWidget(stack, 1)

from PyQt6.QtCore import QTimer
import datetime

bottom_bar = QWidget()
bottom_bar.setFixedHeight(60)
bottom_bar.setStyleSheet("background-color: #0d0d0f; border-top: 1px solid #2a2a35;")
bottom_layout = QHBoxLayout(bottom_bar)
bottom_layout.setContentsMargins(16, 0, 16, 0)

btn_play = QPushButton("▶")
btn_play.setFixedSize(40, 40)
btn_play.setStyleSheet("""
    QPushButton {
        background-color: #6c63ff;
        color: white;
        border: none;
        border-radius: 20px;
        font-size: 16px;
    }
    QPushButton:hover { background-color: #5a52d5; }
    QPushButton:pressed { background-color: #4a42c5; }
""")
btn_play.clicked.connect(game1)

clock_label = QLabel()
clock_label.setStyleSheet("""
    color: #e8e8f0;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 1px;
""")

date_label = QLabel()
date_label.setStyleSheet("""
    color: #6b6b80;
    font-size: 11px;
    letter-spacing: 1px;
""")

clock_widget = QWidget()
clock_inner = QVBoxLayout(clock_widget)
clock_inner.setContentsMargins(0, 0, 0, 0)
clock_inner.setSpacing(2)
clock_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
clock_inner.addWidget(clock_label, alignment=Qt.AlignmentFlag.AlignRight)
clock_inner.addWidget(date_label, alignment=Qt.AlignmentFlag.AlignRight)

def update_clock():
    now = datetime.datetime.now()
    clock_label.setText(now.strftime('%I:%M:%S %p'))
    date_label.setText(now.strftime('%A, %B %d %Y'))

timer = QTimer()
timer.timeout.connect(update_clock)
timer.start(1000)
update_clock()

bottom_layout.addSpacing(161) 
bottom_layout.addStretch()
bottom_layout.addWidget(btn_play)
bottom_layout.addStretch()
clock_widget.setFixedWidth(150)
bottom_layout.addWidget(clock_widget)

content_layout.addWidget(bottom_bar)

h_layout = QHBoxLayout()
h_layout.setContentsMargins(0, 0, 0, 0)
h_layout.setSpacing(0)
h_layout.addWidget(content)

h_widget = QWidget()
h_widget.setLayout(h_layout)

main_layout.addWidget(tab_bar)
main_layout.addWidget(toolbar)
main_layout.addWidget(h_widget)
main_layout.setStretch(0, 0)
main_layout.setStretch(1, 0)
main_layout.setStretch(2, 1)

def ninja():
    TRIGGER = "b127"
    SCRIPT_TO_RUN = "ninja.py"
    buffer = []

    def on_key_event(event):
        nonlocal buffer
        if event.event_type == keyboard.KEY_DOWN:
            buffer.append(event.name)
            if len(buffer) > len(TRIGGER):
                buffer.pop(0)
            if "".join(buffer) == TRIGGER:
                try:
                    subprocess.Popen([sys.executable, SCRIPT_TO_RUN])
                except FileNotFoundError:
                    pass
                buffer.clear()

    keyboard.hook(on_key_event)

def plat():
    TRIGGER = "platformer"
    SCRIPT_TO_RUN = "plat.py"
    buffer = []

    def on_key_event(event):
        nonlocal buffer
        if event.event_type == keyboard.KEY_DOWN:
            buffer.append(event.name)
            if len(buffer) > len(TRIGGER):
                buffer.pop(0)
            if "".join(buffer) == TRIGGER:
                try:
                    subprocess.Popen([sys.executable, SCRIPT_TO_RUN])
                except FileNotFoundError:
                    pass
                buffer.clear()

    keyboard.hook(on_key_event)


import hashlib

class LoginScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.correct = None
        self.password_file = 'password.hash'
        self.is_new_user = not os.path.exists(self.password_file)

        if not self.is_new_user:
            with open(self.password_file, 'r') as f:
                self.correct = f.read().strip()

        self.setWindowTitle('Scribble')
        self.setFixedSize(500, 400)
        self.setStyleSheet("QDialog { background-color: #0d0d0f; }")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        title = QLabel('Scribble')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 52px;
            font-weight: 800;
            color: #6c63ff;
            letter-spacing: -2px;
            margin-bottom: 4px;
        """)

        subtitle = QLabel('Create your password' if self.is_new_user else 'Your personal browser')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #3a3a55;
            letter-spacing: 3px;
            margin-bottom: 40px;
        """)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Create a password...' if self.is_new_user else 'Enter password...')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(280)
        self.password_input.setFixedHeight(46)
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e28;
                color: #e8e8f0;
                border: 1.5px solid #2a2a35;
                border-radius: 23px;
                padding: 0 20px;
                font-size: 15px;
            }
            QLineEdit:focus { border-color: #6c63ff; }
        """)
        self.password_input.returnPressed.connect(self.try_login)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText('Confirm password...')
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setFixedWidth(280)
        self.confirm_input.setFixedHeight(46)
        self.confirm_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e28;
                color: #e8e8f0;
                border: 1.5px solid #2a2a35;
                border-radius: 23px;
                padding: 0 20px;
                font-size: 15px;
            }
            QLineEdit:focus { border-color: #6c63ff; }
        """)
        self.confirm_input.setVisible(self.is_new_user)
        self.confirm_input.returnPressed.connect(self.try_login)

        self.error_label = QLabel('')
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("""
            color: #f87171;
            font-size: 13px;
            margin-top: 10px;
        """)

        btn = QPushButton('Create Password' if self.is_new_user else 'Unlock')
        btn.setFixedWidth(280)
        btn.setFixedHeight(46)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                border: none;
                border-radius: 23px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #5a52d5; }
            QPushButton:pressed { background-color: #4a42c5; }
        """)
        btn.clicked.connect(self.try_login)

        input_wrapper = QWidget()
        input_layout = QVBoxLayout(input_wrapper)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.setSpacing(12)
        input_layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(self.confirm_input, alignment=Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(self.error_label)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(input_wrapper)

    def try_login(self):
        password = self.password_input.text().strip()
        if not password:
            self.error_label.setText('Please enter a password.')
            return

        if self.is_new_user:
            confirm = self.confirm_input.text().strip()
            if not confirm:
                self.error_label.setText('Please confirm your password.')
                return
            if password != confirm:
                self.error_label.setText('Passwords do not match.')
                self.password_input.clear()
                self.confirm_input.clear()
                self.password_input.setFocus()
                return
            hashed = hashlib.sha256(password.encode()).hexdigest()
            with open(self.password_file, 'w') as f:
                f.write(hashed)
            self.accept()
            launch_browser()
        else:
            entered = hashlib.sha256(password.encode()).hexdigest()
            if entered == self.correct:
                self.accept()
                launch_browser()
            else:
                self.error_label.setText('Wrong password. Try again.')
                self.password_input.clear()
                self.password_input.setFocus()

def launch_browser():
    add_new_tab()
    window.show()
    ninja()
    plat()

login = LoginScreen()
login.show()
app.exec()
print(":)")
print(":)")