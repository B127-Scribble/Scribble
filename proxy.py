import sys

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget
)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


START_PAGE = """
<html>
<head>
<style>

body{
    margin:0;
    background: radial-gradient(circle at top,#141824,#0b0f14);
    font-family:Segoe UI;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    height:100vh;
}

.container{
    text-align:center;
}

.title{
    font-size:48px;
    font-weight:600;
    margin-bottom:30px;
    letter-spacing:2px;
    color:#c9a7ff;
}

.search{
    width:500px;
    padding:14px;
    font-size:16px;
    border:none;
    border-radius:12px;
    background:#161b22;
    color:white;
    outline:none;
}

.search:focus{
    box-shadow:0 0 10px #9d7dff;
}

</style>
</head>

<body>

<div class="container">

<div class="title">Nebula</div>

<input class="search" placeholder="Search the web..."
onkeydown="
if(event.key==='Enter'){
window.location='https://duckduckgo.com/?q='+this.value
}
">

</div>

</body>
</html>
"""


class BrowserTab(QWebEngineView):

    def __init__(self):
        super().__init__()
        self.setHtml(START_PAGE)


class ProxyBrowser(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nebula Proxy")
        self.resize(1200, 750)

        layout = QVBoxLayout()

        top_bar = QHBoxLayout()

        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setFixedWidth(40)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter URL...")

        self.go_btn = QPushButton("Go")

        top_bar.addWidget(self.new_tab_btn)
        top_bar.addWidget(self.url_bar)
        top_bar.addWidget(self.go_btn)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)

        layout.addLayout(top_bar)
        layout.addWidget(self.tabs)

        self.setLayout(layout)

        self.new_tab_btn.clicked.connect(self.add_tab)
        self.go_btn.clicked.connect(self.load_page)
        self.url_bar.returnPressed.connect(self.load_page)

        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.add_tab()

    def current_browser(self):
        return self.tabs.currentWidget()

    def add_tab(self):

        browser = BrowserTab()

        index = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(
            lambda url, browser=browser:
            self.update_url(url, browser)
        )

    def close_tab(self, index):

        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def load_page(self):

        text = self.url_bar.text()

        if "." in text:
            url = "https://" + text
        else:
            url = f"https://duckduckgo.com/?q={text}"

        self.current_browser().setUrl(QUrl(url))

    def update_url(self, url, browser):

        if browser == self.current_browser():
            self.url_bar.setText(url.toString())


dark_style = """

QWidget{
    background:#0b0f14;
    color:#e6edf3;
    font-family:Segoe UI;
}

QLineEdit{
    background:#161b22;
    border:1px solid #30363d;
    padding:8px;
    border-radius:8px;
}

QPushButton{
    background:#2a1f45;
    border:none;
    padding:8px;
    border-radius:8px;
    color:#d6c8ff;
}

QPushButton:hover{
    background:#3a2b63;
}

QTabWidget::pane{
    border:none;
}

QTabBar::tab{
    background:#161b22;
    padding:10px;
    border-radius:6px;
    margin-right:4px;
}

QTabBar::tab:selected{
    background:#2a1f45;
    color:#c9a7ff;
}

"""

app = QApplication(sys.argv)
app.setStyleSheet(dark_style)

window = ProxyBrowser()
window.show()

sys.exit(app.exec())