# -*- coding: utf-8 -*-

import tkinter as tk 
from app_gui import App 
import platform

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