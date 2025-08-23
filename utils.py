# -*- coding: utf-8 -*-

# --- Sabitler ---
BACKUP_FOLDER_BASENAME = "backups" # Yedekleme klasörünün temel adı
DB_NAME = "program_manager_data.db"

DEFAULT_DARK_THEME_COLORS = {
    "main_bg": "#2E3B4E",          # Ana pencere arka planı
    "tree_bg": "#252A33",          # Treeview (liste) arka planı
    "tree_fg": "#D0D0D0",          # Treeview (liste) yazı rengi
    "tree_select_bg": "#4A90E2",   # Treeview seçili öğe arka planı
    "tree_select_fg": "#FFFFFF",   # Treeview seçili öğe yazı rengi (beyaz)
    "button_bg": "#4A5568",        # TButton arka planı
    # Diğer elemanlar için renkler buraya eklenebilir
}

# İkon dosya adları (opsiyonel, app_gui.py içinde de tanımlanabilir)
ICON_FOLDER = "folder.png"
ICON_PYTHON_FILE = "python_file.png"
ICON_COMPRESS = "compress.png"
ICON_EXECUTABLE = "executable.png"
ICON_UNKNOWN = "unknown.png" # Bilinmeyen dosya türleri için ikon
ICON_DATABASE_FILE = "database.png" # Veritabanı dosyaları için ikon
ICON_ARROW_UP = "arrow_up.png" # Yukarı ok ikonu
ICON_ARROW_DOWN = "arrow_down.png" # Aşağı ok ikonu
ICON_MP3_FILE = "play.png" # MP3 dosyaları için ikon
ICON_PLAY_BUTTON = "play_button.png" # MP3 Oynat butonu
ICON_PAUSE_BUTTON = "pause_button.png" # MP3 Duraklat butonu
ICON_STOP_BUTTON = "stop_button.png" # MP3 Durdur butonu