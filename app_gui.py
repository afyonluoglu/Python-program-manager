# -*- coding: utf-8 -*-

# --- Gerekli Kütüphaneler ---

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import os
import subprocess
import platform
import json
from datetime import datetime
import sys

from sympy import false # ZIP dosyalarını okumak için

# Yerel modüllerden importlar
from utils import DB_NAME, DEFAULT_DARK_THEME_COLORS, ICON_FOLDER, ICON_PYTHON_FILE, ICON_COMPRESS, ICON_EXECUTABLE, ICON_UNKNOWN, ICON_DATABASE_FILE, ICON_ARROW_UP, ICON_ARROW_DOWN, BACKUP_FOLDER_BASENAME, ICON_MP3_FILE, ICON_PLAY_BUTTON, ICON_PAUSE_BUTTON, ICON_STOP_BUTTON
from db_manager import DatabaseManager
from ui_dialogs import SearchResultsWindow, WordSearchResultsWindow # WordSearchResultsWindow'ı da ekleyin
from favorites_manager import FavoritesManager # Yeni import
from theme_manager import ThemeManager # Yeni import
from history_manager import HistoryManager # Yeni import
from file_browser import FileBrowser # Yeni import
from search_manager import SearchManager # Yeni import
from action_manager import ActionManager # Yeni import
from icon_loader import load_all_icons # Yeni import
from ui_manager import UIManager # Yeni import
from execution_manager import ExecutionManager # Yeni import
from python_analyzer import PythonAnalyzer, DependencyAnalyzer # Python dosya analizi için
import operations # operations.py'deki fonksiyonları kullanmak için
from metod_analiz import MethodAnalyzer  # Bu import'u dosyanın başına ekleyin
from python_editor import PythonEditor  # Python editörü için yeni import
from custom_widgets import ColoredContextMenu  # Import ekleyin

