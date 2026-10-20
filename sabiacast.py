import os
import sys
import socket
import ssl
import threading
import requests
import subprocess 
import time
import base64
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import streamlink
import vlc
import re
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QLineEdit, QTextBrowser, QLabel,
    QSplitter, QInputDialog, QMessageBox, QFrame, QListWidgetItem,
    QTabWidget, QToolButton, QGridLayout, QScrollArea,
    QDialog, QDialogButtonBox, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QByteArray, QSize
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QPixmap, QIcon

# Credenciais Twitch — cada pessoa entra com a própria conta (ver README).
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".twitch_app_credentials.json")

CLIENT_ID = None
ACCESS_TOKEN = None
HEADERS = {}

def load_saved_credentials():
    """Lê credenciais salvas localmente (se a pessoa já logou antes nesta máquina)."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return data.get("client_id"), data.get("access_token")
        except Exception:
            pass
    return None, None

def save_credentials(client_id, access_token):
    try:
        descriptor = os.open(CONFIG_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as f:
            os.chmod(CONFIG_PATH, 0o600)
            json.dump({"client_id": client_id, "access_token": access_token}, f)
    except Exception:
        pass

def apply_credentials(client_id, access_token):
    """Aplica as credenciais desta sessão (usadas por todas as chamadas de API/IRC)."""
    global CLIENT_ID, ACCESS_TOKEN
    CLIENT_ID = client_id
    ACCESS_TOKEN = access_token
    HEADERS.clear()
    HEADERS.update({
        "Authorization": f"Bearer {access_token}",
        "Client-Id": client_id
    })

def clear_saved_credentials():
    try:
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
    except Exception:
        pass

IRC_SERVER = "irc.chat.twitch.tv"
IRC_PORT = 6697

EMOTE_MAP = {
    "Pog": "😮", "PogChamp": "😮", "LUL": "🤣", "LULW": "🤣",
    "Kappa": "😏", "KAPPA": "😏", "Kreygasm": "🤤", "BibleThump": "😭",
    "NotLikeThis": "🙈", "WutFace": "😱", "ResidentSleeper": "😴",
    "<3": "💜", ":)": "😊", ":(": "🙁", ";)": "😜"
}

# TELA DE LOGIN — cada pessoa entra com o próprio Client ID / Access Token
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Entrar na Twitch")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Pra usar o app, você precisa do teu próprio Client ID e Access Token "
            "(cada pessoa usa a própria conta — nada é compartilhado)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_get_token = QPushButton("🌐 Gerar meu token (abre no navegador)")
        btn_get_token.clicked.connect(
            lambda: webbrowser.open("https://twitchtokengenerator.com/")
        )
        layout.addWidget(btn_get_token)

        layout.addWidget(QLabel("Client ID:"))
        self.input_client_id = QLineEdit()
        layout.addWidget(self.input_client_id)

        layout.addWidget(QLabel("Access Token:"))
        self.input_token = QLineEdit()
        self.input_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_token)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_accept(self):
        client_id = self.input_client_id.text().strip()
        token = self.input_token.text().strip()
        if not client_id or not token:
            QMessageBox.warning(self, "Faltou algo", "Preencha o Client ID e o Access Token.")
            return
        apply_credentials(client_id, token)
        save_credentials(client_id, token)
        self.accept()

# GERENCIADOR DE EMOTES COM BASE64 (100% COMPATÍVEL COM QTEXTBROWSER)
class EmoteManager:
    """
    Gerencia emotes de forma 100% assíncrona:
    - add_emotes() só registra URLs e dispara download em background (não bloqueia a UI/chat)
    - get_emote_html() é chamado no caminho de cada mensagem e faz apenas um dict.get()
      (zero I/O, zero rede) -> não introduz delay no chat mesmo com centenas de emotes.
    - Também categoriza cada emote (usável / do canal X / global) pra alimentar as
      abas do seletor, sem afetar a exibição no chat (que sempre usa o dicionário todo).
    """
    def __init__(self):
        self.cache_dir = "emotes_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.local_emotes = {}
        self.usable = set()              # nomes que ESTA conta pode de fato usar (aba "Meus")
        self.global_names = set()        # nomes globais (Twitch/BTTV/FFZ/7TV) (aba "Global")
        self.channel_names = {}          # {canal: set(nomes)} — específicos de cada canal (aba "Canal")
        self._known = set()              # nomes já baixados (evita re-download)
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=8)

    def add_emotes(self, emote_urls: dict, category: str = "global", channel: str = None):
        """Registra um lote de emotes, marca a categoria (pras abas do seletor)
        e baixa em paralelo só o que ainda não tinha sido baixado."""
        with self._lock:
            for name in emote_urls:
                if category == "usable":
                    self.usable.add(name)
                elif category == "channel" and channel:
                    self.channel_names.setdefault(channel, set()).add(name)
                else:
                    self.global_names.add(name)

        novos = {}
        with self._lock:
            for name, url in emote_urls.items():
                if name not in self._known:
                    self._known.add(name)
                    novos[name] = url

        for name, url in novos.items():
            self._executor.submit(self._download_one, name, url)

    def _download_one(self, name, url):
        ext = ".webp" if url.endswith(".webp") else ".png"
        filepath = os.path.join(self.cache_dir, f"{name}{ext}")
        try:
            if not os.path.exists(filepath):
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)

            if os.path.exists(filepath):
                mime = "image/webp" if ext == ".webp" else "image/png"
                with open(filepath, 'rb') as f:
                    b64_data = base64.b64encode(f.read()).decode('utf-8')
                    with self._lock:
                        self.local_emotes[name] = f"data:{mime};base64,{b64_data}"
        except Exception:
            pass

    def get_emote_html(self, word):
        """Chamado por mensagem recebida. Só leitura de dict -> sem custo perceptível."""
        data_uri = self.local_emotes.get(word)
        if data_uri:
            return f'<img src="{data_uri}" width="28" height="28" align="middle">'
        return None

# Instancia o gerenciador
emote_manager = EmoteManager()
_global_emotes_loaded = False  # evita repetir a chamada de emotes globais a cada aba aberta

# ESTILO VISUAL DA INTERFACE (QSS / STYLESHEET) — Tema roxo-azulado, cantos macios
AURORA_THEME_STYLE = """
QMainWindow {
    background-color: #14121f;
}
QWidget {
    background-color: #14121f;
    color: #e8e6f5;
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}
QListWidget {
    background-color: #1c1a2e;
    border: 1px solid #2c294a;
    border-radius: 16px;
    padding: 8px;
    outline: none;
}
QListWidget::item {
    background-color: #201e38;
    border-radius: 14px;
    padding: 10px;
    margin-bottom: 6px;
    color: #e8e6f5;
}
QListWidget::item:hover {
    background-color: #2a2750;
}
QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c5cfc, stop:1 #4c6fff);
    color: #ffffff;
    font-weight: bold;
}
QPushButton, QToolButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c5cfc, stop:1 #4c6fff);
    color: #ffffff;
    border: none;
    border-radius: 16px;
    padding: 9px 16px;
    font-weight: bold;
}
QPushButton:hover, QToolButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8f72ff, stop:1 #6688ff);
}
QPushButton:pressed, QToolButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6640d9, stop:1 #3555d9);
}
QPushButton#iconButton {
    padding: 0px;
    border-radius: 17px;
    font-size: 15px;
}
QLineEdit {
    background-color: #201e38;
    border: 1px solid #3a3762;
    border-radius: 16px;
    padding: 9px 14px;
    color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #7c5cfc;
}
QTextBrowser {
    background-color: #1c1a2e;
    border: 1px solid #2c294a;
    border-radius: 16px;
    padding: 10px;
}
QSplitter::handle {
    background-color: #14121f;
    width: 6px;
}
QTabWidget::pane {
    border: 1px solid #2c294a;
    border-radius: 16px;
    background-color: #14121f;
}
QTabBar::tab {
    background-color: #1c1a2e;
    color: #cfcbe8;
    padding: 9px 18px;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    margin-right: 4px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c5cfc, stop:1 #4c6fff);
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #2a2750;
}
QLabel {
    background-color: transparent;
}
QLabel#shortcutsBar {
    color: #8b87b8;
    font-size: 11px;
    padding: 8px 4px;
    border-top: 1px solid #2c294a;
    margin-top: 4px;
}
QWidget#emotePickerPopup {
    background-color: #201e38;
    border: 1px solid #3a3762;
    border-radius: 14px;
}
QScrollBar:vertical {
    background: #1c1a2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #4c6fff;
    border-radius: 5px;
    min-height: 20px;
}
"""

# COMPONENTE DE VÍDEO COM DUPLO CLIQUE
class VideoFrame(QFrame):
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

# FUNÇÕES DA API DA TWITCH
def get_my_info():
    try:
        res = requests.get("https://api.twitch.tv/helix/users", headers=HEADERS).json()
        if "data" in res and res["data"]:
            return res["data"][0]["id"], res["data"][0]["login"], res["data"][0]["display_name"]
    except Exception as e:
        print(f"Erro na API da Twitch: {e}")
    return None, None, None

def get_followed_streams(user_id):
    try:
        res = requests.get(f"https://api.twitch.tv/helix/streams/followed?user_id={user_id}", headers=HEADERS).json()
        return res.get("data", [])
    except:
        return []

def search_channels(query):
    try:
        res = requests.get(f"https://api.twitch.tv/helix/search/channels?query={query}&live_only=true", headers=HEADERS).json()
        return res.get("data", [])
    except:
        return []

def get_user_id_by_login(login):
    try:
        res = requests.get(f"https://api.twitch.tv/helix/users?login={login}", headers=HEADERS).json()
        data = res.get("data", [])
        return data[0]["id"] if data else None
    except Exception:
        return None

def _parse_emote_images(entries):
    """Converte a resposta da Helix (chat/emotes) em {nome: url}."""
    parsed = {}
    for e in entries:
        images = e.get("images", {})
        url = images.get("url_2x") or images.get("url_1x") or images.get("url_4x")
        if url and e.get("name"):
            parsed[e["name"]] = url
    return parsed

def get_global_emotes():
    """Emotes globais da Twitch (Kappa, PogChamp, etc.) — 1 chamada, sem depender de canal."""
    try:
        res = requests.get("https://api.twitch.tv/helix/chat/emotes/global", headers=HEADERS).json()
        return _parse_emote_images(res.get("data", []))
    except Exception:
        return {}

def get_channel_emotes(broadcaster_id):
    """Emotes específicos do canal (sub emotes, bits emotes, etc) — TODOS, independente de quem está vendo.
    Usado só pra RENDERIZAR emotes de outras pessoas no chat."""
    try:
        res = requests.get(
            f"https://api.twitch.tv/helix/chat/emotes?broadcaster_id={broadcaster_id}",
            headers=HEADERS
        ).json()
        return _parse_emote_images(res.get("data", []))
    except Exception:
        return {}

def get_user_emotes(user_id):
    """Emotes que ESTA conta pode de fato usar (globais + follower/sub/bits que já são seus).
    Usado só pra popular o SELETOR de emote — não afeta a exibição no chat."""
    result = {}
    cursor = None
    try:
        while True:
            url = f"https://api.twitch.tv/helix/chat/emotes/user?user_id={user_id}"
            if cursor:
                url += f"&after={cursor}"
            res = requests.get(url, headers=HEADERS).json()
            template = res.get("template", "")
            for e in res.get("data", []):
                name, eid = e.get("name"), e.get("id")
                if not name or not eid or not template:
                    continue
                url_emote = (template
                             .replace("{{id}}", eid)
                             .replace("{{format}}", "static")
                             .replace("{{theme_mode}}", "dark")
                             .replace("{{scale}}", "2.0"))
                result[name] = url_emote
            cursor = res.get("pagination", {}).get("cursor")
            if not cursor:
                break
    except Exception:
        pass
    return result

# --- Fontes de terceiros (BetterTTV / FrankerFaceZ / 7TV) ---
def get_bttv_global_emotes():
    try:
        res = requests.get("https://api.betterttv.net/3/cached/emotes/global", timeout=5).json()
        return {
            e["code"]: f"https://cdn.betterttv.net/emote/{e['id']}/2x"
            for e in res if e.get("code") and e.get("id")
        }
    except Exception:
        return {}

def get_bttv_channel_emotes(broadcaster_id):
    try:
        res = requests.get(f"https://api.betterttv.net/3/cached/users/twitch/{broadcaster_id}", timeout=5).json()
        emotes = {}
        for e in res.get("channelEmotes", []) + res.get("sharedEmotes", []):
            if e.get("code") and e.get("id"):
                emotes[e["code"]] = f"https://cdn.betterttv.net/emote/{e['id']}/2x"
        return emotes
    except Exception:
        return {}

def _parse_ffz_sets(sets_dict):
    emotes = {}
    for s in sets_dict.values():
        for e in s.get("emoticons", []):
            urls = e.get("urls", {})
            url = urls.get("2") or urls.get("1") or urls.get("4")
            if url and e.get("name"):
                emotes[e["name"]] = "https:" + url if url.startswith("//") else url
    return emotes

def get_ffz_global_emotes():
    try:
        res = requests.get("https://api.frankerfacez.com/v1/set/global", timeout=5).json()
        return _parse_ffz_sets(res.get("sets", {}))
    except Exception:
        return {}

def get_ffz_channel_emotes(channel_login):
    try:
        res = requests.get(f"https://api.frankerfacez.com/v1/room/{channel_login}", timeout=5).json()
        return _parse_ffz_sets(res.get("sets", {}))
    except Exception:
        return {}

def _parse_7tv_emotes(entries):
    emotes = {}
    for e in entries:
        name = e.get("name")
        host = (e.get("data") or {}).get("host") or {}
        files = host.get("files", [])
        base = host.get("url", "")
        if not name or not base or not files:
            continue
        chosen = next((f for f in files if f.get("name", "").startswith("2x")), files[0])
        url = f"https:{base}/{chosen['name']}" if base.startswith("//") else f"{base}/{chosen['name']}"
        emotes[name] = url
    return emotes

def get_7tv_global_emotes():
    try:
        res = requests.get("https://7tv.io/v3/emote-sets/global", timeout=5).json()
        return _parse_7tv_emotes(res.get("emotes", []))
    except Exception:
        return {}

def get_7tv_channel_emotes(broadcaster_id):
    try:
        res = requests.get(f"https://7tv.io/v3/users/twitch/{broadcaster_id}", timeout=5).json()
        emote_set = res.get("emote_set") or {}
        return _parse_7tv_emotes(emote_set.get("emotes", []))
    except Exception:
        return {}

# CLIENTE IRC
class ChatSignals(QObject):
    message_received = pyqtSignal(str, str)
    status_changed = pyqtSignal(str)

class IRCClient:
    def __init__(self, channel_name, user_login, signals):
        self.channel_name = channel_name.lower()
        self.user_login = user_login.lower()
        self.signals = signals
        self.socket = None
        self.running = False

    def start(self):
        try:
            raw_socket = socket.create_connection((IRC_SERVER, IRC_PORT), timeout=10)
            try:
                self.socket = ssl.create_default_context().wrap_socket(
                    raw_socket, server_hostname=IRC_SERVER)
            except Exception:
                raw_socket.close()
                raise
        except Exception as e:
            self.signals.status_changed.emit(f"Erro de conexão: {e}")
            return

        self.socket.sendall(f"PASS oauth:{ACCESS_TOKEN}\r\n".encode("utf-8"))
        self.socket.sendall(f"NICK {self.user_login}\r\n".encode("utf-8"))
        self.socket.sendall(f"JOIN #{self.channel_name}\r\n".encode("utf-8"))

        self.running = True
        self.signals.status_changed.emit(f"💬 Chat conectado")
        threading.Thread(target=self._receive, daemon=True).start()

    def _receive(self):
        while self.running:
            try:
                self.socket.settimeout(1.0)
                resp = self.socket.recv(2048).decode("utf-8", errors="ignore")
                if not resp:
                    break
                lines = resp.split("\r\n")
                for line in lines:
                    if not line:
                        continue
                    if line.startswith("PING"):
                        self.socket.sendall("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                    elif "PRIVMSG" in line:
                        parts = line.split("PRIVMSG", 1)
                        user = parts[0].split("!")[0].lstrip(":")
                        msg = parts[1].split(":", 1)[1] if ":" in parts[1] else ""
                        self.signals.message_received.emit(user, msg)
            except socket.timeout:
                continue
            except:
                break

    def send_message(self, msg):
        if self.socket and self.running:
            self.socket.sendall(f"PRIVMSG #{self.channel_name} :{msg}\r\n".encode("utf-8"))

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

# SELETOR DE EMOTE — abas (Meus/Canal/Global) + busca, num popup próprio
class EmotePickerPopup(QWidget):
    def __init__(self, channel_name, on_pick):
        super().__init__(None, Qt.WindowType.Popup)
        self.setObjectName("emotePickerPopup")
        self.channel_name = channel_name.lower()
        self.on_pick = on_pick
        
        # Define um tamanho mínimo confortável em vez de fixo estrito
        self.setMinimumWidth(390)
        self.setMaximumHeight(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar emote...")
        self.search.textChanged.connect(self.refresh)
        layout.addWidget(self.search)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.refresh)
        layout.addWidget(self.tabs)

        self.scroll_areas = {}
        for label in ("Meus", "Canal", "Global"):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none; background: transparent;")
            self.tabs.addTab(scroll, label)
            self.scroll_areas[label] = scroll

        self.refresh()
        
    def _names_for_current_tab(self):
        label = self.tabs.tabText(self.tabs.currentIndex())
        if label == "Meus":
            return emote_manager.usable
        elif label == "Canal":
            return emote_manager.channel_names.get(self.channel_name, set())
        return emote_manager.global_names

    def refresh(self):
        names = self._names_for_current_tab()
        query = self.search.text().strip().lower()

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(4)

        items = [
            (name, emote_manager.local_emotes[name])
            for name in sorted(names)
            if name in emote_manager.local_emotes and (not query or query in name.lower())
        ]

        if not items:
            grid.addWidget(QLabel("Nada aqui ainda..."), 0, 0)
        else:
            cols = 5  # Limitado a 5 colunas para encaixar perfeitamente sem scroll horizontal
            for idx, (name, data_uri) in enumerate(items):
                btn = QToolButton()
                btn.setIconSize(QSize(28, 28))
                btn.setToolTip(name)
                btn.setAutoRaise(True)
                try:
                    _, b64data = data_uri.split(",", 1)
                    pixmap = QPixmap()
                    pixmap.loadFromData(QByteArray.fromBase64(b64data.encode("utf-8")))
                    btn.setIcon(QIcon(pixmap))
                except Exception:
                    btn.setText(name[:3])
                btn.clicked.connect(lambda checked, n=name: self._pick(n))
                grid.addWidget(btn, idx // cols, idx % cols)

        current_scroll = self.tabs.currentWidget()
        current_scroll.setWidget(container)

    def _pick(self, name):
        self.on_pick(name)
        self.close()

class PictureWindow(QWidget):
    """Janela leve que recebe o mesmo vídeo, sem outra reprodução."""
    def __init__(self, tab):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.tab = tab
        self.setWindowTitle(f"{tab.channel_name} — Picture-in-picture")
        self.resize(640, 360)
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(0, 0, 0, 0)
        button = QPushButton("Voltar à aba (Esc)")
        button.clicked.connect(self.close)
        self.box.addWidget(button)
        shortcut = QShortcut(QKeySequence("Escape"), self)
        shortcut.activated.connect(self.close)

    def closeEvent(self, event):
        self.tab.restore_video()
        event.accept()


# WIDGET DE UMA ABA DE STREAM
class StreamTab(QWidget):
    def __init__(self, channel_name, user_login, display_name, parent_window):
        super().__init__()
        self.channel_name = channel_name
        self.user_login = user_login
        self.display_name = display_name
        self.parent_window = parent_window
        
        self.streamlink_process = None # Segura o processo em segundo plano
        self.user_muted = False
        self.focus_muted = False
        self.volume = 100
        self.pip_window = None

        # O proxy é local, mas os dados ainda chegam da rede: reserve buffer
        # para oscilações e mantenha a sincronização padrão de áudio/vídeo.
        vlc_options = [
            "--network-caching=1000",
            "--live-caching=1000"
        ]
        self.vlc_instance = vlc.Instance(vlc_options)
        self.media_player = self.vlc_instance.media_player_new()

        self.chat_signals = ChatSignals()
        self.chat_signals.message_received.connect(self.display_chat_message)
        self.chat_signals.status_changed.connect(self.update_status)
        self.irc_client = None

        self.init_ui()
        self.start_stream_and_chat()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Player de Vídeo
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        self.video_layout = video_layout
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_frame = VideoFrame()
        self.video_frame.setStyleSheet("background-color: #000000; border-radius: 16px;")
        self.video_frame.double_clicked.connect(self.parent_window.toggle_fullscreen)
        video_layout.addWidget(self.video_frame)
        controls = QHBoxLayout()
        self.mute_button = QPushButton("Som")
        self.mute_button.setCheckable(True)
        self.mute_button.setToolTip("Silenciar esta aba (Ctrl+M)")
        self.mute_button.toggled.connect(self.set_user_muted)
        controls.addWidget(self.mute_button)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.setToolTip("Volume desta aba (Ctrl+↑ / Ctrl+↓)")
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls.addWidget(self.volume_slider)
        self.volume_label = QLabel("100%")
        controls.addWidget(self.volume_label)
        for title, callback in [("Cinema", self.parent_window.toggle_cinema),
                                ("PiP", self.toggle_pip),
                                ("Tela cheia", self.parent_window.toggle_fullscreen)]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            controls.addWidget(button)
        video_layout.addLayout(controls)

        splitter.addWidget(video_container)

        # Conectar VLC ao Widget
        if sys.platform.startswith("linux"):
            self.media_player.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.media_player.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.video_frame.winId()))

        # Chat
        chat_widget = QWidget()
        self.chat_widget = chat_widget
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(6)

        status_row = QHBoxLayout()

        self.lbl_chat_status = QLabel(f"Carregando #{self.channel_name}...")
        self.lbl_chat_status.setStyleSheet("font-weight: bold; color: #adadb8;")
        status_row.addWidget(self.lbl_chat_status)

        status_row.addStretch()

        self.btn_subscribe = QPushButton("💜 Assinar canal")
        self.btn_subscribe.setToolTip("Abre a página de assinatura no navegador")
        self.btn_subscribe.clicked.connect(self.open_subscribe_page)
        status_row.addWidget(self.btn_subscribe)

        chat_layout.addLayout(status_row)

        self.chat_display = QTextBrowser()
        chat_layout.addWidget(self.chat_display)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.btn_emote = QToolButton()
        self.btn_emote.setText("😊")
        self.btn_emote.setToolTip("Escolher emote")
        self.btn_emote.clicked.connect(self.open_emote_picker)
        input_row.addWidget(self.btn_emote)

        self.input_chat = QLineEdit()
        self.input_chat.setPlaceholderText("Enviar mensagem...")
        self.input_chat.returnPressed.connect(self.send_chat_message)
        input_row.addWidget(self.input_chat)

        chat_layout.addLayout(input_row)

        splitter.addWidget(chat_widget)
        splitter.setSizes([900, 320])

        layout.addWidget(splitter)

    def get_free_port(self):
        """Encontra uma porta de rede livre no seu PC para o Streamlink rodar"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def start_stream_and_chat(self):
        threading.Thread(target=self._resolve_and_play, daemon=True).start()
        threading.Thread(target=self._load_channel_emotes, daemon=True).start()
        self.irc_client = IRCClient(self.channel_name, self.user_login, self.chat_signals)
        self.irc_client.start()

    def _load_channel_emotes(self):
        """Busca emotes globais (1x por app) + do canal desta aba, em background.
        Não afeta o chat: só popula o dicionário que o get_emote_html() já lê,
        e categoriza (global/canal) pra alimentar as abas do seletor."""
        global _global_emotes_loaded
        if not _global_emotes_loaded:
            emote_manager.add_emotes(get_global_emotes(), category="global")
            emote_manager.add_emotes(get_bttv_global_emotes(), category="global")
            emote_manager.add_emotes(get_ffz_global_emotes(), category="global")
            emote_manager.add_emotes(get_7tv_global_emotes(), category="global")
            _global_emotes_loaded = True

        channel = self.channel_name.lower()
        broadcaster_id = get_user_id_by_login(self.channel_name)
        if broadcaster_id:
            emote_manager.add_emotes(get_channel_emotes(broadcaster_id), category="channel", channel=channel)
            emote_manager.add_emotes(get_bttv_channel_emotes(broadcaster_id), category="channel", channel=channel)
            emote_manager.add_emotes(get_7tv_channel_emotes(broadcaster_id), category="channel", channel=channel)
        emote_manager.add_emotes(get_ffz_channel_emotes(channel), category="channel", channel=channel)

    def _resolve_and_play(self):
        try:
            url = f"https://www.twitch.tv/{self.channel_name}"
            port = self.get_free_port()
            
            # Comando CLI para o Streamlink puxar a live em baixa latência real
            cmd = [
                sys.executable, "-m", "streamlink",
                "--twitch-low-latency",
                "--player-external-http",
                f"--player-external-http-port={port}",
                url,
                "best,720p60,low" # Tenta best, se não achar, cai para as outras
            ]

            # Oculta a janela preta do terminal no Windows (se estiver usando)
            kwargs = {}
            if sys.platform == "win32":
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            # Inicia o proxy local do Streamlink
            self.streamlink_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **kwargs
            )

            # Dá 2 segundos pro proxy do Streamlink ligar e criar o link local
            time.sleep(2)
            
            # Conecta o VLC ao proxy que o Streamlink acabou de criar
            stream_url = f"http://127.0.0.1:{port}"
            media = self.vlc_instance.media_new(stream_url)
            self.media_player.set_media(media)
            self.media_player.play()
            self.media_player.audio_set_volume(self.volume)
            self.apply_audio()
            
        except Exception as e:
            self.chat_signals.status_changed.emit(f"Erro ao abrir: {e}")

    def send_chat_message(self):
        msg = self.input_chat.text().strip()
        if msg and self.irc_client:
            self.irc_client.send_message(msg)
            self.display_chat_message(self.display_name, msg)
            self.input_chat.clear()

    def open_emote_picker(self):
        popup = EmotePickerPopup(self.channel_name, self.insert_emote)
        pos = self.btn_emote.mapToGlobal(self.btn_emote.rect().topLeft())
        pos.setY(pos.y() - popup.height())
        popup.move(pos)
        popup.show()

    def insert_emote(self, name):
        current = self.input_chat.text()
        sep = "" if not current or current.endswith(" ") else " "
        self.input_chat.setText(f"{current}{sep}{name} ")
        self.input_chat.setFocus()

    def display_chat_message(self, user, msg):
        # 1. Segurança: Impede que utilizadores quebrem o HTML
        msg = msg.replace("<", "&lt;").replace(">", "&gt;")
        
        # 2. Aplica emojis de texto tradicionais como base
        for emote, emoji in EMOTE_MAP.items():
            msg = msg.replace(emote, emoji)

        # 3. Transforma palavras-chave em emotes reais (imagens)
        words = msg.split()
        for i, word in enumerate(words):
            emote_html = emote_manager.get_emote_html(word)
            if emote_html:
                words[i] = emote_html
                
        msg_html = " ".join(words)

        # 4. Formatação de cores e hora
        colors = ["#00ffff", "#ff79c6", "#50fa7b", "#f1fa8c", "#8be9fd", "#ffb86c", "#bd93f9"]
        user_color = colors[sum(ord(c) for c in user) % len(colors)]
        hora = datetime.now().strftime("%H:%M")

        html_msg = f'<span style="color: #6272a4;">[{hora}]</span> <b style="color: {user_color};">{user}:</b> {msg_html}'
        
        # 5. Adiciona a mensagem ao chat
        self.chat_display.append(html_msg)

        # 6. OTIMIZAÇÃO DE PERFORMANCE: Limita o histórico a 150 mensagens
        # Isto impede que o QTextBrowser fique pesado com o passar do tempo
        document = self.chat_display.document()
        if document.blockCount() > 150:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def open_subscribe_page(self):
        """Abre a página oficial de assinatura no navegador — o checkout em si
        só a própria Twitch pode processar, não dá (nem deve) ser feito via API."""
        webbrowser.open(f"https://www.twitch.tv/subs/{self.channel_name}")

    def set_volume(self, value):
        self.volume = value
        self.volume_label.setText(f"{value}%")
        self.media_player.audio_set_volume(value)

    def set_user_muted(self, muted):
        self.user_muted = muted
        self.mute_button.setText("Mudo" if muted else "Som")
        self.apply_audio()

    def set_muted(self, muted: bool):
        self.focus_muted = muted
        self.apply_audio()

    def apply_audio(self):
        self.media_player.audio_set_mute(self.user_muted or self.focus_muted)

    def bind_video(self):
        handle = int(self.video_frame.winId())
        if sys.platform.startswith("linux"):
            self.media_player.set_xwindow(handle)
        elif sys.platform == "win32":
            self.media_player.set_hwnd(handle)
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(handle)

    def toggle_pip(self):
        if self.pip_window is not None:
            self.pip_window.close()
            return
        self.pip_window = PictureWindow(self)
        self.pip_window.box.insertWidget(0, self.video_frame, 1)
        self.pip_window.show()
        self.video_frame.show()
        self.bind_video()

    def restore_video(self):
        self.video_layout.insertWidget(0, self.video_frame, 1)
        self.video_frame.show()
        self.bind_video()
        window = self.pip_window
        self.pip_window = None
        if window is not None:
            window.deleteLater()

    def update_status(self, text):
        self.lbl_chat_status.setText(text)

    def close_tab(self):
        if self.pip_window is not None:
            self.pip_window.close()
        if self.irc_client:
            self.irc_client.stop()
        self.media_player.stop()
        
        # Garante que o servidor invisível do Streamlink feche junto com a aba
        if hasattr(self, 'streamlink_process') and self.streamlink_process:
            self.streamlink_process.terminate()
            self.streamlink_process.wait()

