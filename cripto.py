import sys
import os

# --- PYINSTALLER QT PLATFORM PLUGIN FIX (MUST BE BEFORE PYQT5 IMPORTS) ---
if getattr(sys, 'frozen', False):
    # Running as compiled executable (.exe)
    base_path = sys._MEIPASS
    # Tell Qt exactly where to find the platform plugins (like qwindows.dll)
    plugin_path = os.path.join(base_path, 'PyQt5', 'Qt5', 'plugins', 'platforms')
    if not os.path.exists(plugin_path):
        plugin_path = os.path.join(base_path, 'PyQt5', 'Qt', 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
# ------------------------------------------------------------------------

import hashlib
import requests
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QLineEdit, QDialog, QFormLayout, 
                             QMessageBox, QScrollArea, QFrame, QMenuBar, QAction, QMenu, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer, QDateTime
from PyQt5.QtGui import QFont, QColor, QDesktopServices

import pyqtgraph as pg

# Suppress Wayland warning on Linux/Gnome
os.environ["QT_QPA_PLATFORM"] = "xcb"

# --- Theme Definitions ---
THEMES = {
    "Dark Purple": {
        "bg": "#1E1E24", "panel": "#25252D", "accent": "#8B5CF6", 
        "text": "#F8F8F2", "text_muted": "#A0A0B0", "border": "#33333D",
        "graph_bg": "#25252D", "graph_fg": "#A0A0B0"
    },
    "Soft Blue": {
        "bg": "#1A202C", "panel": "#2D3748", "accent": "#4299E1", 
        "text": "#F7FAFC", "text_muted": "#A0AEC0", "border": "#4A5568",
        "graph_bg": "#2D3748", "graph_fg": "#A0AEC0"
    },
    "Warm Orange": {
        "bg": "#2D241E", "panel": "#3D2E24", "accent": "#ED8936", 
        "text": "#FFF5F5", "text_muted": "#CBD5E0", "border": "#4A3B32",
        "graph_bg": "#3D2E24", "graph_fg": "#CBD5E0"
    },
    "Gentle Pink": {
        "bg": "#2D1F26", "panel": "#3D2A33", "accent": "#ED64A6", 
        "text": "#FFF5F7", "text_muted": "#CBD5E0", "border": "#4A3240",
        "graph_bg": "#3D2A33", "graph_fg": "#CBD5E0"
    },
    "Clean Light": {
        "bg": "#F7FAFC", "panel": "#FFFFFF", "accent": "#3182CE", 
        "text": "#1A202C", "text_muted": "#4A5568", "border": "#E2E8F0",
        "graph_bg": "#FFFFFF", "graph_fg": "#4A5568"
    }
}

THEME_FILE = os.path.expanduser("~/.mamassa_cripto_theme")
AUTH_FILE = os.path.expanduser("~/.mamassa_cripto_auth")

def load_theme():
    if os.path.exists(THEME_FILE):
        with open(THEME_FILE, "r") as f:
            theme = f.read().strip()
            return theme if theme in THEMES else "Dark Purple"
    return "Dark Purple"

def save_theme(theme_name):
    with open(THEME_FILE, "w") as f:
        f.write(theme_name)

def get_stylesheet(theme_name):
    t = THEMES[theme_name]
    return f"""
        QMainWindow {{ background-color: {t['bg']}; color: {t['text']}; }}
        QMenuBar {{ background-color: {t['bg']}; color: {t['text']}; border-bottom: 1px solid {t['border']}; padding: 5px; }}
        QMenuBar::item:selected {{ background-color: {t['border']}; border-radius: 4px; }}
        QMenu {{ background-color: {t['panel']}; color: {t['text']}; border: 1px solid {t['border']}; }}
        QMenu::item:selected {{ background-color: {t['accent']}; color: white; }}
        QTabWidget::pane {{ border: 1px solid {t['border']}; background-color: {t['panel']}; border-radius: 8px; margin-top: -1px; }}
        QTabBar::tab {{ background: {t['bg']}; color: {t['text_muted']}; padding: 12px 24px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; font-weight: bold; font-size: 13px; }}
        QTabBar::tab:selected {{ background: {t['panel']}; color: {t['accent']}; border-bottom: 2px solid {t['accent']}; }}
        QTabBar::tab:hover {{ color: {t['text']}; }}
        QTableWidget {{ background-color: {t['panel']}; color: {t['text']}; border: none; gridline-color: {t['border']}; font-size: 13px; selection-background-color: {t['border']}; }}
        QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {t['border']}; }}
        QHeaderView::section {{ background-color: {t['bg']}; color: {t['accent']}; padding: 10px; border: none; font-weight: bold; font-size: 12px; text-transform: uppercase; }}
        QPushButton {{ background-color: {t['accent']}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 13px; }}
        QPushButton:hover {{ background-color: {t['accent']}; opacity: 0.85; }}
        QLabel {{ color: {t['text']}; font-size: 14px; }}
        #statusLabel {{ color: {t['text_muted']}; font-size: 12px; }}
        #autoRefreshLabel {{ color: #10B981; font-size: 12px; font-weight: bold; }}
        QSplitter::handle {{ background-color: {t['border']}; width: 2px; }}
        QLineEdit {{ background-color: {t['border']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 8px; border-radius: 6px; font-size: 13px; }}
        QLineEdit:focus {{ border: 1px solid {t['accent']}; }}
        QDialog {{ background-color: {t['panel']}; color: {t['text']}; }}
    """

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- Security & Authentication ---
class AuthDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MaMassa Cripto | Security")
        self.resize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.is_setup = not os.path.exists(AUTH_FILE)
        
        if self.is_setup:
            self.title = QLabel("Create a Password")
            self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.instructions = QLabel("Min 8 characters. Must include letters and numbers.")
            self.instructions.setStyleSheet("font-size: 12px; margin-bottom: 10px; opacity: 0.7;")
        else:
            self.title = QLabel("Welcome Back")
            self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.instructions = QLabel("Enter your password to access MaMassa Cripto.")
            self.instructions.setStyleSheet("font-size: 12px; margin-bottom: 10px; opacity: 0.7;")
            
        layout.addWidget(self.title)
        layout.addWidget(self.instructions)
        
        form_layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password...")
        form_layout.addRow("Password:", self.password_input)
        
        if self.is_setup:
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.confirm_input.setPlaceholderText("Confirm password...")
            form_layout.addRow("Confirm:", self.confirm_input)
            
        layout.addLayout(form_layout)
        
        self.submit_btn = QPushButton("Create Password" if self.is_setup else "Unlock App")
        self.submit_btn.setStyleSheet("""
            QPushButton { padding: 10px; border-radius: 6px; font-weight: bold; margin-top: 15px; }
        """)
        self.submit_btn.clicked.connect(self.handle_auth)
        layout.addWidget(self.submit_btn)

    def handle_auth(self):
        pwd = self.password_input.text()
        
        if self.is_setup:
            confirm_pwd = self.confirm_input.text()
            if pwd != confirm_pwd:
                QMessageBox.warning(self, "Error", "Passwords do not match!")
                return
            if len(pwd) < 8:
                QMessageBox.warning(self, "Error", "Password must be at least 8 characters long.")
                return
            if not any(c.isalpha() for c in pwd) or not any(c.isdigit() for c in pwd):
                QMessageBox.warning(self, "Error", "Password must contain both letters and numbers.")
                return
            
            with open(AUTH_FILE, "w") as f:
                f.write(hash_password(pwd))
            self.accept()
        else:
            with open(AUTH_FILE, "r") as f:
                stored_hash = f.read().strip()
            if hash_password(pwd) == stored_hash:
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Incorrect password. Please try again.")
                self.password_input.clear()

# --- News Fetcher Thread ---
class NewsFetcher(QThread):
    news_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            try:
                cp_url = "https://cryptopanic.com/api/v1/posts/?public=true&kind=news&filter=hot"
                cp_response = requests.get(cp_url, timeout=10)
                if cp_response.status_code == 200:
                    cp_data = cp_response.json()
                    news_items = []
                    for item in cp_data.get('results', [])[:15]:
                        news_items.append({
                            'title': item.get('title', 'No Title'),
                            'url': item.get('url', '#'),
                            'source': item.get('source', {}).get('title', 'CryptoPanic'),
                            'sentiment': item.get('sentiment', 'neutral')
                        })
                    self.news_received.emit(news_items)
                    return
            except:
                pass
            
            news_items = [
                {'title': 'Bitcoin Surges Past Key Resistance Level', 'url': 'https://www.coindesk.com', 'source': 'CoinDesk', 'sentiment': 'positive'},
                {'title': 'Ethereum Network Upgrade Successfully Deployed', 'url': 'https://cointelegraph.com', 'source': 'Cointelegraph', 'sentiment': 'positive'},
                {'title': 'SEC Announces New Crypto Regulatory Framework', 'url': 'https://www.coindesk.com', 'source': 'CoinDesk', 'sentiment': 'neutral'},
            ]
            self.news_received.emit(news_items)
        except Exception as e:
            self.error_occurred.emit(str(e))

# --- Background Data Fetcher Thread ---
class DataFetcher(QThread):
    data_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    rate_limited = pyqtSignal()

    def run(self):
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 429:
                self.rate_limited.emit()
                return
                
            response.raise_for_status()
            self.data_received.emit(response.json())
        except Exception as e:
            self.error_occurred.emit(str(e))

class VolumeAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"${v/1e9:.1f}B" if v >= 1e9 else f"${v/1e6:.1f}M" for v in values]