# --- Ana Uygulama Sınıfı ---
class App(tk.Tk):
    """Ana uygulama penceresi ve mantığı."""
    def __init__(self):
        super().__init__()
        self.title("Python Program Yöneticisi")
        self.geometry("900x650") # Boyutu biraz büyüttük

        # Uygulamanın çalıştığı temel dizini belirle
        if getattr(sys, 'frozen', False):
            # PyInstaller gibi bir araçla paketlenmişse
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Normal script olarak çalışıyorsa
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # --- İkonları Yükle (icon_loader.py üzerinden) ---
        loaded_icons = load_all_icons(self.base_path)
        self.folder_icon = loaded_icons.get("folder")
        self.file_icon = loaded_icons.get("file")
        self.zip_icon = loaded_icons.get("zip")
        self.exe_icon = loaded_icons.get("exe")
        self.db_icon = loaded_icons.get("db") # Yeni DB ikonu
        self.unknown_icon = loaded_icons.get("unknown")
        self.arrow_up_icon = loaded_icons.get("arrow_up")
        self.arrow_down_icon = loaded_icons.get("arrow_down")
        self.mp3_icon = loaded_icons.get("mp3") # Dosya listesi için
        self.play_button_icon = loaded_icons.get("play_btn")   # MP3 kontrolü için
        self.pause_button_icon = loaded_icons.get("pause_btn") # MP3 kontrolü için
        self.stop_button_icon = loaded_icons.get("stop_btn")   # MP3 kontrolü için


        self.db_path = os.path.join(self.base_path, DB_NAME)
        # Veritabanı yöneticisini başlatmadan önce, eğer favorites_panel_visible ayarı yoksa oluşturalım
        # Bu, _apply_saved_sash_position'ın erken bir aşamada bu ayara erişebilmesi için.
        temp_db_check = DatabaseManager(self.db_path) # Geçici bağlantı
        if temp_db_check.get_setting("favorites_panel_visible") is None:
            temp_db_check.set_setting("favorites_panel_visible", "0") # Varsayılan olarak gizli
        temp_db_check._close()
        self.db = DatabaseManager(self.db_path)

        self.style = ttk.Style(self)
        # Windows temalarını önceliklendir ('vista', 'xpnative'), sonra diğerleri ('clam', 'alt', 'default')
        available_themes = self.style.theme_names()
        preferred_themes = ['vista', 'xpnative', 'clam', 'alt', 'default'] # Windows öncelikli tercih sırası
        chosen_theme = None
        # print(f"DEBUG: Kullanılabilir Temalar: {available_themes}") # Hangi temaların olduğunu görmek için
        for theme in preferred_themes:
            if theme in available_themes:
                chosen_theme = theme
                break
        if not chosen_theme and available_themes:
             chosen_theme = available_themes[0] # Bulunamazsa ilk kullanılabilir tema

        if chosen_theme:
            try:
                self.style.theme_use(chosen_theme)
                self.db.set_setting("chosen_theme", chosen_theme) # Save the base theme used
                print(f"✨ Kullanılan tema: {chosen_theme}")
            except tk.TclError:
                print(f"❗ {chosen_theme} teması yüklenemedi, varsayılan kullanılıyor.")
        else:
            print("❗ Kullanılabilir ttk teması bulunamadı.")

        # Okunabilirlik için Stil Ayarları (Treeview için)
        # Daha büyük bir font ve satır yüksekliği deneyelim
        style_font = ("Segoe UI", 10) # Windows için iyi bir varsayılan
        self.style.configure("Treeview", rowheight=25, font=style_font) # Satır yüksekliğini artır
        self.style.configure("Treeview.Heading", font=(style_font[0], style_font[1], 'bold')) # Başlıkları kalın yap

        # Son seçilen klasörü yükle
        self.current_folder = self.db.get_setting("last_folder")

        # Favorites Panel related
        self.favorites_pane = None # This will be the frame added to PanedWindow
        self.favorites_list_treeview = None
        # self.is_favorites_panel_visible_setting = "favorites_panel_visible" # DB key        # --- Manager Sınıflarının Örnekleri ---
        self.favorites_manager = FavoritesManager(self)
        self.theme_manager = ThemeManager(self)
        self.history_manager = HistoryManager(self)
        self.search_manager = SearchManager(self)
        self.file_browser = FileBrowser(self)
        self.action_manager = ActionManager(self)
        self.ui_manager = UIManager(self) # UIManager örneği
        self.execution_manager = ExecutionManager(self) # ExecutionManager örneği
        self.python_analyzer = PythonAnalyzer(self) # PythonAnalyzer örneği
        self.dependency_analyzer = DependencyAnalyzer() # DependencyAnalyzer örneği

        self.ui_manager._setup_ui() # UI kurulumu UIManager üzerinden

        self.file_browser.setup_file_list_colors()
        
        self.ui_manager._setup_menus() # Menü kurulumu UIManager üzerinden
        
        # Dosya listesi sıralama durumu - populate_tree çağrısından önce tanımlanmalı
        self.file_list_sort_column = None
        self.file_list_sort_order_asc = True # True: artan, False: azalan
        # _update_file_list_header_indicators çağrısı __init__ sonunda kalacak,
        # populate_file_list zaten gerekirse çağırıyor.

        # MP3 kontrolü için _programmatic_scale_update bayrağı
        self._programmatic_scale_update = False
        self._mp3_after_id = None # MP3 polling için after ID'si

        self.theme_manager.apply_custom_theme() # Kayıtlı özel tema renklerini uygula

        # Dosya listesinin o anda hangi klasörü gösterdiğini takip etmek için
        self.currently_displayed_folder_in_file_list = None
        
        # Başlangıçta klasör ağacını doldur
        if self.current_folder and os.path.isdir(self.current_folder): # İlk yüklemede App içinden çağır
            self.file_browser.populate_tree(self.current_folder) # FileBrowser üzerinden çağır
        else:
            self.current_folder = None # Geçersizse sıfırla
            # İsteğe bağlı: Kullanıcıya ilk kez klasör seçmesini isteyebiliriz
            # self.select_folder()

        # Olayları bağla
        self.dir_tree.bind("<<TreeviewSelect>>", self.file_browser.on_tree_select) # FileBrowser üzerinden
        self.file_list.bind("<Double-1>", self.on_file_double_click) # Sol çift tıklama
        self.dir_tree.bind("<<TreeviewOpen>>", self.file_browser.on_node_expand) # FileBrowser üzerinden
        self.file_list.bind("<Button-3>", self.show_file_context_menu) # Sağ tıklama (Windows/Linux)
        self.file_list.bind("<Delete>", self.file_browser.on_file_delete_key) # FileBrowser üzerinden
        self.dir_tree.bind("<Button-3>", self.show_dir_context_menu) # Klasör ağacı için sağ tık menüsü
        
        # Favoriler paneli olay bağlamaları (widget'lar App'de olduğu için burada kalmalı)
        self.favorites_list_treeview.bind("<Double-1>", self.favorites_manager._on_favorite_double_click)
        self.favorites_list_treeview.bind("<Button-3>", self.favorites_manager._show_favorites_context_menu)
        self.favorites_list_treeview.bind("<<TreeviewSelect>>", self._on_favorite_click)

        self.file_list.bind("<Button-2>", self.show_file_context_menu) # Sağ tıklama (macOS)

        # Pencere kapatıldığında veritabanı bağlantısını düzgün kapat
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._bind_global_shortcuts() # Global kısayolları bağla

        # Ana pencere geometrisini yükle veya ortala
        self.load_or_center_window("main", self, 900, 650) # Varsayılan boyutlar

        self.after_idle(self._update_file_list_header_indicators) # Başlangıçta başlıkları ayarla

    def _bind_global_shortcuts(self):
        """Uygulama geneli klavye kısayollarını bağlar."""
        self.bind_all("<Control-d>", lambda event: self.search_manager.prompt_search())
        self.bind_all("<Control-f>", lambda event: self.search_manager.prompt_word_search()) 
        self.bind_all("<Control-o>", lambda event: self.file_browser.select_folder())
        self.bind_all("<Control-q>", lambda event: self.on_closing())
        self.bind_all("<Control-p>", lambda event: self.open_window_settings_dialog())
        self.bind_all("<Control-b>", lambda event: self.favorites_manager._toggle_favorites_panel())
        self.bind_all("<Control-h>", lambda event: self.history_manager.show_history())
        self.bind_all("<Control-t>", lambda event: self.theme_manager.manage_themes())
        self.bind_all("<F1>", lambda event: self.show_help())
        
        # Not: Bazı widget'lar (örn. Entry) Ctrl+H gibi kısayolları kendileri için yakalayabilir.
        # Bu durumda, event.widget.winfo_class() kontrolü ile Entry widget'ındaysa işlem yapmamak gibi
        # daha karmaşık bir mantık gerekebilir. Şimdilik genel bağlama yeterli olacaktır.

        # Kaydedilmiş splitter konumunu pencere hazır olduğunda uygula
        # manage_visibility=True ile çağırarak başlangıçta panel görünürlüğünü de yönetmesini sağla
        self.after_idle(lambda: self._apply_saved_sash_position(manage_visibility=True))

    def _on_favorite_click(self, event):
        selected_item_id = self.favorites_list_treeview.focus()
        if not selected_item_id:
            return
        item_data = self.favorites_list_treeview.item(selected_item_id)
        file_path = item_data["values"][0]
        self.status_label.config(text=f"Favori: {file_path}")

    def load_or_center_window(self, window_key, window_obj, default_width, default_height):
        """Loads saved geometry or centers the window."""
        saved_geom = self.db.get_window_geometry(window_key)
        if saved_geom:
            try:
                # Geometriyi uygulamadan önce pencerenin var olduğundan emin olalım
                window_obj.update_idletasks()
                window_obj.geometry(saved_geom)
                # print(f"'{window_key}' için geometri yüklendi: {saved_geom}") # Bilgi mesajı
            except Exception as e: # Daha genel bir hata yakalama (TclError dahil)
                error_msg = f"'{window_key}' penceresi için kaydedilmiş konum/boyut bilgisi ({saved_geom}) uygulanamadı:\n{e}\n\nBu pencere için ayarlar sıfırlanacak ve varsayılan konumda açılacaktır."
                print(f"❗ HATA: {error_msg}") # Konsola detaylı log
                messagebox.showwarning("Pencere Konum Hatası", error_msg, parent=self) # Kullanıcıya uyarı göster
                try:
                    # Sorunlu geometri kaydını veritabanından sil
                    self.db.delete_window_geometry(window_key)
                except Exception as db_err:
                    print(f"❗ HATA: Sorunlu geometri kaydı ({window_key}) silinirken veritabanı hatası: {db_err}")
                self.center_window(window_obj, default_width, default_height)
        else:
            self.center_window(window_obj, default_width, default_height)

    def center_window(self, window, width=None, height=None):
        """Bir Toplevel penceresini ekranın ortasına yerleştirir."""
        window.update_idletasks() # Pencere boyutlarının hesaplanmasını bekle
        w = width or window.winfo_width()
        h = height or window.winfo_height()
        ws = window.winfo_screenwidth() # Ekran genişliği
        hs = window.winfo_screenheight() # Ekran yüksekliği
        # Ortalanmış x ve y koordinatlarını hesapla
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        # Pencereyi konumlandır
        window.geometry('%dx%d+%d+%d' % (w, h, x, y))
        window.deiconify() # Gizlenmişse göster

    def on_closing(self):
        """Pencere kapatılırken yapılacaklar."""
        # Ana pencere geometrisini kaydet
        geom = self.winfo_geometry()
        self.db.save_window_geometry("main", geom)

        # Dosya listesi sütun genişliklerini doğru anahtara kaydet
        if hasattr(self, 'file_list') and self.file_list.winfo_exists() and \
           hasattr(self, 'currently_displayed_folder_in_file_list') and \
           self.currently_displayed_folder_in_file_list and \
           os.path.isdir(self.currently_displayed_folder_in_file_list):
            try:
                current_col_widths = {
                    "#0": self.file_list.column("#0", "width"),
                    "description": self.file_list.column("description", "width"),
                    "date_modified": self.file_list.column("date_modified", "width")
                }

                abs_current_displayed_path = os.path.abspath(self.currently_displayed_folder_in_file_list)
                abs_backup_dir_path = os.path.abspath(os.path.join(self.base_path, BACKUP_FOLDER_BASENAME))
                is_backup_folder_displayed = os.path.normcase(abs_current_displayed_path) == os.path.normcase(abs_backup_dir_path)

                setting_key_to_save = "backup_list_column_widths" if is_backup_folder_displayed else "file_list_column_widths"
                
                self.db.set_setting(setting_key_to_save, json.dumps(current_col_widths))
                print(f"🔸 BİLGİ: Dosya listesi sütun genişlikleri '{setting_key_to_save}' anahtarına kaydedildi.")
            except Exception as e:
                print(f"❗ HATA: Dosya listesi sütun genişlikleri kaydedilemedi: {e}")
        else:
            print("🔸 BİLGİ: Geçerli bir klasör dosya listesinde görüntülenmediği veya file_list widget'ı mevcut olmadığı için sütun genişlikleri kaydedilmedi.")

        # PanedWindow (splitter) konumunu ve favori paneli görünürlüğünü kaydet
        sash_info_to_save = None
        fav_panel_is_visible_db_val = "0" # Varsayılan: gizli

        # Önce paned_window nesnesinin varlığını ve widget'ın hala var olup olmadığını kontrol et
        if hasattr(self, 'paned_window') and self.paned_window is not None:
            # print(f"DEBUG: Kapatma sırasında self.paned_window type: {type(self.paned_window)}") # İsteğe bağlı debug
            try:
                # winfo_exists() çağrısı da widget yok edilmişse TclError verebilir
                if self.paned_window.winfo_exists():
                    # 1. Favori panelinin görünürlüğünü belirle
                    current_panes_from_widget = []
                    try:
                        # panes() metodu AttributeError veya TclError verebilir
                        current_panes_from_widget = self.paned_window.panes()
                        if self.favorites_pane and self.favorites_pane.winfo_exists():
                            if str(self.favorites_pane) in current_panes_from_widget:
                                fav_panel_is_visible_db_val = "1"
                    except (tk.TclError, AttributeError) as e_panes_check:
                        print(f"❗ UYARI: Kapatma sırasında PanedWindow.panes() ile favori görünürlüğü kontrol edilirken hata: {type(e_panes_check).__name__} - {e_panes_check}")
                        # fav_panel_is_visible_db_val "0" olarak kalır (varsayılan)

                    # 2. Bölme (sash) konumlarını almayı dene
                    sash_data = {}
                    # .sashes() metodunu çağırmaktan kaçınıyoruz çünkü kapatma sırasında AttributeError veriyor.
                    # Bunun yerine doğrudan .sashpos() kullanmayı deneyeceğiz.
                    
                    try:
                        # İlk bölmenin (ağaç ve dosya listesi arası) konumunu almayı dene.
                        # Bu bölme, paned_window işlevselse her zaman var olmalıdır.
                        sash_data["pos0"] = str(self.paned_window.sashpos(0))

                        # Eğer favori panelinin görünür olduğu belirlendiyse, ikinci bölmenin konumunu almayı dene.
                        if fav_panel_is_visible_db_val == "1":
                            try:
                                # Bu bölme dosya listesi ve favoriler paneli arasındadır.
                                # sashpos(1) çağrısı, eğer sadece bir bölme varsa (örn. favoriler paneli
                                # bir şekilde kaldırıldıysa ama fav_panel_is_visible_val hala "1" ise)
                                # IndexError veya TclError verebilir.
                                sash_data["pos1"] = str(self.paned_window.sashpos(1))
                            except (tk.TclError, AttributeError, IndexError) as e_sashpos1:
                                print(f"❗ UYARI: Kapatma sırasında PanedWindow.sashpos(1) hatası (favoriler görünürken bekleniyordu): {type(e_sashpos1).__name__} - {e_sashpos1}")
                                # pos1 alınamazsa, en azından pos0 kaydedilmiş olabilir.
                        
                        if sash_data: # En azından pos0 alınabildiyse
                            sash_info_to_save = json.dumps(sash_data)
                            
                    except (tk.TclError, AttributeError, IndexError) as e_sashpos0:
                        # Bu, genellikle paned_window'un artık geçerli olmadığı anlamına gelir.
                        print(f"❗ UYARI: Kapatma sırasında PanedWindow.sashpos(0) (birincil bölme) hatası: {type(e_sashpos0).__name__} - {e_sashpos0}")
                        sash_info_to_save = None # Birincil bölme konumu alınamazsa, hiçbir şeyi kaydetme.
                else: # winfo_exists() false döndürdü
                    print("❗ UYARI: Kapatma sırasında PanedWindow.winfo_exists() false döndü. Konum ve görünürlük kaydedilemiyor.")

            except tk.TclError as e_winfo_exists_tcl: # self.paned_window.winfo_exists() TclError verdiyse
                print(f"❗ UYARI: Kapatma sırasında PanedWindow.winfo_exists() TclError verdi: {e_winfo_exists_tcl}. Konum ve görünürlük kaydedilemiyor.")
            except Exception as e_pw_general_processing:
                # PanedWindow işlemleri sırasında beklenmedik bir genel hata (yukarıdaki spesifik except'ler tarafından yakalanmayan)
                print(f"❗ HATA: PanedWindow bilgileri işlenirken genel iç hata (kapatma sırasında): {type(e_pw_general_processing).__name__} - {e_pw_general_processing}")
                # import traceback # Gerekirse daha fazla detay için traceback'i yazdırabilirsiniz
                # print(traceback.format_exc())
                sash_info_to_save = None # Güvenlik için sıfırla
                # fav_panel_is_visible_db_val varsayılan değerinde ("0") kalır veya önceki try-except'ten gelen değer olur.
        else:
            print("❗ UYARI: self.paned_window tanımlı değil, None veya widget kapatma sırasında zaten yok edilmiş. Konum ve favori görünürlüğü kaydedilemiyor.")

        # Ayarları veritabanına kaydet
        if sash_info_to_save:
            self.db.set_setting("main_paned_window_sashes", sash_info_to_save)
            print(f"🔸 BİLGİ: PanedWindow bölme konumları kaydedildi: {sash_info_to_save}")
        else:
            # Eğer sash bilgisi alınamadıysa, eski (muhtemelen bozuk) ayarı silmek bir seçenek olabilir,
            # ya da hiçbir şey yapmamak (mevcut davranış). Şimdilik bir şey yapmayalım.
            # self.db.delete_setting("main_paned_window_sashes")
            print("🔸 BİLGİ: PanedWindow bölme konumları bu oturum için kaydedilemedi veya alınamadı.")

        self.db.set_setting("favorites_panel_visible", fav_panel_is_visible_db_val)
        print(f"🔸 BİLGİ: Favori paneli görünürlüğü kaydedildi: {fav_panel_is_visible_db_val}")

        print("🚩 Uygulama kapatılıyor, veritabanı bağlantısı kapatılıyor.")
        if hasattr(self, 'db') and self.db: # db örneği varsa kapat
            self.db._close() # Veritabanı bağlantısını kapat
        self.destroy()   # Pencereyi yok et

    def _apply_saved_sash_position(self, manage_visibility=True):
        """Kaydedilmiş PanedWindow splitter konumunu uygular."""
        if not hasattr(self, 'paned_window') or not self.paned_window: # Önce paned_window var mı kontrol et
            print("❗ UYARI: _apply_saved_sash_position çağrıldı ancak paned_window mevcut değil.")
            return

        if manage_visibility:
            favorites_visible_setting = self.db.get_setting("favorites_panel_visible", "0") == "1"
            is_fav_pane_currently_in_panes = False
            if self.favorites_pane and self.paned_window.winfo_exists(): # winfo_exists paned_window için de geçerli
                try:
                    is_fav_pane_currently_in_panes = str(self.favorites_pane) in self.paned_window.panes()
                except (tk.TclError, AttributeError): # panes() metodu hata verirse (örn. pencere hazır değilken)
                    pass

            if favorites_visible_setting and not is_fav_pane_currently_in_panes:
                if self.favorites_pane: # Ensure favorites_pane itself exists
                    try:
                        self.paned_window.add(self.favorites_pane, weight=1) # Önce ekle
                        # self.paned_window.pane(self.favorites_pane, minsize=150) # HATA: unknown option -minsize
                        self.favorites_manager._populate_favorites_list() # FavoritesManager üzerinden çağır
                    except tk.TclError as e_add:
                        if "already managed" in str(e_add).lower() or "already added" in str(e_add).lower():
                            print(f"🔸 BİLGİ: _apply_saved_sash_position: Favori paneli zaten ekli/yönetiliyor: {e_add}")
                        else:
                            print(f"❗ HATA: _apply_saved_sash_position: Favori paneli eklenirken TclError: {e_add}")
            elif not favorites_visible_setting and is_fav_pane_currently_in_panes:
                if self.favorites_pane:
                    try:
                        self.paned_window.forget(self.favorites_pane)
                    except tk.TclError as e_forget:
                        print(f"❗ HATA: _apply_saved_sash_position içinde favori paneli kaldırılırken: {e_forget}")

        # PanedWindow'un panelleri ekledikten veya çıkardıktan sonra kendini güncellemesi için
        # update_idletasks() çağrısı yapıyoruz. sashpos uygulamadan önce UI'ın yerleşmesini sağlamak önemli.
        # Küçük bir after() gecikmesi, özellikle başlangıçta UI'ın tam olarak hazır olmasına yardımcı olabilir.
        try:
            # self.paned_window.update_idletasks() # Bu zaten vardı
            self.paned_window.update_idletasks() # PanedWindow yapısını güncelle
        except (tk.TclError, AttributeError) as e_update:
            print(f"❗ UYARI: _apply_saved_sash_position içinde paned_window.update_idletasks() hatası: {e_update}")
            return # Güncelleme başarısız olursa devam etmenin anlamı yok

        saved_sashes_json = self.db.get_setting("main_paned_window_sashes")
        if saved_sashes_json:
            try:
                sash_info = json.loads(saved_sashes_json)
                if isinstance(sash_info, dict):
                    # .sashes() metoduna güvenmek yerine doğrudan sashpos kullanacağız.
                    
                    # sashpos uygulamadan önce UI'ın biraz daha yerleşmesini bekle
                    # Bu, özellikle başlangıçta panellerin doğru boyutlanmasına yardımcı olabilir.
                    self.after(10, lambda: self._apply_sash_positions_after_delay(sash_info)) # 10ms gecikme ile yeni bir metoda yönlendir
                    return # Ana metottan çık

            except (ValueError, json.JSONDecodeError) as e_json:
                print(f"❗ HATA: Kayıtlı PanedWindow konumları JSON olarak çözümlenemedi ({saved_sashes_json}): {e_json}")
            except Exception as e_general_apply:
                 print(f"❗ HATA: Kayıtlı PanedWindow konumları ({saved_sashes_json}) uygulanırken genel hata: {e_general_apply}")

    def _apply_sash_positions_after_delay(self, sash_info):
        """Kısa bir gecikmeden sonra sash pozisyonlarını uygular."""
        if not hasattr(self, 'paned_window') or not self.paned_window or not self.paned_window.winfo_exists():
            print("❗ UYARI: _apply_sash_positions_after_delay çağrıldı ancak paned_window mevcut değil.")
            return

        try:
            self.paned_window.update_idletasks() # Değerlerin yansıması için tekrar güncelle

            # Bölme 0'ı uygula (varsa)
            if "pos0" in sash_info:
                try:
                    self.paned_window.sashpos(0, int(sash_info["pos0"]))
                    applied_pos0 = sash_info['pos0']
                    # print(f"🔸 BİLGİ: PanedWindow.sashpos(0, {applied_pos0}) çağrıldı.")
                    # Hemen sonra oku
                    self.paned_window.update_idletasks() 
                    current_sash0_val = self.paned_window.sashpos(0)
                    # print(f" DEBUG: sashpos(0) çağrısından hemen sonra okunan değer: {current_sash0_val}")
                    if int(current_sash0_val) != int(applied_pos0):
                        print(f"❗ UYARI: sashpos(0) ayarlanan ({applied_pos0}) ve okunan ({current_sash0_val}) değerler farklı!")
                except (tk.TclError, AttributeError, IndexError) as e_sp0:
                    print(f"❗ UYARI: Kayıtlı PanedWindow.sashpos(0) uygulanamadı: {type(e_sp0).__name__} - {e_sp0}")

            # Favori panelinin şu anda PanedWindow'un bir parçası olup olmadığını kontrol et
            # Bu, sashpos(1)'i ayarlamadan önce önemlidir.
            is_fav_pane_actually_in_panes_now = False
            if self.favorites_pane and self.paned_window.winfo_exists():
                try:
                    is_fav_pane_actually_in_panes_now = str(self.favorites_pane) in self.paned_window.panes()
                except (tk.TclError, AttributeError):
                    pass
    
            # Bölme 1'i uygula (varsa VE favoriler paneli görünürse)
            if "pos1" in sash_info and is_fav_pane_actually_in_panes_now:
                try:
                    self.paned_window.sashpos(1, int(sash_info["pos1"]))
                    applied_pos1 = sash_info['pos1']
                    # print(f"BİLGİ: PanedWindow.sashpos(1, {applied_pos1}) çağrıldı.")
                    # Hemen sonra oku (hem pos0 hem pos1) - pos1 ayarının pos0'ı bozup bozmadığını kontrol etmek için
                    self.paned_window.update_idletasks() 
                    current_sash0_after_pos1 = self.paned_window.sashpos(0)
                    current_sash1_val = self.paned_window.sashpos(1)
                    #print(f"DEBUG: sashpos(1) çağrısından sonra okunan değerler: pos0={current_sash0_after_pos1}, pos1={current_sash1_val}")
                    if int(current_sash1_val) != int(applied_pos1) and int(current_sash0_after_pos1) != 0 : # Eğer pos0 sıfırlanmadıysa pos1'i kontrol et
                        print(f"❗ UYARI: sashpos(1) ayarlanan ({applied_pos1}) ve okunan ({current_sash1_val}) değerler farklı!")
                    if int(current_sash0_after_pos1) == 0 and int(sash_info.get("pos0", -1)) != 0 : # pos0'ın sıfırlanıp sıfırlanmadığını kontrol et
                        print(f"❗ UYARI: sashpos(1) ayarlandıktan sonra sashpos(0) SIFIR oldu! (Ayarlanan ilk pos0: {sash_info.get('pos0')})")
                except (tk.TclError, AttributeError, IndexError) as e_sp1:
                    print(f"❗ UYARI: Kayıtlı PanedWindow.sashpos(1) uygulanamadı (favoriler görünürken): {type(e_sp1).__name__} - {e_sp1}")
            elif "pos1" in sash_info and not is_fav_pane_actually_in_panes_now: # Favori paneli görünür değilse pos1'i uygulamadık
                print(f"🔸 BİLGİ: Kayıtlı pos1 ({sash_info.get('pos1')}) var ama favori paneli şu anda görünür değil, bu yüzden uygulanmadı.")
        except Exception as e_general_apply: # This except should be aligned with the try
            print(f"❗ HATA: Kayıtlı PanedWindow konumları ({sash_info}) uygulanırken genel hata: {e_general_apply}") # saved_sashes_json -> sash_info

    # _setup_ui ve _setup_menus metodları UIManager sınıfına taşındı.

    # Dosya/Klasör listeleme ve gezinme metodları FileBrowser sınıfına taşındı.
    # Ancak ilk populate_tree çağrısı __init__ içinde App'ten yapılıyor.
    def select_folder(self):
        """Kullanıcının yeni bir ana klasör seçmesini sağlar."""
        # Başlangıç dizini olarak mevcut klasörü veya kullanıcı ev dizinini kullan
        initial_dir = self.current_folder or os.path.expanduser("~")
        new_folder = filedialog.askdirectory(
            title="Python Dosyalarının Bulunduğu Ana Klasörü Seçin", initialdir=initial_dir, parent=self)
        if new_folder:
            self.file_browser.select_folder() # select_folder artık FileBrowser'da, ama App'den çağrılabilir
                                            # veya doğrudan self.file_browser.select_folder() menüde kullanılabilir.
                                            # Şimdilik App'de bir sarmalayıcı bırakalım.
                                            # Daha iyisi: Menü komutunu doğrudan self.file_browser.select_folder yapalım.
                                            # Bu diff'te _setup_menus'ta bu düzeltme yapıldı.

    def on_file_double_click(self, event):
        """Dosya listesindeki bir öğeye çift tıklandığında dosyayı çalıştırır."""
        selected_item = self.file_list.focus() # Odaklanmış öğeyi al
        if not selected_item:
            return # Seçili öğe yoksa çık

        try:
            # Saklanan tam yolu al (values'daki ikinci öğe, indeks 1)
            item_tags = self.file_list.item(selected_item, "tags")
            file_path = self.file_list.item(selected_item, "values")[2] # İndeks 2'ye güncellendi

            if "zip_file" in item_tags:
                # messagebox.showinfo("Bilgi", f"'{os.path.basename(file_path)}' bir ZIP arşividir ve çalıştırılamaz.", parent=self)
                self.file_browser.show_zip_contents(file_path) # FileBrowser üzerinden
            elif "python_file" in item_tags: # ExecutionManager üzerinden
                self.execution_manager.run_python_file(file_path)
            elif "exe_file" in item_tags: # ExecutionManager üzerinden
                self.execution_manager.run_executable_file(file_path)
            elif "folder_item" in item_tags: # Handle double-click on a folder
                new_folder_path = self.file_list.item(selected_item, "values")[2]
                
                # self.current_folder = new_folder_path # Ana klasör (last_folder) artık burada değişmeyecek
                # self.db.set_setting("last_folder", self.current_folder) # Ana klasör (last_folder) artık burada değişmeyecek
  
                self.file_browser.populate_file_list(new_folder_path)
            elif "parent_folder_item" in item_tags: # Handle double-click on ".."
                parent_folder_path = self.file_list.item(selected_item, "values")[2]
                self.file_browser.populate_file_list(parent_folder_path)
            elif "other_file" in item_tags: # ExecutionManager üzerinden
                self.execution_manager.open_file_with_default_app(file_path)
            elif "mp3_file" in item_tags: # ExecutionManager üzerinden
                self.execution_manager.play_mp3_file(file_path)
            elif "db_file" in item_tags: # DB dosyaları için de varsayılan uygulama ile aç
                self.execution_manager.open_file_with_default_app(file_path)
            elif "json_file" in item_tags: # JSON dosyaları için özel görüntüleyici
                self._show_json_viewer(file_path)
            elif "markdown_file" in item_tags: # Markdown dosyaları için özel görüntüleyici
                self._show_markdown_viewer(file_path)
        except IndexError:
             print(f"❗ Hata: Dosya yolu alınamadı: {selected_item}")
             messagebox.showerror("Hata", "Seçili dosyanın yolu alınamadı.")
        except Exception as e:
             print(f"❗ Çift tıklama işlenirken hata: {e}")
             messagebox.showerror("Hata", f"Dosya çalıştırılırken beklenmedik hata:\n{e}")

    def sort_file_list_by_column(self, column_id):
        """Dosya listesini belirtilen sütuna göre sıralar."""
        if not hasattr(self, 'file_list') or not self.file_list.winfo_exists():
            return

        # 1. Sıralama düzenini belirle
        if self.file_list_sort_column == column_id:
            self.file_list_sort_order_asc = not self.file_list_sort_order_asc
        else:
            self.file_list_sort_order_asc = True
        self.file_list_sort_column = column_id

        # 2. Treeview'den verileri al
        items_data = []
        for item_id_str in self.file_list.get_children(''):
            item_info = self.file_list.item(item_id_str)
            items_data.append({
                'text': item_info['text'],
                'values': item_info['values'], # (description, date_modified, fullpath)
                'image': item_info['image'],
                'tags': item_info['tags']
            })

        # 3. Sıralama anahtar fonksiyonunu tanımla
        def get_sort_key(item):
            if column_id == "#0":  # Dosya Adı
                return item.get('text', '').lower()
            elif column_id == "description": # Açıklama
                desc = item['values'][0] if item.get('values') and len(item['values']) > 0 else ""
                return desc.lower() if desc else ""
            elif column_id == "date_modified": # Değiştirme Tarihi
                date_str = item['values'][1] if item.get('values') and len(item['values']) > 1 else "N/A"
                if date_str == "N/A":
                    # "N/A" değerlerini sıralamanın bir ucuna yerleştir
                    return "" if self.file_list_sort_order_asc else "~~~~~~~~~~~~~~~~~"
                return date_str # 'YYYY-MM-DD HH:MM:SS' formatı zaten string olarak sıralanabilir
            return item.get('text', '').lower() # Varsayılan

        # 4. Sırala
        items_data.sort(key=get_sort_key, reverse=not self.file_list_sort_order_asc)

        # 5. Yeniden doldur
        for item_id_old in self.file_list.get_children(''):
            self.file_list.delete(item_id_old)

        for data in items_data:
            self.file_list.insert('', tk.END, text=data['text'], values=data['values'], image=data['image'], tags=data['tags'])

        self._update_file_list_header_indicators()

    def _update_file_list_header_indicators(self):
        """Dosya listesi başlıklarındaki sıralama göstergelerini günceller."""
        if not hasattr(self, 'file_list') or not self.file_list.winfo_exists(): return
        headers_config = {"#0": "Dosya Adı", "description": "Açıklama", "date_modified": "Değiştirme Tarihi"}
        for col_id_key, base_text in headers_config.items():
            text_to_display = base_text
            if col_id_key == self.file_list_sort_column:
                text_to_display += " ▲" if self.file_list_sort_order_asc else " ▼"
            try: self.file_list.heading(col_id_key, text=text_to_display)
            except tk.TclError: pass # Widget yok edilmişse hata vermesini engelle

    # run_python_file ve run_executable_file metodları ExecutionManager sınıfına taşındı.
    # FavoritesManager içindeki _on_favorite_double_click metodu da ExecutionManager'ı kullanacak şekilde güncellenmeli.
    # Bu, ExecutionManager'ın __init__ içinde self.app.execution_manager = self şeklinde ayarlanmasıyla veya
    # FavoritesManager'a ExecutionManager örneğinin de geçirilmesiyle yapılabilir.
    # Şimdilik, FavoritesManager'daki run_python_file çağrısı self.app.run_python_file şeklinde kalacak
    # ve App sınıfı bu çağrıyı self.execution_manager.run_python_file'a yönlendirecek.
    # Daha temiz bir çözüm için FavoritesManager'a ExecutionManager'ı enjekte etmek daha iyi olurdu.
    # Ancak mevcut yapı için App üzerinden delegasyon daha basit.
    def run_python_file(self, file_path, source=None): # Delegasyon metodu
        self.execution_manager.run_python_file(file_path, source)

    def run_executable_file(self, file_path, source=None): # Delegasyon metodu
        self.execution_manager.run_executable_file(file_path, source)

    def show_file_context_menu(self, event):
        """Dosya listesinde sağ tıklandığında içerik menüsünü gösterir."""
        # Tıklanan satırı belirle
        selected_item = self.file_list.identify_row(event.y)
        if not selected_item:
            return # Boş alana tıklandıysa çık

        # Menüyü göstermeden önce tıklanan öğeyi seçili hale getir
        self.file_list.selection_set(selected_item)
        self.file_list.focus(selected_item)

        try:              
            # Seçili öğenin tam yolunu al (values'daki ikinci öğe)
            item_tags = self.file_list.item(selected_item, "tags")
            file_path = self.file_list.item(selected_item, "values")[2] # İndeks 2'ye güncellendi

            # Renkli context menu oluştur
            context_menu = ColoredContextMenu(self)

            item_tags = self.file_list.item(selected_item, "tags")
            file_path = self.file_list.item(selected_item, "values")[2] # İndeks 2'ye güncellendi

            # Renkli context menu oluştur
            context_menu = ColoredContextMenu(self)

            # --- Dosya Adı Değiştir seçeneği ---
            def rename_file_dialog(p=file_path, item=selected_item):
                current_name = os.path.basename(p)
                new_name = simpledialog.askstring("Dosya Adı Değiştir", f"Yeni dosya adını girin:", initialvalue=current_name, parent=self)
                if new_name and new_name != current_name:
                    new_path = os.path.join(os.path.dirname(p), new_name)
                    try:
                        os.rename(p, new_path)
                        # Dosya listesinde güncelle
                        self.file_list.item(item, text=new_name)
                        values = list(self.file_list.item(item, "values"))
                        values[2] = new_path
                        self.file_list.item(item, values=values)
                        self.status_label.config(text=f"Dosya adı değiştirildi: {new_name}")
                        self.db.add_history(f"Yeniden adlandırıldı: '{current_name}' -> '{new_name}' ({os.path.dirname(p)})", event_type="rename")
                    except Exception as e:
                        messagebox.showerror("Hata", f"Dosya adı değiştirilemedi:\n{e}", parent=self)

            context_menu.add_command(
                "✏️ Dosya Adı Değiştir...",
                rename_file_dialog,
                color="#00796B",
                bg_color="#E0F2F1",
                hover_color="#B2DFDB"
            )


            # Eğer seçilen dosya bir klasörse, "Klasör" seçeneğini ekle
            if os.path.isdir(file_path):
                context_menu.add_command(
                    "📂 Klasör Özellikleri",
                    lambda p=file_path: self.show_folder_properties(p),
                    color="#92540A",
                    bg_color="#FFEBD0",
                    hover_color="#FCB44F"
                )            
            
            context_menu.add_command("📂 Dosyaya Git", 
                               lambda p=file_path: self.file_browser.go_to_file(p),
                               color="#1976D2", 
                               bg_color="#E3F2FD",
                               hover_color="#BBDEFB")

            if "python_file" in item_tags:
                context_menu.add_command("🚀 Çalıştır", 
                                   lambda p=file_path: self.execution_manager.run_python_file(p),
                                   color="#2E7D32", 
                                   bg_color="#E8F5E8",
                                   hover_color="#C8E6C9")
                
                context_menu.add_separator()
                                
                context_menu.add_command("📝 Python Dosyasını Görüntüle", 
                                   lambda p=file_path: self._open_python_editor(p),
                                   color="#F57C00", 
                                   bg_color="#FFF3E0",
                                   hover_color="#FFE0B2")
                
                context_menu.add_command("💫 Python Proje Analizi", 
                                   lambda p=file_path: self.python_analyzer.analyze_python_file(p),
                                   color="#7B1FA2", 
                                   bg_color="#F3E5F5",
                                   hover_color="#E1BEE7")
                
                context_menu.add_command("📦 Dependency Analizi", 
                                   lambda p=file_path: self.show_dependency_analysis(p),
                                   color="#455A64", 
                                   bg_color="#ECEFF1",
                                   hover_color="#CFD8DC")
                
                context_menu.add_command("🔍 Python Metod Kontrolü", 
                                   lambda p=file_path: self.analyze_python_methods_for_path(p),
                                   color="#5D4037", 
                                   bg_color="#EFEBE9",
                                   hover_color="#D7CCC8")
                
                context_menu.add_separator()
                
                # Favoriler için renkli seçenekler
                if self.db.is_favorite(file_path):
                    context_menu.add_command("💔 Favorilerden Kaldır", 
                                       lambda p=file_path: self.favorites_manager._remove_from_favorites(p),
                                       color="#D32F2F", 
                                       bg_color="#FFEBEE",
                                       hover_color="#FFCDD2")
                else:
                    context_menu.add_command("❤️ Favorilere Ekle", 
                                       lambda p=file_path: self.favorites_manager._add_to_favorites(p),
                                       color="#C2185B", 
                                       bg_color="#FCE4EC",
                                       hover_color="#F8BBD9")
                
                context_menu.add_command("⚙️ EXE'ye Çevir", 
                                   lambda p=file_path: self.action_manager.convert_py_to_exe(p),
                                   color="#D84315", 
                                   bg_color="#FBE9E7",
                                   hover_color="#FFCCBC")
                context_menu.add_command("✏️ Açıklama Düzenle...", 
                                   lambda p=file_path, item=selected_item: self.file_browser.edit_description(p, item),
                                   color="#303F9F", 
                                   bg_color="#E8EAF6",
                                   hover_color="#C5CAE9")
        
            elif "exe_file" in item_tags:
                context_menu.add_command("🚀 Çalıştır", 
                                lambda p=file_path: self.execution_manager.run_executable_file(p),
                                color="#2E7D32", 
                                bg_color="#E8F5E8",
                                hover_color="#C8E6C9")
            
            elif "zip_file" in item_tags:
                context_menu.add_command("✏️ ZIP Adını Değiştir...", 
                                lambda p=file_path, item=selected_item: self.file_browser.rename_selected_file(p, item, "zip"),
                                color="#F57C00", 
                                bg_color="#FFF3E0",
                                hover_color="#FFE0B2")
            
            elif "other_file" in item_tags:
                context_menu.add_command("🔗 Aç (Varsayılan)", 
                                lambda p=file_path: self.execution_manager.open_file_with_default_app(p),
                                color="#1976D2", 
                                bg_color="#E3F2FD",
                                hover_color="#BBDEFB")
            
            elif "mp3_file" in item_tags:
                context_menu.add_command("🎵 MP3 Çal", 
                                lambda p=file_path: self.execution_manager.play_mp3_file(p),
                                color="#C2185B", 
                                bg_color="#FCE4EC",
                                hover_color="#F8BBD9")
            
            elif "db_file" in item_tags:
                context_menu.add_command("🔗 Aç (Varsayılan)", 
                                lambda p=file_path: self.execution_manager.open_file_with_default_app(p),
                                color="#1976D2", 
                                bg_color="#E3F2FD",
                                hover_color="#BBDEFB")
            elif "json_file" in item_tags:
                context_menu.add_command("📄 JSON Dosyasını Görüntüle", 
                                lambda p=file_path: self._show_json_viewer(p),
                                color="#FF6600", 
                                bg_color="#FFF8E6",
                                hover_color="#FFE0B2")
            elif "markdown_file" in item_tags:
                context_menu.add_command("📖 Markdown Dosyasını Görüntüle", 
                                lambda p=file_path: self._show_markdown_viewer(p),
                                color="#0366D6", 
                                bg_color="#F6F8FA",
                                hover_color="#E1E7ED")
                
                context_menu.add_command("🔗 Aç (Varsayılan)", 
                                lambda p=file_path: self.execution_manager.open_file_with_default_app(p),
                                color="#1976D2", 
                                bg_color="#E3F2FD",
                                hover_color="#BBDEFB")

            context_menu.add_separator()
            context_menu.add_command("🗑️ Sil...", 
                            lambda p=file_path, item=selected_item: self.file_browser.delete_file(p, item),
                            color="#D32F2F", 
                            bg_color="#FFEBEE",
                            hover_color="#FFCDD2")
            
            # Menüyü göster
            context_menu.popup(event.x_root, event.y_root)
            
        except Exception as e:
            print(f"❗ Context menü hatası: {e}")

    def _show_markdown_viewer(self, file_path):
        """Markdown dosyasını formatlanmış olarak gösteren pencere açar."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Markdown görüntüleyici penceresi
            md_window = tk.Toplevel(self)
            md_window.title(f"Markdown Görüntüleyici - {os.path.basename(file_path)}")
            md_window.resizable(True, True)
            
            # Geometri yönetimi
            self.load_or_center_window("markdown_viewer", md_window, 800, 600)
            
            def on_md_closing():
                geom = md_window.winfo_geometry()
                self.db.save_window_geometry("markdown_viewer", geom)
                md_window.destroy()
            
            md_window.protocol("WM_DELETE_WINDOW", on_md_closing)
            md_window.bind("<Escape>", lambda e: on_md_closing())
            
            # Ana frame
            main_frame = ttk.Frame(md_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Başlık
            title_label = ttk.Label(main_frame, text=f"📖 {os.path.basename(file_path)}", 
                                   font=("Arial", 12, "bold"))
            title_label.pack(pady=(0, 10))
            
            # Text widget ve scrollbar
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill="both", expand=True)
            
            text_widget = tk.Text(text_frame, font=("Segoe UI", 11), wrap=tk.WORD, 
                                 bg="#FFFFFF", fg="#24292E", relief="flat", bd=0)
            v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            
            text_widget.configure(yscrollcommand=v_scrollbar.set)
            
            # Grid layout
            text_widget.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            
            # Markdown formatlaması için tag'ler tanımla
            self._configure_markdown_tags(text_widget)
            
            # Markdown içeriğini formatla ve ekle
            self._format_markdown_content(text_widget, markdown_content)
            
            text_widget.configure(state="disabled")
            
            # Butonlar frame
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=(10, 10))
            
            # Ham metin göster/gizle butonu
            show_raw = tk.BooleanVar()
            def toggle_raw_view():
                text_widget.configure(state="normal")
                text_widget.delete("1.0", tk.END)
                
                if show_raw.get():
                    # Ham markdown metnini göster
                    text_widget.insert("1.0", markdown_content)
                    raw_button.configure(text="📖 Formatlanmış Görünüm")
                else:
                    # Formatlanmış görünümü göster
                    self._format_markdown_content(text_widget, markdown_content)
                    raw_button.configure(text="📝 Ham Metin")
                
                text_widget.configure(state="disabled")
            
            raw_button = ttk.Button(buttons_frame, text="📝 Ham Metin", command=toggle_raw_view)
            raw_button.pack(side="left", padx=(10, 10))
            
            # Kopyala butonu
            def copy_markdown():
                self.clipboard_clear()
                self.clipboard_append(markdown_content)
                messagebox.showinfo("Başarılı", "Markdown içeriği panoya kopyalandı!", parent=md_window)
            
            copy_button = ttk.Button(buttons_frame, text="📋 Kopyala", command=copy_markdown)
            copy_button.pack(side="left", padx=(10, 10))
            
            # Varsayılan uygulama ile aç butonu
            default_button = ttk.Button(buttons_frame, text="🔗 Varsayılan Uygulama", 
                                       command=lambda: self.execution_manager.open_file_with_default_app(file_path))
            default_button.pack(side="left")
            
            # Kapat butonu
            close_button = ttk.Button(buttons_frame, text="❌ Kapat", command=on_md_closing)
            close_button.pack(side="right", padx=(10, 10))
            
            # Modal pencere
            md_window.transient(self)
            md_window.grab_set()
            md_window.focus_set()
            
            # History'ye kaydet
            self.db.add_history(f"Markdown Görüntülendi: {file_path}", "markdown_viewer")
            
        except Exception as e:
            messagebox.showerror("Markdown Görüntüleme Hatası", 
                               f"Markdown dosyası görüntülenirken hata oluştu:\n{e}", 
                               parent=self)

    def _configure_markdown_tags(self, text_widget):
        """Markdown formatlaması için Text widget tag'lerini yapılandırır."""
        # Başlıklar
        text_widget.tag_configure("h1", font=("Segoe UI", 20, "bold"), foreground="#1A1A1A", spacing1=10, spacing3=5)
        text_widget.tag_configure("h2", font=("Segoe UI", 16, "bold"), foreground="#1A1A1A", spacing1=8, spacing3=4)
        text_widget.tag_configure("h3", font=("Segoe UI", 14, "bold"), foreground="#1A1A1A", spacing1=6, spacing3=3)
        text_widget.tag_configure("h4", font=("Segoe UI", 12, "bold"), foreground="#1A1A1A", spacing1=4, spacing3=2)
        text_widget.tag_configure("h5", font=("Segoe UI", 11, "bold"), foreground="#1A1A1A", spacing1=3, spacing3=2)
        text_widget.tag_configure("h6", font=("Segoe UI", 10, "bold"), foreground="#6A737D", spacing1=2, spacing3=1)
        
        # Kod blokları
        text_widget.tag_configure("code_block", font=("Consolas", 10), background="#F6F8FA", 
                                 relief="solid", borderwidth=1, lmargin1=20, lmargin2=20, 
                                 rmargin=20, spacing1=5, spacing3=5)
        
        # Satır içi kod
        text_widget.tag_configure("inline_code", font=("Consolas", 10), background="#F3F4F6", 
                                 relief="solid", borderwidth=1)
        
        # Kalın metin
        text_widget.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        
        # İtalik metin
        text_widget.tag_configure("italic", font=("Segoe UI", 11, "italic"))
        
        # Liste öğeleri
        text_widget.tag_configure("list_item", lmargin1=30, lmargin2=50, spacing1=2)
        
        # Alıntı
        text_widget.tag_configure("blockquote", lmargin1=20, lmargin2=20, rmargin=20, 
                                 background="#F6F8FA", relief="solid", borderwidth=1, 
                                 foreground="#6A737D", spacing1=5, spacing3=5)
        
        # Link
        text_widget.tag_configure("link", foreground="#0366D6", underline=True)
        
        # Yatay çizgi
        text_widget.tag_configure("hr", relief="solid", borderwidth=1, background="#E1E4E8")

    def _format_markdown_content(self, text_widget, content):
        """Markdown içeriğini Text widget'a formatlanmış olarak ekler."""
        import re
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Kod blokları (```)
            if line.strip().startswith('```'):
                # Kod bloğu başlangıcı
                lang = line.strip()[3:].strip()
                code_lines = []
                i += 1
                
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code_text = '\n'.join(code_lines) + '\n'
                    if lang:
                        text_widget.insert(tk.END, f"[{lang}]\n", "inline_code")
                    text_widget.insert(tk.END, code_text, "code_block")
                i += 1
                continue
            
            # Başlıklar
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level <= 6:
                    header_text = line.lstrip('#').strip() + '\n'
                    text_widget.insert(tk.END, header_text, f"h{level}")
                    i += 1
                    continue
            
            # Yatay çizgi
            if line.strip() in ['---', '***', '___']:
                text_widget.insert(tk.END, '\n' + '─' * 50 + '\n\n', "hr")
                i += 1
                continue
            
            # Alıntı
            if line.startswith('>'):
                quote_lines = []
                while i < len(lines) and lines[i].startswith('>'):
                    quote_lines.append(lines[i][1:].strip())
                    i += 1
                
                quote_text = '\n'.join(quote_lines) + '\n\n'
                text_widget.insert(tk.END, quote_text, "blockquote")
                continue
            
            # Liste öğeleri
            if re.match(r'^\s*[-*+]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                # Madde işareti veya numaralı liste
                indent = len(line) - len(line.lstrip())
                if re.match(r'^\s*[-*+]\s+', line):
                    bullet = '•'
                    content_part = re.sub(r'^\s*[-*+]\s+', '', line)
                else:
                    match = re.match(r'^\s*(\d+)\.\s+', line)
                    bullet = f"{match.group(1)}."
                    content_part = re.sub(r'^\s*\d+\.\s+', '', line)
                
                list_text = f"{' ' * (indent // 2)}{bullet} {content_part}\n"
                text_widget.insert(tk.END, list_text, "list_item")
                i += 1
                continue
            
            # Normal paragraf - satır içi formatlamalar
            formatted_line = self._format_inline_markdown(line + '\n')
            text_widget.insert(tk.END, formatted_line[0], formatted_line[1] if len(formatted_line) > 1 else None)
            
            i += 1

    def _format_inline_markdown(self, text):
        """Satır içi markdown formatlamalarını uygular."""
        import re
        
        # Satır içi kod (`kod`)
        text = re.sub(r'`([^`]+)`', lambda m: f"[CODE]{m.group(1)}[/CODE]", text)
        
        # Kalın metin (**bold** veya __bold__)
        text = re.sub(r'\*\*([^*]+)\*\*', lambda m: f"[BOLD]{m.group(1)}[/BOLD]", text)
        text = re.sub(r'__([^_]+)__', lambda m: f"[BOLD]{m.group(1)}[/BOLD]", text)
        
        # İtalik metin (*italic* veya _italic_)
        text = re.sub(r'\*([^*]+)\*', lambda m: f"[ITALIC]{m.group(1)}[/ITALIC]", text)
        text = re.sub(r'_([^_]+)_', lambda m: f"[ITALIC]{m.group(1)}[/ITALIC]", text)
        
        # Linkler [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', lambda m: f"[LINK]{m.group(1)}[/LINK]", text)
        
        # Basit formatting için tuple döndür
        if any(tag in text for tag in ['[CODE]', '[BOLD]', '[ITALIC]', '[LINK]']):
            return (text, "formatted")
        else:
            return (text,)

    def _show_json_viewer(self, file_path):
        """JSON dosyasını formatlı olarak gösteren pencere açar."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            
            # JSON'u parse edip güzelce formatla
            try:
                import json
                parsed_json = json.loads(json_content)
                formatted_content = json.dumps(parsed_json, indent=2, ensure_ascii=False, sort_keys=True)
            except json.JSONDecodeError:
                # Eğer geçerli JSON değilse ham içeriği göster
                formatted_content = json_content
            
            # JSON görüntüleyici penceresi
            json_window = tk.Toplevel(self)
            json_window.title(f"JSON Görüntüleyici - {os.path.basename(file_path)}")
            json_window.resizable(True, True)
            
            # Geometri yönetimi
            self.load_or_center_window("json_viewer", json_window, 700, 500)
            
            def on_json_closing():
                geom = json_window.winfo_geometry()
                self.db.save_window_geometry("json_viewer", geom)
                json_window.destroy()
            
            json_window.protocol("WM_DELETE_WINDOW", on_json_closing)
            json_window.bind("<Escape>", lambda e: on_json_closing())
            
            # Ana frame
            main_frame = ttk.Frame(json_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Başlık
            title_label = ttk.Label(main_frame, text=f"📄 {os.path.basename(file_path)}", 
                                   font=("Arial", 12, "bold"))
            title_label.pack(pady=(0, 10))
            
            # Text widget ve scrollbar
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill="both", expand=True)
            
            text_widget = tk.Text(text_frame, font=("Consolas", 10), wrap=tk.NONE)
            v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            h_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=text_widget.xview)
            
            text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Grid layout
            text_widget.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            
            # JSON içeriğini ekle
            text_widget.insert("1.0", formatted_content)
            text_widget.configure(state="disabled")
            
            # Butonlar frame
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=(10, 10))
            
            # Kopyala butonu
            def copy_json():
                self.clipboard_clear()
                self.clipboard_append(formatted_content)
                messagebox.showinfo("Başarılı", "JSON içeriği panoya kopyalandı!", parent=json_window)
            
            copy_button = ttk.Button(buttons_frame, text="📋 Kopyala", command=copy_json)
            copy_button.pack(side="left", padx=(10, 10))
            
            # Varsayılan uygulama ile aç butonu
            default_button = ttk.Button(buttons_frame, text="🔗 Varsayılan Uygulama", 
                                       command=lambda: self.execution_manager.open_file_with_default_app(file_path))
            default_button.pack(side="left")
            
            # Kapat butonu
            close_button = ttk.Button(buttons_frame, text="❌ Kapat", command=on_json_closing)
            close_button.pack(side="right", padx=(10, 10))
            
            # Modal pencere
            json_window.transient(self)
            json_window.grab_set()
            json_window.focus_set()
            
            # History'ye kaydet
            self.db.add_history(f"JSON Görüntülendi: {file_path}", "json_viewer")
            
        except Exception as e:
            messagebox.showerror("JSON Görüntüleme Hatası", 
                               f"JSON dosyası görüntülenirken hata oluştu:\n{e}", 
                               parent=self)

    def _open_python_editor(self, file_path):
        """Python editörü penceresi açar."""
        try:
            editor = PythonEditor(self, file_path, false)
            # History'e kaydet
            self.db.add_history(f"Python Editörü: {file_path}", "python_editor")
        except Exception as e:
            messagebox.showerror("Hata", f"Python editörü açılırken hata oluştu:\n{e}", parent=self)

    @staticmethod
    def format_file_size(size_bytes):
        """Dosya boyutunu uygun birimle (KB, MB, GB) formatlı string olarak döndürür."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:,.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):,.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):,.2f} GB"
        
    def show_folder_properties(self, folder_path):
        def calculate_folder_size(folder_path):
            """Calculate the total size of a folder, including its files and subfolders."""
            total_size = 0
            total_python_size = 0
            total_zip_size = 0
            file_count = 0
            py_file_count = 0  
            zip_file_count = 0
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    if os.path.splitext(file)[1].lower() == ".py":
                        py_file_count += 1
                        total_python_size += os.path.getsize(file_path)
                    if os.path.splitext(file)[1].lower() == ".zip":
                        zip_file_count += 1
                        total_zip_size += os.path.getsize(file_path)
            return total_size, total_python_size, file_count, py_file_count, zip_file_count, total_zip_size

        """Open a folder dialog, calculate its size, and display the result."""
        # print(f"🔸 '{folder_path}' Klasör özellikleri hesaplanıyor... ")
        folder_size, total_python_size, file_count, py_file_count, zip_file_count, total_zip_size = calculate_folder_size(folder_path)
        sonuc = self.format_file_size(folder_size)
        sonuc = f"Folder: {folder_path}\n\n" + \
                 f"Number of files: {file_count:,}\nTotal Folder Size: {self.format_file_size(folder_size)}\n\n" + \
                 f"Number of Python files: {py_file_count:,}\nTotal Python Size: {self.format_file_size(total_python_size)}\n\n" + \
                 f"Number of ZIP files: {zip_file_count:,}\nTotal ZIP Size: {self.format_file_size(total_zip_size)}"

        messagebox.showinfo("Folder Properties",  sonuc)

    def show_dir_context_menu(self, event):
        """Klasör ağacında sağ tıklandığında içerik menüsünü gösterir."""
        item_id = self.dir_tree.identify_row(event.y)
        if not item_id:
            return

        self.dir_tree.selection_set(item_id)
        self.dir_tree.focus(item_id)

        try:
            item_path = self.dir_tree.item(item_id, "values")[0]
            if os.path.isdir(item_path):
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="🗜️ Sıkıştır (ZIP)...",
                                          command=lambda p=item_path: self.action_manager.prompt_compression_options(p)) # ActionManager üzerinden
                context_menu.add_command(label="🗂️ Özellikler...",
                                          command=lambda p=item_path: self.show_folder_properties(p))
                context_menu.tk_popup(event.x_root, event.y_root)
        except IndexError:
            print(f"❗ Hata: Klasör ağacı sağ tık menüsü için yol alınamadı: {item_id}")
        except Exception as e:
            print(f"❗ Klasör ağacı sağ tık menüsü oluşturulurken hata: {e}")

    # Sıkıştırma ve EXE'ye çevirme metodları ActionManager sınıfına taşındı.
    # Aşağıdakiler, operations.py'den geri çağrılar için delegasyon metodlarıdır.

    def _handle_compression_success(self, folder_name, abs_zip_file_path, abs_backup_dir_path):
        self.action_manager._handle_compression_success(folder_name, abs_zip_file_path, abs_backup_dir_path)

    def _handle_compression_error(self, folder_name, e, abs_zip_file_path):
        self.action_manager._handle_compression_error(folder_name, e, abs_zip_file_path)

    def _handle_exe_conversion_success(self, original_py_name, exe_path):
        self.action_manager._handle_exe_conversion_success(original_py_name, exe_path)

    def _handle_exe_conversion_error(self, original_py_name, error_message):
        self.action_manager._handle_exe_conversion_error(original_py_name, error_message)

    def _finalize_exe_conversion_ui(self):
        self.action_manager._finalize_exe_conversion_ui()

    def _finalize_search_ui(self):
        self.search_manager._finalize_search_ui()

    def _handle_search_error(self, error):
        self.search_manager._handle_search_error(error)

    def _show_search_results(self, found_files_details, pattern, root_folder_searched):
        self.search_manager._show_search_results(found_files_details, pattern, root_folder_searched)

    def _finalize_word_search_ui(self):
        self.search_manager._finalize_word_search_ui()

    def _handle_word_search_error(self, error):
        self.search_manager._handle_word_search_error(error)

    def _show_word_search_results(self, found_items, search_word, root_folder_searched):
        self.search_manager._show_word_search_results(found_items, search_word, root_folder_searched)

    def edit_description(self, file_path, item_id):
        self.file_browser.edit_description(file_path, item_id) # FileBrowser üzerinden (Delegasyon)

    def open_window_settings_dialog(self):
        """Pencere geometrisi ayarlarını yönetmek için pencere açar. (Eski adı: show_window_settings)"""
        settings_win = tk.Toplevel(self)
        settings_win.title("Pencere Ayarları")
        settings_win.geometry("400x300") # Varsayılan boyut
        settings_win.transient(self)
        # settings_win.withdraw() # Gizlemeye gerek yok

        # Geometriyi yükle veya ortala
        self.load_or_center_window("window_settings", settings_win, 400, 300)
        
        # Kapatma işleyicisi
        def close_settings():
            geom = settings_win.winfo_geometry()
            self.db.save_window_geometry("window_settings", geom)
            settings_win.destroy()

        main_frame = ttk.Frame(settings_win, padding="10")

        # Geometri yüklendikten SONRA grab_set çağırılır
        settings_win.grab_set()
        settings_win.focus_set()       # Odağı bu pencereye ver
        # 'X' düğmesi ile kapatıldığında da geometriyi kaydet
        settings_win.protocol("WM_DELETE_WINDOW", close_settings)
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.rowconfigure(1, weight=1) # Listbox genişlesin
        main_frame.columnconfigure(0, weight=1) # Listbox genişlesin

        ttk.Label(main_frame, text="Boyutu ve konumu sıfırlanacak pencereyi seçin:").grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky='w')        # Veritabanı anahtarları ve kullanıcı dostu isimler
        window_map = {
            "main": "Ana Pencere",
            "history": "Geçmiş İşlemler",
            "themes": "Tema Yönetimi",
            "window_settings": "Pencere Ayarları", 
            "search_results": "Dosya Arama Sonuçları",
            "word_search_results": "Kelime Arama Sonuçları",
            "zip_contents": "ZIP Dosyası İçeriği",
            "history_stats": "Geçmiş İstatistikleri", 
            "python_analyzer": "Python Analiz Penceresi",
            "dependency_analyzer": "Dependency Analiz Penceresi",
            "help": "Yardım Penceresi",
            "project_main_files": "Metod Analizi: Proje Ana Dosyaları",
            "excluded_methods": "Metod Analizi: Hariç Tutulan Metodlar",
            "method_occurrences": "Metod Analizi: Metodların Geçişleri",
            "method_analysis": "Metod Analizi: Detaylı Metod Analizi",
            "python_editor": "Python Editörü",
            "window_settings": "Pencere Ayarları"
        }
        # Ters map (isimden anahtara)
        name_to_key_map = {v: k for k, v in window_map.items()}

        listbox = tk.Listbox(main_frame, exportselection=False)
        listbox.grid(row=1, column=0, padx=(0, 5), sticky='nsew')
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky='ns')

        for display_name in window_map.values():
            listbox.insert(tk.END, display_name)

        def reset_selected_geometry():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Seçim Yok", "Lütfen sıfırlamak için bir pencere seçin.", parent=settings_win)
                return
            selected_name = listbox.get(selected_indices[0])
            window_key = name_to_key_map.get(selected_name)
            if window_key:
                self.db.delete_window_geometry(window_key)
                messagebox.showinfo("Başarılı", f"'{selected_name}' için kaydedilmiş boyut ve konum sıfırlandı.\nPencere bir sonraki açılışta varsayılan ayarlarla gösterilecek.", parent=settings_win)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky='e')

        reset_button = ttk.Button(button_frame, text="Seçili Pencereyi Sıfırla", command=reset_selected_geometry)
        reset_button.pack(side=tk.LEFT, padx=(0, 10))

        close_button = ttk.Button(button_frame, text="Kapat", command=close_settings)
        close_button.pack(side=tk.LEFT)

        settings_win.bind("<Escape>", lambda e: close_settings())

        self.wait_window(settings_win)

    def show_help(self):
        """Yardım penceresini gösterir."""
        # Yardım içeriğini tarayıcıda aç
        import os, webbrowser
        html_path = os.path.join(self.base_path, 'timer_help.html')
        if os.path.exists(html_path):
            webbrowser.open_new_tab(f'file:///{html_path.replace('\\','/')}')
        else:
            messagebox.showerror("Yardım Bulunamadı", f"'{html_path}' dosyası bulunamadı.", parent=self)

    # --- MP3 Kontrol Metodları ---
    def _format_time(self, seconds):
        """Saniyeyi MM:SS formatına çevirir."""
        if seconds is None or seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def show_mp3_controls(self, duration_sec, filename):
        """MP3 kontrol elemanlarını gösterir ve ayarlar."""
        self.status_label.pack_forget() # Varsayılan durum etiketini gizle
        self.mp3_controls_frame.pack(side=tk.LEFT, padx=(5,0), pady=2, fill=tk.X, expand=True)

        self.mp3_seek_scale.config(to=duration_sec if duration_sec > 0 else 100.0) # to=0 hata verir
        self.mp3_seek_scale.set(0)
        
        formatted_duration = self._format_time(duration_sec if duration_sec > 0 else 0)
        self.mp3_time_label.config(text=f"00:00 / {formatted_duration}")
        
        # Dosya adını kısaltarak göster (çok uzunsa)
        max_len = 20
        display_filename = (filename[:max_len-3] + "...") if len(filename) > max_len else filename
        self.mp3_current_file_label.config(text=f"Çalınıyor: {display_filename}")

        self.update_mp3_play_pause_button_state(paused=False)
        self._start_mp3_polling()

    def hide_mp3_controls(self):
        """MP3 kontrol elemanlarını gizler."""
        self._stop_mp3_polling()
        self.mp3_controls_frame.pack_forget()
        self.status_label.config(text="Hazır.") # Durum etiketini varsayılana döndür
        self.status_label.pack(side=tk.LEFT, padx=(5,0), pady=2) # Varsayılanı tekrar göster
        self.mp3_current_file_label.config(text="")

    def update_mp3_play_pause_button_state(self, paused):
        """Oynat/Duraklat butonunun ikonunu ve metnini günceller."""
        if paused:
            self.mp3_play_pause_button.config(image=self.play_button_icon)
        else:
            self.mp3_play_pause_button.config(image=self.pause_button_icon)

    def on_mp3_play_pause(self):
        self.execution_manager.toggle_mp3_play_pause()

    def on_mp3_stop(self):
        self.execution_manager.stop_mp3() # Bu metod hide_mp3_controls'ü çağıracak

    def on_mp3_seek_start(self, event=None):
        self._user_is_seeking_mp3 = True

    def on_mp3_seek_end(self, event=None):
        if self._user_is_seeking_mp3:
            seek_seconds = float(self.mp3_seek_scale.get())
            self.execution_manager.seek_mp3(seek_seconds)

            # Kullanıcı fareyi bıraktığında kaydırma çubuğunu hemen istenen konuma ayarla.
            # Bu, polling'in eski bir değeri göstermesini engeller.
            self._programmatic_scale_update = True # Kendi command'ının gereksiz tetiklenmesini engelle
            self.mp3_seek_scale.set(seek_seconds)
            self._programmatic_scale_update = False

            # Kullanıcı seek yaptıktan sonra zaman etiketini hemen güncelle
            duration = self.execution_manager.mp3_duration_sec
            self.mp3_time_label.config(text=f"{self._format_time(seek_seconds)} / {self._format_time(duration if duration > 0 else 0)}")
        self._user_is_seeking_mp3 = False


    def on_mp3_seek_user_initiated(self, value_str):
        """Scale komutu, sadece kullanıcı sürüklerken değil, set() ile de tetiklenir.
           Gerçek seek işlemini ButtonRelease-1'de yapacağız. Bu fonksiyon sadece
           sürükleme sırasında zaman etiketini güncelleyebilir."""
        if self._user_is_seeking_mp3: # Sadece kullanıcı aktif olarak sürüklerken
            current_seek_val = float(value_str)
            duration = self.execution_manager.mp3_duration_sec
            self.mp3_time_label.config(text=f"{self._format_time(current_seek_val)} / {self._format_time(duration if duration > 0 else 0)}")

    def _start_mp3_polling(self):
        self._stop_mp3_polling() # Önceki bir polling varsa durdur
        self._mp3_polling_active = True
        self._poll_mp3_status()

    def _stop_mp3_polling(self):
        self._mp3_polling_active = False
        if self._mp3_after_id:
            self.after_cancel(self._mp3_after_id)
            self._mp3_after_id = None

    def _poll_mp3_status(self):
        if not self._mp3_polling_active or not self.execution_manager.is_mp3_playing:
            self.hide_mp3_controls() # Eğer çalma durumu değiştiyse kontrolleri gizle
            return

        # Get current time from player AFTER checking if it's active and playing
        current_time_sec = self.execution_manager.get_mp3_current_time_sec()
        duration_sec = self.execution_manager.mp3_duration_sec
        is_player_paused = self.execution_manager.is_mp3_paused # Check if player is in paused state

        if not self._user_is_seeking_mp3: # Kullanıcı aktif olarak sürüklemiyorsa
            if is_player_paused:
                # If the music is paused by the user:
                # - The seek bar's position (thumb) should remain where the user last placed it (via on_mp3_seek_end or where it was when paused).
                # - The time label should reflect the seek bar's current position.
                # - We do NOT update the seek bar's position from pygame.mixer.music.get_pos() because
                #   get_pos() might be 0 or misleading after a seek operation while paused.
                current_scale_val = float(self.mp3_seek_scale.get()) # Read the current visual position of the scale
                self.mp3_time_label.config(text=f"{self._format_time(current_scale_val)} / {self._format_time(duration_sec if duration_sec > 0 else 0)}")
            else:
                # Music is actively playing (not paused by user).
                # Update the seek bar and time label based on pygame's current playback time.
                self._programmatic_scale_update = True
                self.mp3_seek_scale.set(current_time_sec)
                self._programmatic_scale_update = False
                self.mp3_time_label.config(text=f"{self._format_time(current_time_sec)} / {self._format_time(duration_sec if duration_sec > 0 else 0)}")

        # Check if music has finished playing
        # is_mp3_still_busy() checks pygame.mixer.music.get_busy()
        if not self.execution_manager.is_mp3_still_busy() and not is_player_paused: # is_player_paused burada doğru
            # If music is not busy (likely finished) AND it's not in a user-paused state, then stop everything.
            self.execution_manager.stop_mp3() # This will also call hide_mp3_controls
        else:
            # Continue polling
            self._mp3_after_id = self.after(250, self._poll_mp3_status) # 250ms'de bir kontrol et


    def show_about(self):
        """Hakkında penceresini gösterir."""
        messagebox.showinfo(
            "Hakkında - Python Program Yöneticisi",
            "Bu program Gemini yardımı ile Mayıs 2025 tarihinde\n"
            "Dr. Mustafa Afyonluoğlu tarafından yazılmıştır.",
            parent=self # Mesaj kutusunun ana pencere üzerinde açılmasını sağlar
        )

    def show_dependency_analysis(self, file_path):
        """Python dosyası için dependency analizi yapıp sonuçları gösterir."""
        try:
            # Proje dosyalarını keşfet
            project_files = self.python_analyzer._discover_project_files(file_path)
            
            # Dependency analizi yap
            dependency_results = self.dependency_analyzer.analyze_project_dependencies(project_files)
            
            # Analiz penceresini göster
            self._show_dependency_analysis_results(file_path, dependency_results, project_files)
            
            # History'ye kaydet
            self.db.add_history(f"Dependency Analizi: {file_path}", "method_analysis")            
        except Exception as e:
            messagebox.showerror("Dependency Analizi Hatası", 
                               f"Dependency analizi yapılırken hata oluştu:\n{e}", 
                               parent=self)
    
    def _show_dependency_analysis_results(self, file_path, results, project_files):
        """Dependency analizi sonuçlarını 4 sekmeli bir pencerede gösterir."""
        # Analiz penceresi oluştur
        analysis_window = tk.Toplevel(self)
        analysis_window.title(f"Dependency Analizi - {os.path.basename(file_path)}")
        analysis_window.resizable(True, True)
        
        # Geometri yönetimini kullan
        self.load_or_center_window("dependency_analyzer", analysis_window, 800, 600)
          # Pencere kapatma işleyicisi
        def on_dependency_closing():
            geom = analysis_window.winfo_geometry()
            self.db.save_window_geometry("dependency_analyzer", geom)
            analysis_window.destroy()
        
        analysis_window.protocol("WM_DELETE_WINDOW", on_dependency_closing)
        # ESC tuşu ile pencereyi kapat
        analysis_window.bind("<Escape>", lambda e: on_dependency_closing())
        
        # Ana notebook widget
        notebook = ttk.Notebook(analysis_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 1. Özet Sekmesi
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="📊 Özet")
        self._create_summary_tab(summary_frame, results, project_files)
        
        # 2. Yüklü Paketler Sekmesi
        installed_frame = ttk.Frame(notebook)
        notebook.add(installed_frame, text="✅ Yüklü Paketler")
        self._create_installed_packages_tab(installed_frame, results)
        
        # 3. Eksik Paketler Sekmesi
        missing_frame = ttk.Frame(notebook)
        notebook.add(missing_frame, text="❌ Eksik Paketler")
        self._create_missing_packages_tab(missing_frame, results)
          # 4. Requirements.txt Sekmesi
        requirements_frame = ttk.Frame(notebook)
        notebook.add(requirements_frame, text="📄 Requirements.txt")
        self._create_requirements_tab(requirements_frame, results, os.path.dirname(file_path))
        
        # Modal pencere davranışı
        analysis_window.transient(self)
        analysis_window.grab_set()
        analysis_window.focus_set()
    
    def _create_summary_tab(self, parent, results, project_files):
        """Özet sekmesini oluşturur."""
        # Ana frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Dependency Analizi Özeti", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # İstatistikler frame
        stats_frame = ttk.LabelFrame(main_frame, text="İstatistikler", padding=10)
        stats_frame.pack(fill="x", pady=(0, 15))
        
        # İstatistik bilgileri
        stats_info = [
            ("Analiz Edilen Dosya Sayısı", len(project_files)),
            ("Toplam Import Sayısı", len(results['all_imports'])),
            ("Builtin Modül Sayısı", len(results['builtin_modules'])),
            ("Stdlib Modül Sayısı", len(results['stdlib_modules'])),
            ("Yüklü Paket Sayısı", len(results['installed_packages'])),
            ("Eksik Paket Sayısı", len(results['missing_packages']))
        ]
        
        for i, (label, value) in enumerate(stats_info):
            row_frame = ttk.Frame(stats_frame)
            row_frame.pack(fill="x", pady=2)
            
            ttk.Label(row_frame, text=f"{label}:", width=25, anchor="w").pack(side="left")
            ttk.Label(row_frame, text=str(value), font=("Arial", 10, "bold")).pack(side="left")
        
        # Proje dosyaları frame
        files_frame = ttk.LabelFrame(main_frame, text="Analiz Edilen Dosyalar", padding=10)
        files_frame.pack(fill="both", expand=True)
        
        # Dosya listesi
        files_listbox = tk.Listbox(files_frame, font=("Consolas", 9))
        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=files_listbox.yview)
        files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        files_listbox.pack(side="left", fill="both", expand=True)
        files_scrollbar.pack(side="right", fill="y")
        
        for file_path in project_files:
            files_listbox.insert(tk.END, file_path)
    
    def _create_installed_packages_tab(self, parent, results):
        """Yüklü paketler sekmesini oluşturur."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Yüklü Paketler", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Treeview for installed packages
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("Package", "Type")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        tree.heading("Package", text="Paket Adı")
        tree.heading("Type", text="Tür")
        
        tree.column("Package", width=400)
        tree.column("Type", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Builtin modules
        for module in results['builtin_modules']:
            tree.insert("", tk.END, values=(module, "Builtin"))
        
        # Stdlib modules
        for module in results['stdlib_modules']:
            tree.insert("", tk.END, values=(module, "Stdlib"))
            
        # Installed packages
        for package in results['installed_packages']:
            tree.insert("", tk.END, values=(package, "3rd Party"))
    
    def _create_missing_packages_tab(self, parent, results):
        """Eksik paketler sekmesini oluşturur."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Eksik Paketler", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        if not results['missing_packages']:
            # Eksik paket yoksa
            no_missing_label = ttk.Label(main_frame, 
                                        text="🎉 Tebrikler! Tüm gerekli paketler yüklü.", 
                                        font=("Arial", 12), foreground="darkblue")
            no_missing_label.pack(pady=50)
        else:
            # Eksik paketler listesi
            listbox_frame = ttk.LabelFrame(main_frame, text="Eksik Paketler", padding=10)
            listbox_frame.pack(fill="both", expand=True, pady=(0, 15))
            
            listbox = tk.Listbox(listbox_frame, font=("Consolas", 10))
            listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=listbox_scrollbar.set)
            
            listbox.pack(side="left", fill="both", expand=True)
            listbox_scrollbar.pack(side="right", fill="y")
            
            for package in results['missing_packages']:
                listbox.insert(tk.END, package)
              # Pip install komutu
            if results['pip_install_command']:
                cmd_frame = ttk.LabelFrame(main_frame, text="Kurulum Komutu", padding=10)
                cmd_frame.pack(fill="x")
                
                cmd_text = tk.Text(cmd_frame, height=3, font=("Consolas", 10))
                cmd_text.pack(fill="x")
                cmd_text.insert("1.0", results['pip_install_command'])
                cmd_text.configure(state="disabled")
                
                # Kopyala butonu
                copy_button = ttk.Button(cmd_frame, text="📋 Komutu Kopyala",
                                       command=lambda: self._copy_to_clipboard(results['pip_install_command']))
                copy_button.pack(pady=(10, 0))
    
    def _create_requirements_tab(self, parent, results, project_dir):
        """Requirements.txt sekmesini oluşturur."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Requirements.txt", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Requirements içeriği
        content_frame = ttk.LabelFrame(main_frame, text="Requirements.txt İçeriği", padding=10)
        content_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        text_widget = tk.Text(content_frame, font=("Consolas", 10))
        text_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=text_scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        text_scrollbar.pack(side="right", fill="y")
          # Requirements içeriğini ekle
        requirements_content = "\n".join(results['requirements'])
        text_widget.insert("1.0", requirements_content)
        text_widget.configure(state="disabled")
        
        # Butonlar frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        # Kopyala butonu
        copy_button = ttk.Button(buttons_frame, text="📋 İçeriği Kopyala",
                               command=lambda: self._copy_to_clipboard(requirements_content))
        copy_button.pack(side="left", padx=(0, 10))
        
        # Kaydet butonu
        save_button = ttk.Button(buttons_frame, text="💾 Requirements.txt Kaydet",
                               command=lambda: self._save_requirements_file(project_dir, results['requirements']))
        save_button.pack(side="left")
    
    def _copy_to_clipboard(self, text):
        """Metni panoya kopyalar."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Başarılı", "Metin panoya kopyalandı!", parent=self)
        except Exception as e:
            messagebox.showerror("Hata", f"Panoya kopyalarken hata: {e}", parent=self)
    
    def _save_requirements_file(self, project_dir, requirements):
        """Requirements.txt dosyasını kaydeder."""
        try:
            req_file_path = self.dependency_analyzer.generate_requirements_file(project_dir, requirements)
            messagebox.showinfo("Başarılı", 
                              f"Requirements.txt dosyası kaydedildi:\n{req_file_path}", 
                              parent=self)
            # Dosya listesini yenile
            # self.file_browser.refresh_file_list()
        except Exception as e:
            messagebox.showerror("Hata", 
                               f"Requirements.txt kaydedilirken hata:\n{e}", 
                               parent=self)

    def create_right_click_menu_DEPRECATED(self, tree):
        """Dosya listesi için sağ tık menüsü oluşturur."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="🚀 Çalıştır", command=lambda: self.run_selected_file())
        menu.add_command(label="📝 Düzenle", command=lambda: self.edit_selected_file())
        menu.add_separator()
        menu.add_command(label="🔗 Varsayılan Uygulama ile Aç", command=lambda: self.open_with_default())
        menu.add_command(label="📂 Dosya Konumunu Aç", command=lambda: self.open_file_location())
        menu.add_separator()
        menu.add_command(label="📄 Yeniden Adlandır", command=lambda: self.rename_selected_file())
        menu.add_command(label="🗑️ Sil", command=lambda: self.delete_selected_file())
        menu.add_separator()
        menu.add_command(label="🗜️ Sıkıştır (ZIP)", command=lambda: self.compress_selected_files())
        menu.add_command(label="🎵 MP3 Çal", command=lambda: self.play_mp3_file())
        menu.add_separator()
        # Python metod kontrolü seçeneğini ekle
        menu.add_command(label="🔍 Python Metod Kontrolü", command=lambda: self.analyze_python_methods())
        
        return menu

    def analyze_python_methods_for_path(self, file_path):
        """Belirtilen Python dosyası için metod analizi yapar."""
        try:
            analyzer = MethodAnalyzer(self)
            analyzer.show_analysis_window(file_path)
            
            # History'ye kaydet
            self.db.add_history(f"Metod Analizi: {file_path}", "method_analysis")
            
        except Exception as e:
            print(f"❗ Metod analizi sırasında hata: {e}")
            messagebox.showerror("Hata", f"Metod analizi sırasında hata oluştu:\n{str(e)}")


if __name__ == "__main__":
    print("####################################################################################")
    print("    🔸  Bu dosya doğrudan çalıştırılamaz, Python Program Yöneticisi GUI modülüdür.")
    print("####################################################################################")


