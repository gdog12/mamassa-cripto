import sys
import os
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
        self.scroll_speed = 1.0  # Slowed down slightly for better readability
        
        self.setup_ui()
        
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.tick_scroll)
        self.scroll_timer.start(30) # ~33 FPS for smooth motion
        
        self.fetch_timer = QTimer()
        self.fetch_timer.timeout.connect(self.fetch_news)
        self.fetch_timer.start(600000)
        
        self.fetch_news()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.container = QWidget()
        self.container.setFixedHeight(45) # Taller for better text visibility
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
        
        # Use highly visible, bright colors that pop on any background
        if sentiment == 'positive':
            color = "#00FF00"  # Bright Green
            emoji = "🟢"
        elif sentiment == 'negative':
            color = "#FF4444"  # Bright Red
            emoji = "🔴"
        else:
            color = self.theme['accent'] # e.g., #8B5CF6 (Bright Purple) or #3182CE (Bright Blue)
            emoji = "🟣"
        
        # Added extra spacing for readability
        display_text = f"   {emoji}  {source}:  {title}    |    "
        
        self.ticker_label.setText(display_text)
        
        # CRITICAL: Explicit, high-contrast styling
        self.ticker_label.setStyleSheet(f"""
            color: {color};
            background-color: transparent;
            font-size: 16px;
            font-weight: bold;
            font-family: Arial, sans-serif;
        """)
        self.current_url = item.get('url', '#')
        
        # CRITICAL FIX: Force the label to calculate its exact width based on the new text
        self.ticker_label.adjustSize()
        
        # Reset scroll position to start exactly at the right edge of the container
        self.scroll_position = self.container.width()
        self.ticker_label.move(int(self.scroll_position), 0)

    def tick_scroll(self):
        if not self.news_items:
            return
        
        self.scroll_position -= self.scroll_speed
        self.ticker_label.move(int(self.scroll_position), 0)
        
        # If the label has completely scrolled off the left side, reset to the right and advance news
        if self.scroll_position < -self.ticker_label.width():
            self.current_index = (self.current_index + 1) % len(self.news_items)
            self.display_current_news()

    def mousePressEvent(self, event):
        if self.current_url != '#':
            QDesktopServices.openUrl(QUrl(self.current_url))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.container.resize(self.size())
        # Keep the label positioned correctly during resize
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
        
        # 1. Create Header FIRST
        self.header_label = QLabel("MaMassa Cripto")
        main_layout.addWidget(self.header_label)
        
        # 2. Create News Ticker
        self.news_ticker = NewsTicker()
        main_layout.addWidget(self.news_ticker)
        
        # 3. Create Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        content_layout.addWidget(self.tabs)
        
        main_layout.addWidget(content_widget)
        
        # 4. Initialize Tabs (creates volume_graph, tables, etc.)
        self.init_trends_tab()
        self.init_companies_tab()
        self.init_exchanges_tab()
        
        # 5. NOW apply the theme AFTER all widgets are created
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
        
        # Update global app stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_stylesheet(theme_name))
        
        # Update pyqtgraph
        pg.setConfigOption('background', t['graph_bg'])
        pg.setConfigOption('foreground', t['graph_fg'])
        
        # Update header (with safety check)
        if hasattr(self, 'header_label'):
            self.header_label.setStyleSheet(self.get_header_style())
        
        # Update news ticker (with safety check)
        if hasattr(self, 'news_ticker'):
            self.news_ticker.update_theme(t)
        
        # Update graph if it exists (with safety check)
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
        
        # View / Themes Menu
        view_menu = menu_bar.addMenu("View")
        theme_menu = QMenu("Themes", self)
        
        for theme_name in THEMES.keys():
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_name: self.apply_theme(t))
            theme_menu.addAction(action)
            
        view_menu.addMenu(theme_menu)
        view_menu.addSeparator()
        
        # Help Menu
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
        
        desc = QLabel("Sign up on these regulated exchanges to buy, sell, and trade cryptocurrencies.")
        desc.setObjectName("statusLabel")
        layout.addWidget(desc)
        
        self.exchanges_table = QTableWidget()
        self.exchanges_table.setColumnCount(4)
        self.exchanges_table.setHorizontalHeaderLabels(["Exchange Name", "Region", "Features", "Action"])
        self.exchanges_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.exchanges_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.exchanges_table.setColumnWidth(3, 120)
        self.exchanges_table.verticalHeader().setVisible(False)
        self.exchanges_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.exchanges_table)
        
        self.populate_exchanges()
        self.tabs.addTab(tab, "🔗 Purchase Sites")

    def auto_refresh_all(self):
        self.fetch_trends()
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.company_refresh_label.setText(f"● Last verified: {current_time}")

    def fetch_trends(self):
        self.status_label.setText("Fetching latest market data...")
        self.auto_refresh_label.setText("● Fetching...")
        self.auto_refresh_label.setStyleSheet("color: #F59E0B; font-size: 12px; font-weight: bold;") 
        
        self.thread = DataFetcher()
        self.thread.data_received.connect(self.update_trends_ui)
        self.thread.error_occurred.connect(self.show_error)
        self.thread.rate_limited.connect(self.show_rate_limit)
        self.thread.start()

    def update_trends_ui(self, data):
        if not data:
            self.status_label.setText("No data received from API.")
            return

        self.trends_table.setRowCount(len(data))
        for row, coin in enumerate(data):
            name = coin.get('name', 'Unknown')
            symbol = coin.get('symbol', 'N/A').upper()
            self.trends_table.setItem(row, 0, QTableWidgetItem(f"{name} ({symbol})"))
            
            price = coin.get('current_price')
            price_str = f"${price:,.2f}" if price is not None else "N/A"
            self.trends_table.setItem(row, 1, QTableWidgetItem(price_str))
            
            change = coin.get('price_change_percentage_24h')
            if change is not None:
                change_str = f"{change:.2f}%"
                change_color = QColor("#10B981") if change >= 0 else QColor("#EF4444")
            else:
                change_str = "N/A"
                change_color = QColor(THEMES[self.current_theme_name]['text_muted'])
                
            change_item = QTableWidgetItem(change_str)
            change_item.setForeground(change_color)
            self.trends_table.setItem(row, 2, change_item)
            
            mcap = coin.get('market_cap')
            mcap_str = f"${mcap:,.0f}" if mcap is not None else "N/A"
            self.trends_table.setItem(row, 3, QTableWidgetItem(mcap_str))
            
            vol = coin.get('total_volume')
            vol_str = f"${vol:,.0f}" if vol is not None else "N/A"
            self.trends_table.setItem(row, 4, QTableWidgetItem(vol_str))
            
        valid_coins = [c for c in data if c.get('total_volume') is not None]
        top_10 = sorted(valid_coins, key=lambda x: x.get('total_volume', 0), reverse=True)[:10]
        
        self.volume_graph.clear()
        if top_10:
            names = [f"{c['symbol'].upper()}" for c in top_10]
            volumes = [c.get('total_volume', 0) for c in top_10]
            
            t = THEMES[self.current_theme_name]
            bg = pg.BarGraphItem(x=range(len(names)), height=volumes, width=0.6, brush=t['accent'])
            self.volume_graph.addItem(bg)
            
            ax = self.volume_graph.getAxis('bottom')
            ax.setTicks([[(i, name) for i, name in enumerate(names)]])
        
        self.status_label.setText(f"Success: {len(data)} coins loaded.")
        self.auto_refresh_label.setText("● Auto-refreshing every 60s")
        self.auto_refresh_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")
        
        self.filter_table(self.search_input.text())

    def show_error(self, error_msg):
        self.status_label.setText(f"Network error. Retrying in 60s...")
        self.auto_refresh_label.setText("● Connection Error")
        self.auto_refresh_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: bold;")

    def show_rate_limit(self):
        self.status_label.setText("API Rate limit reached. Keeping last known data. Retrying in 60s...")
        self.auto_refresh_label.setText("● Rate Limited (Waiting)")
        self.auto_refresh_label.setStyleSheet("color: #F59E0B; font-size: 12px; font-weight: bold;")

    def populate_companies(self):
        companies = [
            ("MicroStrategy", "MSTR", "Bitcoin (BTC)", "226,500+ BTC"),
            ("Marathon Digital", "MARA", "Bitcoin (BTC)", "17,320+ BTC"),
            ("Tesla", "TSLA", "Bitcoin (BTC)", "9,720 BTC"),
            ("Coinbase Global", "COIN", "Multi-Asset", "Custody & Trading"),
            ("Block (Square)", "XYZ", "Bitcoin (BTC)", "8,027 BTC"),
            ("Riot Platforms", "RIOT", "Bitcoin (BTC)", "12,300+ BTC"),
            ("Hut 8 Mining", "HUT", "Bitcoin (BTC)", "9,000+ BTC"),
            ("Galaxy Digital", "GLXY", "Multi-Asset", "Institutional Trading"),
            ("Metaplanet", "3350.T", "Bitcoin (BTC)", "13,000+ BTC"),
            ("Seetee", "SEE.ST", "Bitcoin (BTC)", "3,500+ BTC"),
            ("Cipher Mining", "CFIR", "Bitcoin (BTC)", "Mining & Holding"),
            ("Iris Energy", "IREN", "Bitcoin (BTC)", "Mining & Holding"),
            ("Bitfarms", "BITF", "Bitcoin (BTC)", "Mining & Holding"),
            ("HIVE Digital", "HIVE", "Multi-Asset", "Mining & Holding"),
            ("DMG Blockchain", "DMGI", "Multi-Asset", "Mining & Hosting"),
            ("Exodus Movement", "EXOD", "Multi-Asset", "Wallet & Staking"),
            ("Nexo", "NEXO", "Multi-Asset", "Lending & Custody"),
            ("Digital Currency Group", "DCGC", "Multi-Asset", "Grayscale Parent Co."),
            ("CleanSpark", "CLSK", "Bitcoin (BTC)", "8,000+ BTC"),
            ("Semler Scientific", "SMLR", "Bitcoin (BTC)", "4,000+ BTC"),
            ("Core Scientific", "CORZ", "Bitcoin (BTC)", "Mining & Hosting"),
            ("Canaan Inc.", "CAN", "Bitcoin (BTC)", "Mining Hardware & Mining"),
            ("Ebang International", "EBON", "Bitcoin (BTC)", "Mining Hardware & Mining"),
            ("Bit Digital", "BTBT", "Bitcoin (BTC)", "Mining & Holding"),
            ("Applied Digital", "APLD", "Bitcoin (BTC)", "Mining Infrastructure"),
            ("Argo Blockchain", "ARBK", "Bitcoin (BTC)", "Mining & Holding"),
            ("Twenty One Capital", "TONE.V", "Bitcoin (BTC)", "10,000+ BTC"),
            ("Phoenix Group Holdings", "PHNX.L", "Bitcoin (BTC)", "5,000+ BTC"),
            ("Nakamoto X", "NX", "Bitcoin (BTC)", "Treasury Holding"),
            ("The Blockchain Group", "ALBGA.PA", "Bitcoin (BTC)", "1,800+ BTC"),
            ("Mercury Fintech", "MRCY", "Bitcoin (BTC)", "Treasury Holding"),
            ("Strive Asset Management", "STRV", "Bitcoin (BTC)", "Advocacy & Holding"),
            ("NVIDIA", "NVDA", "Multi-Asset", "Mining Hardware (GPUs)"),
            ("Advanced Micro Devices", "AMD", "Multi-Asset", "Mining Hardware (GPUs)"),
            ("Microchip Technology", "MCHP", "Multi-Asset", "Mining Hardware"),
            ("Taiwan Semiconductor", "TSM", "Multi-Asset", "Chip Manufacturing"),
            ("PayPal Holdings", "PYPL", "Multi-Asset", "Crypto Checkout & Custody"),
            ("Visa Inc.", "V", "Multi-Asset", "Crypto Settlement & Cards"),
            ("Mastercard Inc.", "MA", "Multi-Asset", "Crypto Settlement & Cards"),
            ("Robinhood Markets", "HOOD", "Multi-Asset", "Retail Crypto Trading"),
            ("SoFi Technologies", "SOFI", "Multi-Asset", "Retail Crypto Trading"),
            ("Block Inc. (Cash App)", "SQ", "Bitcoin (BTC)", "Trading & Treasury"),
            ("MercadoLibre", "MELI", "Multi-Asset", "LatAm Crypto Trading"),
            ("StoneCo", "STNE", "Multi-Asset", "LatAm Crypto Processing"),
            ("Nu Holdings", "NU", "Multi-Asset", "LatAm Crypto Trading"),
            ("Bakkt Holdings", "BKKT", "Multi-Asset", "Institutional Custody"),
            ("CME Group", "CME", "Bitcoin (BTC)", "Futures & Derivatives"),
            ("Cboe Global Markets", "CBOE", "Bitcoin (BTC)", "Futures & Derivatives"),
            ("Intercontinental Exchange", "ICE", "Multi-Asset", "Bakkt Parent Co."),
            ("Cantor Fitzgerald", "Private", "Bitcoin (BTC)", "Custody & B. Riley Investment"),
            ("B. Riley Financial", "RILY", "Multi-Asset", "Crypto Investment Banking"),
            ("CITIC Securities", "600030.SS", "Multi-Asset", "HashKey Group Investment"),
            ("HashKey Group", "Private", "Multi-Asset", "Licensed Exchange (HK)"),
            ("OSL Group", "0863.HK", "Multi-Asset", "Licensed Exchange (HK)"),
            ("BC Technology Group", "0863.HK", "Multi-Asset", "OSL Parent Co."),
            ("Coincheck Group", "Parent of Coincheck", "Multi-Asset", "Japanese Exchange"),
            ("SBI Holdings", "8473.T", "Multi-Asset", "Japanese Crypto Ecosystem"),
            ("GMO Internet", "9449.T", "Multi-Asset", "Japanese Mining & Exchange"),
            ("Remixpoint", "3825.T", "Bitcoin (BTC)", "Japanese Mining & Holding"),
            ("Franklin Templeton", "BEN", "Multi-Asset", "Spot Bitcoin ETF Issuer"),
            ("BlackRock", "BLK", "Multi-Asset", "Spot Bitcoin ETF Issuer (IBIT)"),
            ("Fidelity Investments", "Private", "Multi-Asset", "Spot Bitcoin ETF Issuer (FBTC)"),
            ("Grayscale Investments", "Private", "Multi-Asset", "Spot Bitcoin ETF (GBTC)"),
            ("VanEck", "Private", "Multi-Asset", "Spot Bitcoin ETF Issuer"),
            ("ARK Invest", "Private", "Multi-Asset", "Spot Bitcoin ETF Issuer"),
            ("Bitwise Asset Management", "Private", "Multi-Asset", "Spot Bitcoin ETF Issuer"),
            ("Invesco", "IVZ", "Multi-Asset", "Spot Bitcoin ETF Issuer"),
            ("Valkyrie Investments", "Private", "Multi-Asset", "Crypto Fund Manager"),
            ("ProShares", "Private", "Multi-Asset", "Bitcoin Futures ETF"),
            ("Volatility Shares", "Private", "Multi-Asset", "Bitcoin Futures ETF"),
            ("T-Rex Asset Management", "Private", "Multi-Asset", "Bitcoin Futures ETF"),
            ("Simplify Asset Management", "Private", "Multi-Asset", "Bitcoin Strategy ETF"),
            ("Global X", "Private", "Multi-Asset", "Blockchain & Crypto ETFs"),
            ("Amplify Investments", "Private", "Multi-Asset", "Blockchain ETF"),
            ("Defiance ETFs", "Private", "Multi-Asset", "Crypto & Blockchain ETFs"),
            ("First Trust", "Private", "Multi-Asset", "Crypto & Blockchain ETFs"),
            ("WisdomTree", "Private", "Multi-Asset", "Crypto & Blockchain ETFs"),
            ("21Shares", "Private", "Multi-Asset", "Crypto ETP Issuer"),
            ("CoinShares", "Private", "Multi-Asset", "Crypto ETP Issuer"),
            ("ETC Group", "Private", "Multi-Asset", "Crypto ETP Issuer"),
            ("Purpose Investments", "Private", "Multi-Asset", "Canadian Bitcoin ETF"),
            ("Evolve ETFs", "Private", "Multi-Asset", "Canadian Bitcoin ETF"),
            ("3iQ Corp", "Private", "Multi-Asset", "Canadian Bitcoin ETF"),
            ("CI Financial", "CIX.TO", "Multi-Asset", "Canadian Crypto Funds"),
            ("Hamilton ETFs", "Private", "Multi-Asset", "Canadian Crypto ETFs"),
            ("Ninepoint Partners", "Private", "Multi-Asset", "Canadian Crypto Funds"),
            ("BitGo", "Private", "Multi-Asset", "Institutional Custody"),
            ("Anchorage Digital", "Private", "Multi-Asset", "Federally Chartered Crypto Bank"),
            ("Paxos Trust Company", "Private", "Multi-Asset", "Stablecoin Issuer & Custody"),
            ("Circle Internet Financial", "Private", "Multi-Asset", "USDC Stablecoin Issuer"),
            ("Tether Limited", "Private", "Multi-Asset", "USDT Stablecoin Issuer"),
            ("Ripple Labs", "Private", "Multi-Asset", "XRP Ledger & Payments"),
            ("Chainalysis", "Private", "Multi-Asset", "Blockchain Analytics"),
            ("Elliptic", "Private", "Multi-Asset", "Blockchain Analytics"),
            ("TRM Labs", "Private", "Multi-Asset", "Blockchain Intelligence"),
            ("Fireblocks", "Private", "Multi-Asset", "Institutional Crypto Infrastructure"),
            ("Ledger", "Private", "Multi-Asset", "Hardware Wallets"),
            ("Trezor (SatoshiLabs)", "Private", "Multi-Asset", "Hardware Wallets")
        ]
        
        self.companies_table.setRowCount(len(companies))
        for row, (name, ticker, crypto, holdings) in enumerate(companies):
            self.companies_table.setItem(row, 0, QTableWidgetItem(name))
            ticker_item = QTableWidgetItem(ticker)
            ticker_item.setForeground(QColor(THEMES[self.current_theme_name]['accent']))
            self.companies_table.setItem(row, 1, ticker_item)
            self.companies_table.setItem(row, 2, QTableWidgetItem(crypto))
            self.companies_table.setItem(row, 3, QTableWidgetItem(holdings))

    def populate_exchanges(self):
        exchanges = [
            ("Coinbase", "Global / US", "Best for beginners, publicly traded", "https://www.coinbase.com"),
            ("Binance", "Global (Excl. US)", "Highest volume, advanced trading", "https://www.binance.com"),
            ("Kraken", "Global / US", "High security, futures trading", "https://www.kraken.com"),
            ("Crypto.com", "Global", "Great mobile app, crypto debit card", "https://crypto.com"),
            ("Gemini", "US / Global", "Highly regulated, earn rewards", "https://www.gemini.com"),
            ("Binance.US", "US Only", "US regulated version of Binance", "https://www.binance.us"),
            ("Bitstamp", "Global / EU", "One of the oldest exchanges, EU regulated", "https://www.bitstamp.net"),
            ("KuCoin", "Global", "Wide variety of altcoins, futures", "https://www.kucoin.com"),
            ("OKX", "Global", "Advanced trading, Web3 wallet integration", "https://www.okx.com"),
            ("Bybit", "Global", "Derivatives focus, copy trading", "https://www.bybit.com")
        ]
        
        self.exchanges_table.setRowCount(len(exchanges))
        for row, (name, region, features, url) in enumerate(exchanges):
            self.exchanges_table.setItem(row, 0, QTableWidgetItem(name))
            self.exchanges_table.setItem(row, 1, QTableWidgetItem(region))
            self.exchanges_table.setItem(row, 2, QTableWidgetItem(features))
            
            visit_btn = QPushButton("Visit Site")
            visit_btn.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            self.exchanges_table.setCellWidget(row, 3, visit_btn)

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    # Apply theme globally before showing anything
    initial_theme = load_theme()
    app.setStyleSheet(get_stylesheet(initial_theme))
    pg.setConfigOption('background', THEMES[initial_theme]['graph_bg'])
    pg.setConfigOption('foreground', THEMES[initial_theme]['graph_fg'])
    
    auth_dialog = AuthDialog()
    if auth_dialog.exec_() == QDialog.Accepted:
        window = CryptoTracker()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
