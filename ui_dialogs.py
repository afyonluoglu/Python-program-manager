# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
import json # Sütun genişliklerini kaydetmek/yüklemek için
import tempfile
import zipfile
import subprocess
import platform
from tkinter import messagebox, filedialog

from regex import F
from python_editor import PythonEditor  
from db_manager import DatabaseManager

# --- Arama Sonuçları Penceresi Sınıfı ---
class SearchResultsWindow(tk.Toplevel):
    def __init__(self, parent, found_files_details, pattern, root_folder_searched):
        super().__init__(parent)
        self.parent = parent
        self.found_files_details = found_files_details
        self.pattern = pattern
        self.root_folder_searched = root_folder_searched
        
        # Pencere ayarlarını yapılandır
        self.title(f"Arama Sonuçları - '{pattern}'")
        self.transient(parent)
        self.grab_set()

        self.parent.load_or_center_window("search_results", self, 800, 500)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.bind("<Escape>", lambda e: self._on_closing())

        # Ana frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bilgi etiketi
        info_text = f"'{pattern}' deseni için '{os.path.basename(root_folder_searched)}' klasöründe {len(found_files_details)} dosya bulundu."
        ttk.Label(main_frame, text=info_text).pack(anchor=tk.W, pady=(0, 10))

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview oluştur
        columns = ("Dosya Adı", "Yol", "Boyut (KB)", "Değiştirilme Tarihi")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        # Sütun başlıklarını ayarla
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Dosya Adı":
                self.tree.column(col, width=200)
            elif col == "Yol":
                self.tree.column(col, width=350)
            elif col == "Boyut (KB)":
                self.tree.column(col, width=100)
            elif col == "Değiştirilme Tarihi":
                self.tree.column(col, width=150)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree ve scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Verileri ekle
        for file_info in self.found_files_details:
            file_path = file_info['path']
            file_name = os.path.basename(file_path)
            file_size = file_info['size_kb']
            modified_date = file_info['modified']
            
            self.tree.insert("", tk.END, values=(file_name, file_path, file_size, modified_date))
        
        # Buton frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Butonlar
        ttk.Button(button_frame, text="Dosyayı Aç", command=self.open_selected_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Klasörü Aç", command=self.open_containing_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Kapat", command=self.destroy).pack(side=tk.RIGHT)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_selected_file())
    
    def show_context_menu(self, event):
        """Sağ tık menüsünü göster"""
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Dosyayı Pyton Editörde Aç", command=self.open_file_in_editor)
        # context_menu.add_command(label="Bu dosyayı Aç", command=self.open_selected_file)
        context_menu.add_command(label="Klasörü Aç", command=self.open_containing_folder)
        context_menu.tk_popup(event.x_root, event.y_root)
     
    def open_file_location(self):
        """Seçilen dosyanın bulunduğu klasörü aç"""
        try:
            selection = self.tree.selection()
            if not selection:
                return

            selected_item = self.tree.item(selection[0])["values"][1]  # Yol sütunu
            print(f"⚡ Seçilen Dosya: {selected_item}")
            self.parent.file_browser.go_to_file(selected_item)

        except Exception as e:
            print(f"❗  HATA: Klasör açılırken hata oluştu: {e}")

    def open_file_in_editor(self):
        print("⚡ Seçilen dosya Pyton editörde açılıyor...")
        selection = self.tree.selection()
        selected_item = self.tree.item(selection[0])["values"][1]  # Yol sütunu

        self.grab_release()

        # Python editörde dosyayı aç
        editor = PythonEditor(self.parent, selected_item, read_only=False)

        # Editör penceresini en üste getir
        editor.window.deiconify()
        editor.window.attributes('-topmost', True)
        editor.window.focus_force()
        editor.window.after(100, lambda: editor.window.attributes('-topmost', False))

    def open_selected_file(self):
        """Seçili dosyayı varsayılan uygulamayla aç"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seçim Yok", "Lütfen açılacak bir dosya seçin.", parent=self)
            return
        
        file_path = self.tree.item(selected[0])["values"][1]  # Yol sütunu
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{e}", parent=self)
    
    def open_containing_folder(self):
        """Seçili dosyanın bulunduğu klasörü aç"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seçim Yok", "Lütfen bir dosya seçin.", parent=self)
            return
        
        file_path = self.tree.item(selected[0])["values"][1]  # Yol sütunu
        folder_path = os.path.dirname(file_path)
        try:
            os.startfile(folder_path)
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı:\n{e}", parent=self.window)

    def _on_closing(self):
        """Pencere kapatılırken geometriyi kaydet"""
        geom = self.winfo_geometry()
        self.parent.db.save_window_geometry("search_results", geom)
        self.destroy()