# --- Scrolling News Ticker Widget (Highly Visible) ---
class NewsTicker(QWidget):
    def __init__(self):
        super().__init__()
        self.news_items = []
        self.current_index = 0
        self.current_url = '#'
        self.theme = THEMES["Dark Purple"]
        self.scroll_position = 0
        self.scroll_speed = 1.0  
        
        self.setup_ui()
        
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.tick_scroll)
        self.scroll_timer.start(30) 
        
        self.fetch_timer = QTimer()
        self.fetch_timer.timeout.connect(self.fetch_news)
        self.fetch_timer.start(600000)
        
        self.fetch_news()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.container = QWidget()
        self.container.setFixedHeight(45) 
        self.container.setStyleSheet(f"background-color: {self.theme['panel']}; border-bottom: 2px solid {self.theme['accent']};")
        
        self.ticker_label = QLabel("📰 Loading latest crypto news...")
        self.ticker_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.ticker_label.setCursor(Qt.PointingHandCursor)
        self.ticker_label.setParent(self.container)
        self.ticker_label.setMinimumHeight(45)
        
        main_layout.addWidget(self.container)

    def update_theme(self, t):
        self.theme = t
        self.container.setStyleSheet(f"background-color: {self.theme['panel']}; border-bottom: 2px solid {self.theme['accent']};")
        self.display_current_news()

    def update_news(self, news_items):
        self.news_items = news_items
        self.current_index = 0
        if news_items:
            self.display_current_news()

    def display_current_news(self):
        if not self.news_items:
            return
            
        item = self.news_items[self.current_index]
        title = item.get('title', 'No Title')
        source = item.get('source', 'Unknown')
        sentiment = item.get('sentiment', 'neutral')
        
        if sentiment == 'positive':
            color = "#00FF00"  
            emoji = "🟢"
        elif sentiment == 'negative':
            color = "#FF4444"  
            emoji = "🔴"
        else:
            color = self.theme['accent'] 
            emoji = "🟣"
        
        display_text = f"   {emoji}  {source}:  {title}    |    "
        
        self.ticker_label.setText(display_text)
        
        self.ticker_label.setStyleSheet(f"""
            color: {color};
            background-color: transparent;
            font-size: 16px;
            font-weight: bold;
            font-family: Arial, sans-serif;
        """)
        self.current_url = item.get('url', '#')
        
        self.ticker_label.adjustSize()
        
        self.scroll_position = self.container.width()
        self.ticker_label.move(int(self.scroll_position), 0)

    def tick_scroll(self):
        if not self.news_items:
            return
        
        self.scroll_position -= self.scroll_speed
        self.ticker_label.move(int(self.scroll_position), 0)
        
        if self.scroll_position < -self.ticker_label.width():
            self.current_index = (self.current_index + 1) % len(self.news_items)
            self.display_current_news()

    def mousePressEvent(self, event):
        if self.current_url != '#':
            QDesktopServices.openUrl(QUrl(self.current_url))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.container.resize(self.size())
        if self.scroll_position > self.container.width():
            self.scroll_position = self.container.width()
            self.ticker_label.move(int(self.scroll_position), 0)

    def fetch_news(self):
        self.thread = NewsFetcher()
        self.thread.news_received.connect(self.update_news)
        self.thread.start()

