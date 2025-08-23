# -*- coding: utf-8 -*-

import tkinter as tk # App sınıfı tk.Tk'den miras alacağı için burada tk importu gerekmeyebilir.
from app_gui import App # app_gui.py dosyasından App sınıfını import et
import platform

# Yüksek DPI ayarları için (Windows'ta bulanıklığı azaltabilir)
if platform.system() == "Windows":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except ImportError: # Linux/macOS veya ctypes yoksa
        pass
    except AttributeError: # Eski Windows sürümleri
        try:
           windll.user32.SetProcessDPIAware()
        except: # Gerekli fonksiyon yoksa
           pass

if __name__ == "__main__":
    app = App()
    app.mainloop()