# --- Kelime Arama Sonuçları Penceresi Sınıfı ---
class WordSearchResultsWindow(tk.Toplevel):
    def __init__(self, app_instance, found_items, search_word, root_folder_searched):
        super().__init__(app_instance)
        self.app = app_instance
        self.title(f"Kelime Arama Sonuçları: '{search_word}' ({len(found_items)} eşleşme)")

        self.app.load_or_center_window("word_search_results", self, 900, 600)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.bind("<Escape>", lambda e: self._on_closing())

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Sütunlar: Dosya Yolu, Satır No, Satır İçeriği
        self.results_tree = ttk.Treeview(main_frame, columns=("line_no", "line_content"))
        self.results_tree.heading("#0", text="Dosya Yolu", anchor='w')
        self.results_tree.heading("line_no", text="Satır No", anchor='w')
        self.results_tree.heading("line_content", text="Satır İçeriği", anchor='w')

        self.results_tree.column("#0", width=300, stretch=tk.YES, anchor='w')
        self.results_tree.column("line_no", width=80, stretch=tk.NO, anchor='center')
        self.results_tree.column("line_content", width=500, stretch=tk.YES, anchor='w')

        self.results_tree.bind('<Double-Button-1>', self._on_double_click)

        # Kaydedilmiş sütun genişliklerini yükle
        saved_widths_json = self.app.db.get_setting("word_search_results_column_widths")
        if saved_widths_json:
            try:
                saved_widths = json.loads(saved_widths_json)
                if isinstance(saved_widths, dict):
                    for col_id, width_val in saved_widths.items():
                        if col_id in ("#0", "line_no", "line_content"):
                            try:
                                self.results_tree.column(col_id, width=int(width_val))
                            except (ValueError, tk.TclError) as e_col:
                                print(f"HATA: Kelime arama '{col_id}' sütun genişliği ({width_val}) uygulanamadı: {e_col}")
            except json.JSONDecodeError as e:
                print(f"HATA: Kayıtlı kelime arama sütun genişlikleri okunamadı (JSON): {e}")

        self.results_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.grid(row=0, column=1, sticky='ns')

        scrollbar_x = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.grid(row=1, column=0, sticky='ew')

        for file_path, line_num, line_content in found_items:
            icon_to_use = self.app.file_icon if self.app.file_icon else None
            self.results_tree.insert("", tk.END, text=file_path, image=icon_to_use,
                                     values=(line_num, line_content))

        close_button = ttk.Button(main_frame, text="Kapat", command=self._on_closing)
        close_button.grid(row=2, column=0, columnspan=2, pady=(10,0))

        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def _on_double_click(self, event):
        """Liste öğesine çift tıklandığında dosyayı editörde aç."""

        # print("⚡ Kelime arama sonuçlarına çift tıklandı.")
        selected_item_id = event.widget.focus()
        if selected_item_id:
            item_data = event.widget.item(selected_item_id)
            selected_item = item_data['values']
            dosya = item_data['text']
            satir = selected_item[0]
            print(f"   📂 Dosya: {dosya}")
            print(f"   ⚡ Satır: {satir}")
            line_number = int(satir)

            self.grab_release()

            # Python editörde dosyayı aç
            editor = PythonEditor(self.app, dosya, read_only=False)

            try:
                editor.open_file_at_line(dosya, line_number)                
            except ValueError:
                print(f"    HATA: Satır numarası parse edilemedi: {satir}")

            # Editör penceresini en üste getir
            editor.window.deiconify()  # Pencereyi göster
            editor.window.attributes('-topmost', True)  # En üste getir
            editor.window.focus_force()  # Focus ver
            editor.window.after(100, lambda: editor.window.attributes('-topmost', False))  # Kısa süre sonra topmost'u kaldır


    def _on_closing(self):
        geom = self.winfo_geometry()
        self.app.db.save_window_geometry("word_search_results", geom)
        # Sütun genişliklerini kaydet
        try:
            col_widths = {
                "#0": self.results_tree.column("#0", "width"),
                "line_no": self.results_tree.column("line_no", "width"),
                "line_content": self.results_tree.column("line_content", "width")
            }
            self.app.db.set_setting("word_search_results_column_widths", json.dumps(col_widths))
        except Exception as e:
            print(f"HATA: Kelime arama listesi sütun genişlikleri kaydedilemedi: {e}")
        self.destroy()