# INTERFACE GRÁFICA PRINCIPAL (PyQt6)
class TwitchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SabiáCast — Multi-Live")
        self.resize(1280, 720)

        self.user_id, self.user_login, self.display_name = get_my_info()
        if not self.user_id:
            QMessageBox.critical(self, "Erro", "Falha ao autenticar. Verifique CLIENT_ID e ACCESS_TOKEN.")
            sys.exit(1)

        self.cinema_mode = False
        self.cinema_sizes = None
        self.open_tabs = {}
        self.saved_sidebar_size = 260

        self.init_ui()
        self.load_followed_streams()

        # Busca (1x, em background) os emotes que ESTA conta pode de fato usar,
        # pra alimentar o seletor de emote sem travar a UI
        threading.Thread(target=self._load_usable_emotes, daemon=True).start()

        # Atalho de teclado Ctrl+B para ocultar/mostrar a sidebar
        shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        shortcut.activated.connect(self.toggle_sidebar)
        self.shortcuts = []
        for key, callback in [
            ("F11", self.toggle_fullscreen),
            ("Escape", self.leave_view_modes),
            ("Ctrl+Shift+C", self.toggle_cinema),
            ("Ctrl+Shift+P", lambda: self.with_tab(lambda t: t.toggle_pip())),
            ("Ctrl+M", lambda: self.with_tab(lambda t: t.mute_button.toggle())),
            ("Ctrl+Up", lambda: self.adjust_volume(5)),
            ("Ctrl+Down", lambda: self.adjust_volume(-5)),
            ("Ctrl+Tab", lambda: self.cycle_tab(1)),
            ("Ctrl+Shift+Tab", lambda: self.cycle_tab(-1)),
        ]:
            action = QShortcut(QKeySequence(key), self)
            action.activated.connect(callback)
            self.shortcuts.append(action)

    def _load_usable_emotes(self):
        usable = get_user_emotes(self.user_id)
        emote_manager.add_emotes(usable, category="usable")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # ----------------------------------------------------------------------
        # SPLITTER PRINCIPAL (Permite arrastar e recolher a barra esquerda)
        # ----------------------------------------------------------------------
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # PAINEL LATERAL ESQUERDO
        sidebar = QWidget()
        self.sidebar = sidebar
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        lbl_user = QLabel(f"👤 <b>{self.display_name}</b>")
        lbl_user.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(lbl_user)
        header_layout.addStretch()

        # Botão para trocar de conta (limpa as credenciais salvas nesta máquina)
        btn_logout = QPushButton("🔓")
        btn_logout.setObjectName("iconButton")
        btn_logout.setFixedSize(34, 34)
        btn_logout.setToolTip("Trocar de conta")
        btn_logout.clicked.connect(self.logout)
        header_layout.addWidget(btn_logout)

        # Botão para recolher a sidebar
        btn_toggle = QPushButton("◄")
        btn_toggle.setObjectName("iconButton")
        btn_toggle.setFixedSize(34, 34)
        btn_toggle.setToolTip("Ocultar lista de canais (Ctrl+B)")
        btn_toggle.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(btn_toggle)

        sidebar_layout.addLayout(header_layout)

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Atualizar")
        btn_refresh.clicked.connect(self.load_followed_streams)
        btn_layout.addWidget(btn_refresh)

        btn_search = QPushButton("Buscar")
        btn_search.clicked.connect(self.search_channel)
        btn_layout.addWidget(btn_search)
        sidebar_layout.addLayout(btn_layout)

        self.channel_list = QListWidget()
        self.channel_list.itemDoubleClicked.connect(self.on_channel_selected)
        sidebar_layout.addWidget(self.channel_list)

        # Barra de atalhos sempre visível
        shortcuts_bar = QLabel(
            "⌨  <b>Ctrl+B</b> ocultar barra  ·  <b>F11</b> tela cheia  ·  "
            "<b>Ctrl+Shift+C</b> cinema · <b>Ctrl+Shift+P</b> PiP · "
            "<b>Ctrl+M</b> mudo · <b>Ctrl+↑/↓</b> volume · "
            "<b>Ctrl+Tab</b> trocar aba · <b>Esc</b> voltar"
        )
        shortcuts_bar.setObjectName("shortcutsBar")
        shortcuts_bar.setWordWrap(True)
        sidebar_layout.addWidget(shortcuts_bar)

        self.main_splitter.addWidget(sidebar)

        # ÁREA DE ABAS MULTI-LIVE (DIREITA)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab_at_index)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.main_splitter.addWidget(self.tab_widget)

        # Permite recolher a barra lateral completamente até o zero
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setSizes([260, 1020])

        main_layout.addWidget(self.main_splitter)

    # --------------------------------------------------------------------------
    # CONTROLE DA BARRA LATERAL (RECOLHER / EXPANDIR)
    # --------------------------------------------------------------------------
    def toggle_sidebar(self):
        if self.cinema_mode:
            self.toggle_cinema()
            return
        sizes = self.main_splitter.sizes()
        if sizes[0] > 0:
            # Salva a largura atual antes de fechar
            self.saved_sidebar_size = sizes[0]
            self.main_splitter.setSizes([0, sizes[1] + sizes[0]])
        else:
            # Reabre na largura anterior
            self.main_splitter.setSizes([self.saved_sidebar_size, sizes[1] - self.saved_sidebar_size])

    # --------------------------------------------------------------------------
    # FOCO DE ÁUDIO (só a aba ativa toca som; as outras ficam mudas)
    # --------------------------------------------------------------------------
    def with_tab(self, callback):
        tab = self.tab_widget.currentWidget()
        if isinstance(tab, StreamTab):
            callback(tab)

    def adjust_volume(self, delta):
        self.with_tab(lambda t: t.volume_slider.setValue(t.volume_slider.value() + delta))

    def cycle_tab(self, delta):
        count = self.tab_widget.count()
        if count:
            self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() + delta) % count)

    def toggle_cinema(self):
        if not self.tab_widget.count():
            return
        self.cinema_mode = not self.cinema_mode
        if self.cinema_mode:
            self.cinema_sizes = self.main_splitter.sizes()
        self.sidebar.setVisible(not self.cinema_mode)
        self.tab_widget.tabBar().setVisible(not self.cinema_mode)
        for i in range(self.tab_widget.count()):
            self.tab_widget.widget(i).chat_widget.setVisible(not self.cinema_mode)
        if not self.cinema_mode and self.cinema_sizes:
            self.main_splitter.setSizes(self.cinema_sizes)

    def leave_view_modes(self):
        self.with_tab(lambda t: t.pip_window.close() if t.pip_window else None)
        if self.cinema_mode:
            self.toggle_cinema()
        if self.isFullScreen():
            self.showNormal()

    def on_tab_changed(self, index):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, StreamTab):
                tab.set_muted(i != index)
                tab.chat_widget.setVisible(not self.cinema_mode)

    # --------------------------------------------------------------------------
    # GERENCIAMENTO DE ABAS
    # --------------------------------------------------------------------------
    def open_channel_tab(self, channel_name):
        channel_key = channel_name.lower()

        if channel_key in self.open_tabs:
            tab_instance = self.open_tabs[channel_key]
            index = self.tab_widget.indexOf(tab_instance)
            if index != -1:
                self.tab_widget.setCurrentIndex(index)
                return

        new_tab = StreamTab(channel_name, self.user_login, self.display_name, self)
        tab_index = self.tab_widget.addTab(new_tab, f"🔴 {channel_name}")
        self.open_tabs[channel_key] = new_tab
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab_at_index(self, index):
        if self.cinema_mode and self.tab_widget.count() == 1:
            self.toggle_cinema()
        tab_widget = self.tab_widget.widget(index)
        if isinstance(tab_widget, StreamTab):
            for key, val in list(self.open_tabs.items()):
                if val == tab_widget:
                    del self.open_tabs[key]
                    break
            tab_widget.close_tab()
            self.tab_widget.removeTab(index)

    # --------------------------------------------------------------------------
    # CONTROLE DE TELA CHEIA
    # --------------------------------------------------------------------------
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        super().keyPressEvent(event)

    # --------------------------------------------------------------------------
    # MÉTODOS DE AÇÃO
    # --------------------------------------------------------------------------
    def load_followed_streams(self):
        self.channel_list.clear()
        streams = get_followed_streams(self.user_id)
        if not streams:
            self.channel_list.addItem("Nenhum canal ao vivo.")
            return

        for s in streams:
            item_text = f"🔴 {s['user_name']}\n🎮 {s['game_name']}\n👥 {s['viewer_count']} viewers"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, s['user_login'])
            self.channel_list.addItem(item)

    def search_channel(self):
        query, ok = QInputDialog.getText(self, "Buscar Canal", "Digite o nome do canal:")
        if ok and query.strip():
            channels = search_channels(query.strip())
            self.channel_list.clear()
            for ch in channels:
                item_text = f"📺 {ch['display_name']} (@{ch['broadcaster_login']})\n🎮 {ch['game_name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, ch['broadcaster_login'])
                self.channel_list.addItem(item)

    def on_channel_selected(self, item):
        channel_login = item.data(Qt.ItemDataRole.UserRole)
        if channel_login:
            self.open_channel_tab(channel_login)

    def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if isinstance(tab_widget, StreamTab):
                tab_widget.close_tab()
        event.accept()

    def logout(self):
        resposta = QMessageBox.question(
            self, "Trocar de conta",
            "Isso vai apagar as credenciais salvas nesta máquina e fechar o app.\n"
            "Na próxima vez que abrir, você loga com outra conta. Continuar?"
        )
        if resposta == QMessageBox.StandardButton.Yes:
            clear_saved_credentials()
            self.close()
            sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(AURORA_THEME_STYLE)

    saved_client_id, saved_token = load_saved_credentials()
    if saved_client_id and saved_token:
        apply_credentials(saved_client_id, saved_token)
    else:
        login = LoginDialog()
        if login.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

    window = TwitchApp()
    window.show()
    sys.exit(app.exec())