# --- Main Application Window ---
class CryptoTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MaMassa Cripto | Trends & Insights")
        self.resize(1200, 750)
        
        self.current_theme_name = load_theme()
        
        self.create_menu_bar()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.header_label = QLabel("MaMassa Cripto")
        main_layout.addWidget(self.header_label)
        
        self.news_ticker = NewsTicker()
        main_layout.addWidget(self.news_ticker)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        content_layout.addWidget(self.tabs)
        
        main_layout.addWidget(content_widget)
        
        self.init_trends_tab()
        self.init_companies_tab()
        self.init_exchanges_tab()
        
        self.apply_theme(self.current_theme_name)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh_all)
        self.timer.start(60000) 
        
        self.fetch_trends()

    def get_header_style(self):
        t = THEMES[self.current_theme_name]
        return f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {t['accent']};
                padding: 15px 30px;
                background-color: {t['bg']};
                border-bottom: 3px solid {t['accent']};
            }}
        """

    def apply_theme(self, theme_name):
        self.current_theme_name = theme_name
        save_theme(theme_name)
        t = THEMES[theme_name]
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_stylesheet(theme_name))
        
        pg.setConfigOption('background', t['graph_bg'])
        pg.setConfigOption('foreground', t['graph_fg'])
        
        if hasattr(self, 'header_label'):
            self.header_label.setStyleSheet(self.get_header_style())
        
        if hasattr(self, 'news_ticker'):
            self.news_ticker.update_theme(t)
        
        if hasattr(self, 'volume_graph'):
            self.volume_graph.setBackground(t['graph_bg'])
            self.volume_graph.getAxis('left').setPen(t['graph_fg'])
            self.volume_graph.getAxis('bottom').setPen(t['graph_fg'])
            self.volume_graph.getAxis('left').setTextPen(t['graph_fg'])
            self.volume_graph.getAxis('bottom').setTextPen(t['graph_fg'])
            self.volume_graph.setTitle(color=t['accent'])
            
        self.update()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        view_menu = menu_bar.addMenu("View")
        theme_menu = QMenu("Themes", self)
        
        for theme_name in THEMES.keys():
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_name: self.apply_theme(t))
            theme_menu.addAction(action)
            
        view_menu.addMenu(theme_menu)
        view_menu.addSeparator()
        
        help_menu = menu_bar.addMenu("Help")
        
        instructions_action = QAction("Instructions", self)
        instructions_action.triggered.connect(self.show_instructions)
        help_menu.addAction(instructions_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About Us", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_instructions(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Instructions - MaMassa Cripto")
        msg.setIcon(QMessageBox.Information)
        msg.setTextFormat(Qt.RichText)
        msg.setText("""
            <h3>How to Use MaMassa Cripto</h3>
            <ul>
                <li><b>🎨 Themes:</b> Go to <b>View > Themes</b> in the top menu to change the app's color scheme. Your choice is saved automatically.</li>
                <li><b>🔒 Security:</b> On first run, create a password (min 8 chars, letters + numbers). You will need this to unlock the app.</li>
                <li><b>📈 Market Trends:</b> View live data for the top 100 cryptocurrencies. Use the search bar to instantly filter by coin name or symbol.</li>
                <li><b>📰 News Ticker:</b> The scrolling bar at the top displays the latest crypto industry news. <b>Click on any headline</b> to open the full article.</li>
                <li><b>🏢 Companies:</b> Browse a comprehensive list of 100+ public companies, miners, and financial institutions with crypto exposure.</li>
                <li><b>🔗 Purchase Sites:</b> View trusted, regulated exchanges. Click "Visit Site" to open their registration pages.</li>
            </ul>
        """)
        msg.exec_()

    def show_about(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("About Us")
        msg.setIcon(QMessageBox.Information)
        msg.setTextFormat(Qt.RichText)
        msg.setText("""
            <h2>MaMassa Cripto</h2>
            <p><b>Version:</b> 1.2.2</p>
            <p>A comprehensive, secure, and modern desktop application for tracking cryptocurrency market trends, corporate holdings, and industry news in real-time.</p>
            <br>
            <p><b>Written by:</b> Arthur Jimmy Garrett & Qwen AI</p>
            <br>
            <p style="font-weight: bold; font-size: 16px; color: #8B5CF6;">© 2024 MaMassa Software</p>
            <hr style="border-color: #33333D; margin: 15px 0;">
            <p style="font-size: 12px; color: #A0A0B0;">
                <b>GNU General Public License Notice:</b><br>
                This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.<br><br>
                This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
            </p>
        """)
        msg.exec_()

    def init_trends_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        top_bar = QHBoxLayout()
        title = QLabel("Live Market Trends (Top 100)")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.auto_refresh_label = QLabel("● Auto-refreshing every 60s")
        self.auto_refresh_label.setObjectName("autoRefreshLabel")
        
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.auto_refresh_label)
        layout.addLayout(top_bar)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search for a specific coin (e.g., Bitcoin, BTC, Ethereum)...")
        self.search_input.textChanged.connect(self.filter_table)
        layout.addWidget(self.search_input)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.trends_table = QTableWidget()
        self.trends_table.setColumnCount(5)
        self.trends_table.setHorizontalHeaderLabels(["Coin", "Price (USD)", "24h Change", "Market Cap", "24h Volume"])
        self.trends_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trends_table.verticalHeader().setVisible(False)
        self.trends_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.volume_graph = pg.PlotWidget(title="Top 10 Coins by 24h Trading Volume")
        self.volume_graph.setLabel('left', 'Volume (USD)', units='$')
        self.volume_graph.showGrid(x=False, y=True, alpha=0.2)
        
        left_axis = VolumeAxis(orientation='left')
        self.volume_graph.setAxisItems({'left': left_axis})
        
        splitter.addWidget(self.trends_table)
        splitter.addWidget(self.volume_graph)
        splitter.setSizes([600, 400]) 
        
        layout.addWidget(splitter)
        
        bottom_bar = QHBoxLayout()
        self.status_label = QLabel("Loading initial data...")
        self.status_label.setObjectName("statusLabel")
        
        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self.fetch_trends)
        
        bottom_bar.addWidget(self.status_label)
        bottom_bar.addStretch()
        bottom_bar.addWidget(refresh_btn)
        layout.addLayout(bottom_bar)
        
        self.tabs.addTab(tab, "📈 Market Trends")

    def filter_table(self, text):
        text = text.lower().strip()
        for row in range(self.trends_table.rowCount()):
            name_item = self.trends_table.item(row, 0)
            if name_item:
                if text in name_item.text().lower():
                    self.trends_table.showRow(row)
                else:
                    self.trends_table.hideRow(row)

    def init_companies_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        top_bar = QHBoxLayout()
        title = QLabel("Public Companies Trading/Holding Crypto (Top 100)")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.company_refresh_label = QLabel("● Synced with auto-refresh")
        self.company_refresh_label.setObjectName("autoRefreshLabel")
        
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.company_refresh_label)
        layout.addLayout(top_bar)
        
        desc = QLabel("Major corporations, miners, and financial institutions with significant cryptocurrency exposure.")
        desc.setObjectName("statusLabel")
        layout.addWidget(desc)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.companies_table = QTableWidget()
        self.companies_table.setColumnCount(4)
        self.companies_table.setHorizontalHeaderLabels(["Company", "Ticker", "Primary Crypto Held", "Est. Holdings / Role"])
        self.companies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.companies_table.verticalHeader().setVisible(False)
        self.companies_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        scroll.setWidget(self.companies_table)
        layout.addWidget(scroll)
        
        self.populate_companies()
        self.tabs.addTab(tab, "🏢 Companies")

    def init_exchanges_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Trusted Platforms to Purchase Crypto")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        desc = QLabel("Sign up on these regulated exchanges to buy, sell, and trade cryptocurrencies