# --- ZIP Dosyası İçeriği Penceresi Sınıfı ---
class ZipContentsWindow(tk.Toplevel):
    def __init__(self, app_instance, zip_items_info, zip_filename, zip_file_path=None):
        super().__init__(app_instance)
        self.app = app_instance
        self.zip_file_path = zip_file_path
        print(f"ZIP dosyası yolu: {self.zip_file_path}")
        self.title(f"ZIP İçeriği: {zip_filename} ({len(zip_items_info)} öğe)")

        self.app.load_or_center_window("zip_contents", self, 700, 500)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.bind("<Escape>", lambda e: self._on_closing())

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Sütunlar: Ad, Tür, Boyut (byte), Değiştirme Tarihi
        self.contents_tree = ttk.Treeview(main_frame, columns=("type", "size", "modified"))
        self.contents_tree.heading("#0", text="Ad", anchor='w')
        self.contents_tree.heading("type", text="Tür", anchor='w')
        self.contents_tree.heading("size", text="Boyut (byte)", anchor='e') # Sayılar için sağa hizalı
        self.contents_tree.heading("modified", text="Değiştirilme Tarihi", anchor='w')

        self.contents_tree.column("#0", width=300, stretch=tk.YES, anchor='w')
        self.contents_tree.column("type", width=80, stretch=tk.NO, anchor='w')
        self.contents_tree.column("size", width=100, stretch=tk.NO, anchor='e')
        self.contents_tree.column("modified", width=150, stretch=tk.NO, anchor='w')

        # Kaydedilmiş sütun genişliklerini yükle
        saved_widths_json = self.app.db.get_setting("zip_contents_column_widths")
        if saved_widths_json:
            try:
                saved_widths = json.loads(saved_widths_json)
                if isinstance(saved_widths, dict):
                    for col_id, width_val in saved_widths.items():
                        if col_id in ("#0", "type", "size", "modified"):
                            try:
                                self.contents_tree.column(col_id, width=int(width_val))
                            except (ValueError, tk.TclError) as e_col:
                                print(f"HATA: ZIP içerik '{col_id}' sütun genişliği ({width_val}) uygulanamadı: {e_col}")
            except json.JSONDecodeError as e:
                print(f"HATA: Kayıtlı ZIP içerik sütun genişlikleri okunamadı (JSON): {e}")

        self.contents_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.contents_tree.yview)
        self.contents_tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.grid(row=0, column=1, sticky='ns')

        scrollbar_x = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.contents_tree.xview)
        self.contents_tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.grid(row=1, column=0, sticky='ew')

        for item_info in zip_items_info:
            item_name = item_info.filename
            item_type = "Klasör" if item_info.is_dir() else "Dosya"
            item_size = item_info.file_size
            dt_tuple = item_info.date_time
            item_modified_str = f"{dt_tuple[0]:04d}-{dt_tuple[1]:02d}-{dt_tuple[2]:02d} {dt_tuple[3]:02d}:{dt_tuple[4]:02d}:{dt_tuple[5]:02d}"
            
            icon_to_use = None
            if item_info.is_dir():
                if self.app.folder_icon:
                    icon_to_use = self.app.folder_icon
            else: # Dosya ise
                filename_lower = item_name.lower()
                if filename_lower.endswith(".py") and self.app.file_icon: # .py için file_icon (python_file.png)
                    icon_to_use = self.app.file_icon
                elif filename_lower.endswith(".zip") and self.app.zip_icon:
                    icon_to_use = self.app.zip_icon
                elif filename_lower.endswith(".exe") and self.app.exe_icon:
                    icon_to_use = self.app.exe_icon
                elif filename_lower.endswith(".db") and self.app.db_icon: # DB ikonu
                    icon_to_use = self.app.db_icon
                elif self.app.unknown_icon: # Diğer tüm dosya türleri için unknown_icon
                    icon_to_use = self.app.unknown_icon

            # ZIP içindeki dosya yolunu tags olarak kaydet
            self.contents_tree.insert("", tk.END, text=item_name, image=icon_to_use, 
                                    values=(item_type, item_size, item_modified_str),
                                    tags=(item_info.filename,))
            
        close_button = ttk.Button(main_frame, text="Kapat", command=self._on_closing)
        close_button.grid(row=2, column=0, columnspan=2, pady=(10,0))

        self.bind_events()
        
        self.grab_set()
        self.focus_set()
        self.wait_window(self)


    def bind_events(self):
        # Çift tıklama ile dosya çalıştırma
        self.contents_tree.bind("<Double-1>", self.on_double_click)
        
        # Sağ tık menüsü
        self.contents_tree.bind("<Button-3>", self.show_context_menu)

    def _on_closing(self):
        geom = self.winfo_geometry()
        self.app.db.save_window_geometry("zip_contents", geom)
        try:
            col_widths = { "#0": self.contents_tree.column("#0", "width"), "type": self.contents_tree.column("type", "width"), "size": self.contents_tree.column("size", "width"), "modified": self.contents_tree.column("modified", "width")}
            self.app.db.set_setting("zip_contents_column_widths", json.dumps(col_widths))
        except Exception as e:
            print(f"HATA: ZIP içerik listesi sütun genişlikleri kaydedilemedi: {e}")
        self.destroy()

    def on_double_click(self, event):
        """ZIP içindeki dosyayı geçici olarak çıkartıp çalıştırır."""
        selected_item = self.contents_tree.focus()
        if not selected_item or not self.zip_file_path:
            return
            
        try:
            # Seçili dosyanın ZIP içindeki yolunu al
            tags = self.contents_tree.item(selected_item, "tags")
            if not tags:
                return
            zip_internal_path = tags[0]
            
            temp_dir = tempfile.mkdtemp()  # Geçici klasör oluştur
            # Dosyayı ZIP'den çıkart
            with zipfile.ZipFile(self.zip_file_path, 'r') as zf:
                zf.extract(zip_internal_path, temp_dir)
            
            extracted_file_path = os.path.join(temp_dir, zip_internal_path)
            
            # Python dosyası ise çalıştır
            if zip_internal_path.lower().endswith('.py'):
                self.run_python_file(extracted_file_path)
            else:
                # Diğer dosya türleri için sistem varsayılan uygulamasıyla aç
                self.open_with_default_app(extracted_file_path)
                
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya çalıştırılırken hata oluştu:\n{e}", parent=self.window)

    def run_python_file(self, file_path):
        """Python dosyasını çalıştırır."""
        try:
            # Python dosyasını yeni bir terminal penceresinde çalıştır
            system = platform.system()
            if system == "Windows":
                # Windows'ta dosya yolundaki ters slashları düzelt ve tırnak kullanımını düzelt
                normalized_path = os.path.normpath(file_path)
                subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', 'python', normalized_path])
            elif system == "Darwin":  # macOS
                subprocess.Popen(['osascript', '-e', f'tell app "Terminal" to do script "python \\"{file_path}\\""'])
            elif system == "Linux":
                subprocess.Popen(['gnome-terminal', '--', 'python3', file_path])
            else:
                messagebox.showinfo("Bilgi", f"'{system}' sistemi için çalıştırma özelliği henüz desteklenmiyor.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Çalıştırma Hatası", f"Python dosyası çalıştırılamadı:\n{e}", parent=self.window)

    def open_with_default_app(self, file_path):
        """Dosyayı sistem varsayılan uygulamasıyla açar."""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', file_path])
            elif system == "Linux":
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Açma Hatası", f"Dosya açılamadı:\n{e}", parent=self.window)

    def show_context_menu(self, event):
        """Sağ tık menüsünü gösterir."""
        selected_item = self.contents_tree.focus()
        if not selected_item:
            return
            
        # Seçili dosyanın ZIP içindeki yolunu al
        tags = self.contents_tree.item(selected_item, "tags")
        if not tags:
            return
        
        zip_internal_path = tags[0]
        is_python_file = zip_internal_path.lower().endswith('.py')
            
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Çalıştır", command=lambda: self.on_double_click(None))
        context_menu.add_separator()
        context_menu.add_command(label="Çıkart...", command=self.extract_file)
        
        # Sadece Python dosyaları için "İzle" seçeneğini ekle
        if is_python_file:
            context_menu.add_command(label="Python Dosyasını Aç", command=self.showPythonFileInEditor)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def showPythonFileInEditor(self):
        """Seçili Python dosyasını Python Editor'de readonly olarak gösterir."""
        selected_item = self.contents_tree.focus()
        if not selected_item:
            return

        # Seçili dosyanın ZIP içindeki yolunu al
        tags = self.contents_tree.item(selected_item, "tags")
        if not tags:
            return

        zip_internal_path = tags[0]
        print(f"⚡ ZIP içindeki dosya: {zip_internal_path}")

        # Sadece Python dosyalarını işle
        if not zip_internal_path.lower().endswith('.py'):
            messagebox.showinfo("Bilgi", "Bu özellik sadece Python dosyaları için kullanılabilir.", parent=self)
            return

        try:
            # Geçici klasör oluştur
            temp_dir = tempfile.mkdtemp()  # Geçici klasör oluştur
                
            # Dosyayı ZIP'den çıkart
            with zipfile.ZipFile(self.zip_file_path, 'r') as zf:
                zf.extract(zip_internal_path, temp_dir)
                
            extracted_file_path = os.path.join(temp_dir, zip_internal_path)
            print(f"⚡ İzlemek üzere çıkartılan Python dosyası: {extracted_file_path}")
                

            # Modal grab'ı geçici olarak kaldır
            self.grab_release()
            
            # Editörü readonly modunda oluştur
            editor = PythonEditor(self.app, extracted_file_path, read_only=True)
            
            # Editör penceresini en üste getir
            editor.window.deiconify()  # Pencereyi göster
            editor.window.attributes('-topmost', True)  # En üste getir
            editor.window.focus_force()  # Focus ver
            editor.window.after(100, lambda: editor.window.attributes('-topmost', False))  # Kısa süre sonra topmost'u kaldır
            
            # Modal grab'ı geri al
            # self.after(200, self.grab_set)

            # History'e kaydet
            self.app.db.add_history(f"Python Editörü (Readonly) - ZIP: {extracted_file_path}", "python_editor")
        except Exception as e:
            # Hata durumunda grab'ı geri al
            self.grab_set()
            messagebox.showerror("Hata", f"Python editörü açılırken hata oluştu:\n{e}", parent=self)

    def extract_file(self):
        """Seçili dosyayı ZIP'den kullanıcının seçtiği konuma çıkartır."""
        selected_item = self.contents_tree.focus()
        print(f"⚡ ZIP içeriği çıkartma işlemi başlatıldı. Seçili öğe: {selected_item}")
        print(f"⚡ ZIP dosyası yolu: {self.zip_file_path}")
        if not selected_item or not self.zip_file_path:
            return
            
        try:
            # Seçili dosyanın ZIP içindeki yolunu al
            tags = self.contents_tree.item(selected_item, "tags")
            print(f"⚡ ZIP içindeki etiketler: {tags}")
            if not tags:
                return
            zip_internal_path = tags[0]
            
            # Dosya adını al
            filename = os.path.basename(zip_internal_path)
            print(f"♦️ Çıkartılacak dosya: {filename} (ZIP içindeki yol: {zip_internal_path})")
            
            try:
                # Kullanıcıdan çıkartma konumunu sor
                save_path = filedialog.asksaveasfilename(
                    title=f"'{filename}' dosyasını nereye çıkartmak istiyorsunuz?",
                    initialfile=filename,
                    parent=self.app
                )
            except Exception as e:
                print(f"HATA: Çıkartma konumu seçilirken hata oluştu: {e}")
                messagebox.showerror("Hata", f"Çıkartma konumu seçilirken hata oluştu:\n{e}", parent=self.window)
                return              
            print(f"♦️ Çıkartma konumu: {save_path}")
            if not save_path:
                return
                
            # Dosyayı ZIP'den çıkart
            with zipfile.ZipFile(self.zip_file_path, 'r') as zf:
                # Dosyayı oku ve hedef konuma yaz
                with zf.open(zip_internal_path) as source, open(save_path, 'wb') as target:
                    target.write(source.read())
            
            messagebox.showinfo("Başarılı", f"'{filename}' dosyası başarıyla çıkartıldı:\n{save_path}", parent=self.app)
            history_message = f"'{filename}' dosyası ZIP içeriğinden çıkartıldı: {save_path}"
            self.app.db.add_history(f"ZIP Dosya çıkartıldı: {history_message}", event_type="zip_extraction")

        except Exception as e:
            print(f"HATA: ZIP içeriği çıkartılırken hata oluştu: {e}")
            messagebox.showerror("Çıkartma Hatası", f"Dosya çıkartılırken hata oluştu:\n{e}", parent=self.app)

if __name__ == "__main__":
    print("######################################################################")
    print("    🔸  Bu dosya doğrudan çalıştırılamaz, UIDialog modülüdür.")
    print("######################################################################")

