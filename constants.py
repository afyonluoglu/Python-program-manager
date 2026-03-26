# -*- coding: utf-8 -*-
"""
Python Program Yöneticisi - Sabitler ve Enum Tanımları

Bu modül, uygulama genelinde kullanılan sabit değerleri ve
enum tanımlamalarını içerir. Merkezi sabit yönetimi sayesinde
kod tekrarı önlenir ve bakım kolaylaşır.
"""

from enum import Enum, auto


class FileType(Enum):
    """Desteklenen dosya türlerini tanımlar.
    
    Bu enum, dosya tarayıcısında ve diğer bileşenlerde dosya
    türlerini belirlemek için kullanılır.
    
    Attributes:
        PYTHON: Python kaynak dosyaları (.py)
        EXECUTABLE: Çalıştırılabilir dosyalar (.exe, .bat, .cmd)
        ARCHIVE: Sıkıştırılmış dosyalar (.zip, .rar, .7z)
        DATABASE: Veritabanı dosyaları (.db, .sqlite)
        AUDIO: Ses dosyaları (.mp3, .wav, .ogg)
        MARKDOWN: Markdown dosyaları (.md)
        JSON: JSON dosyaları (.json)
        TEXT: Metin dosyaları (.txt)
        FOLDER: Klasörler
        UNKNOWN: Bilinmeyen dosya türleri
    """
    PYTHON = auto()
    EXECUTABLE = auto()
    ARCHIVE = auto()
    DATABASE = auto()
    AUDIO = auto()
    MARKDOWN = auto()
    JSON = auto()
    TEXT = auto()
    FOLDER = auto()
    UNKNOWN = auto()


class EventType(Enum):
    """Çalıştırma geçmişi olay türlerini tanımlar.
    
    Bu enum, execution_history tablosunda kaydedilen olayların
    türlerini standartlaştırır.
    
    Attributes:
        RUN_NORMAL: Normal Python dosyası çalıştırma
        RUN_DEBUG: Debug modunda çalıştırma
        COMPRESS: Sıkıştırma işlemi
        DECOMPRESS: Sıkıştırılmış dosya açma
        CONVERT_EXE: EXE'ye dönüştürme
        SEARCH: Arama işlemi başlatma
        WORD_SEARCH: Kelime arama işlemi
        RENAME: Dosya yeniden adlandırma
        DELETE: Dosya silme
        COPY: Dosya kopyalama
        MOVE: Dosya taşıma
        OPEN_EXTERNAL: Harici uygulama ile açma
        EDIT: Dosya düzenleme
        ANALYZE: Kod analizi
    """
    RUN_NORMAL = "run_normal"
    RUN_DEBUG = "run_debug"
    COMPRESS = "compress"
    DECOMPRESS = "decompress"
    CONVERT_EXE = "convert_exe"
    SEARCH = "search_initiated"
    WORD_SEARCH = "word_search"
    RENAME = "rename"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    OPEN_EXTERNAL = "open_external"
    EDIT = "edit"
    ANALYZE = "analyze"


class ThemeColor(Enum):
    """Tema renk anahtarlarını tanımlar.
    
    Bu enum, tema yapılandırmasında kullanılan renk
    anahtarlarını standartlaştırır.
    """
    MAIN_BG = "main_bg"
    TREE_BG = "tree_bg"
    TREE_FG = "tree_fg"
    TREE_SELECT_BG = "tree_select_bg"
    TREE_SELECT_FG = "tree_select_fg"
    BUTTON_BG = "button_bg"
    BUTTON_FG = "button_fg"
    ENTRY_BG = "entry_bg"
    ENTRY_FG = "entry_fg"


class SearchMode(Enum):
    """Arama modlarını tanımlar.
    
    Attributes:
        FILENAME: Dosya adına göre arama
        CONTENT: Dosya içeriğinde kelime arama
        REGEX: Regular expression ile arama
    """
    FILENAME = auto()
    CONTENT = auto()
    REGEX = auto()


# Dosya uzantısı eşleştirmeleri
FILE_TYPE_EXTENSIONS = {
    FileType.PYTHON: ['.py', '.pyw', '.pyi'],
    FileType.EXECUTABLE: ['.exe', '.bat', '.cmd', '.com'],
    FileType.ARCHIVE: ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    FileType.DATABASE: ['.db', '.sqlite', '.sqlite3'],
    FileType.AUDIO: ['.mp3', '.wav', '.ogg', '.flac', '.m4a'],
    FileType.MARKDOWN: ['.md', '.markdown'],
    FileType.JSON: ['.json'],
    FileType.TEXT: ['.txt', '.log', '.cfg', '.ini'],
}


def get_file_type(file_path: str) -> FileType:
    """Dosya yolundan dosya türünü belirler.
    
    Args:
        file_path: Dosya yolu veya dosya adı.
        
    Returns:
        FileType: Belirlenen dosya türü.
        
    Example:
        >>> get_file_type("main.py")
        FileType.PYTHON
        >>> get_file_type("archive.zip")
        FileType.ARCHIVE
    """
    import os
    
    if os.path.isdir(file_path):
        return FileType.FOLDER
    
    _, ext = os.path.splitext(file_path.lower())
    
    for file_type, extensions in FILE_TYPE_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    
    return FileType.UNKNOWN


# Varsayılan değerler
DEFAULT_WINDOW_SIZE = "900x650"
DEFAULT_EDITOR_SIZE = "1000x700"
MAX_HISTORY_ENTRIES = 1000
MAX_FAVORITES = 100
AUTOCOMPLETE_MIN_CHARS = 2
AUTOCOMPLETE_MAX_SUGGESTIONS = 12

# Dosya boyutu limitleri (byte)
MAX_FILE_SIZE_FOR_CONTENT_SEARCH = 10 * 1024 * 1024  # 10 MB
MAX_FILE_SIZE_FOR_PREVIEW = 5 * 1024 * 1024  # 5 MB
