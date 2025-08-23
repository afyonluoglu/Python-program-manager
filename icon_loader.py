# -*- coding: utf-8 -*-

import tkinter as tk
import os
from utils import ICON_FOLDER, ICON_PYTHON_FILE, ICON_COMPRESS, ICON_EXECUTABLE, ICON_UNKNOWN, ICON_DATABASE_FILE, ICON_ARROW_UP, ICON_ARROW_DOWN, ICON_MP3_FILE, ICON_PLAY_BUTTON, ICON_PAUSE_BUTTON, ICON_STOP_BUTTON

def _load_icon(icon_path, icon_name_for_log):
    """Belirli bir ikonu yükler ve PhotoImage nesnesini döndürür."""
    if os.path.exists(icon_path):
        try:
            img = tk.PhotoImage(file=icon_path)
            if img and img.width() > 0 and img.height() > 0:
                return img
            else:
                print(f"HATA: tk.PhotoImage(file='{icon_path}') '{icon_name_for_log}' için boş veya geçersiz bir resim döndürdü.")
                return None
        except tk.TclError as e_tcl:
            print(f"HATA: '{icon_name_for_log}' yüklenirken TclError ('{icon_path}'): {e_tcl}")
            return None
        except Exception as e_exc:
            print(f"HATA: '{icon_name_for_log}' yüklenirken BEKLENMEDİK HATA ('{icon_path}'): {type(e_exc).__name__} - {e_exc}")
            return None
    else:
        print(f"HATA: '{icon_name_for_log}' dosyası bulunamadı: {icon_path}")
        return None

def load_all_icons(base_path):
    """
    Tüm uygulama ikonlarını yükler ve bir sözlük olarak döndürür.
    Keys: "folder", "file", "zip", "exe", "unknown" "db"
          "arrow_up", "arrow_down", "mp3", "play_btn", "pause_btn", "stop_btn"
    Values: PhotoImage nesneleri veya None (yüklenemezse).
    """
    icons = {
        "folder": None,
        "file": None,
        "zip": None,
        "exe": None,
        "unknown": None,
        "db": None,
        "arrow_up": None,
        "arrow_down": None,
        "mp3": None,
        "play_btn": None,
        "pause_btn": None,
        "stop_btn": None,
    }

    icon_definitions = [
        ("folder", ICON_FOLDER, "folder_icon"),
        ("file", ICON_PYTHON_FILE, "file_icon"),
        ("zip", ICON_COMPRESS, "zip_icon"),
        ("exe", ICON_EXECUTABLE, "exe_icon"),
        ("unknown", ICON_UNKNOWN, "unknown_icon"),
        ("db", ICON_DATABASE_FILE, "db_icon"),
        ("arrow_up", ICON_ARROW_UP, "arrow_up_icon"),
        ("arrow_down", ICON_ARROW_DOWN, "arrow_down_icon"),
        ("mp3", ICON_MP3_FILE, "mp3_icon"),
        ("play_btn", ICON_PLAY_BUTTON, "play_button_icon"),
        ("pause_btn", ICON_PAUSE_BUTTON, "pause_button_icon"),
        ("stop_btn", ICON_STOP_BUTTON, "stop_button_icon"),
    ]

    icons_dir = os.path.join(base_path, "icons")

    for key, filename, log_name in icon_definitions:
        if filename: # utils.py'de dosya adı tanımlanmışsa
            icon_path = os.path.join(icons_dir, filename)
            icons[key] = _load_icon(icon_path, log_name)
        else:
            print(f"UYARI: '{log_name}' için utils.py'de ikon dosya adı tanımlanmamış.")
            
    return icons

# Örnek kullanım (test için):
# if __name__ == '__main__':
#     root = tk.Tk() # PhotoImage için bir ana pencereye ihtiyaç var
#     current_base_path = os.path.dirname(os.path.abspath(__file__)) # Bu dosyanın olduğu dizin
#     loaded_icons = load_all_icons(current_base_path)
#     print(loaded_icons)
#     # root.mainloop() # Pencereyi görmek isterseniz