# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import os
import threading # For starting search threads

# Yerel modüllerden importlar (App'den çağrılacakları için App'in importlarına benzer)
from ui_dialogs import SearchResultsWindow, WordSearchResultsWindow
import operations # operations.py'deki fonksiyonları kullanmak için

class SearchManager:
    def __init__(self, app_instance):
        self.app = app_instance

    def prompt_search_OLD(self):
        """Kullanıcıdan arama kriterlerini alır ve dosya aramasını başlatır."""
        selected_item_id = self.app.dir_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Klasör Seçilmedi",
                                   "Lütfen önce sol taraftaki listeden dosya aranacak bir klasör seçin.",
                                   parent=self.app)
            return

        try:
            search_root_folder = self.app.dir_tree.item(selected_item_id, "values")[0]
            if not os.path.isdir(search_root_folder):
                messagebox.showwarning("Geçersiz Klasör",
                                       "Seçilen öğe geçerli bir klasör değil. Lütfen bir klasör seçin.",
                                       parent=self.app)
                return
        except IndexError:
            messagebox.showwarning("Klasör Seçilemedi",
                                   "Seçili klasörün yolu alınamadı. Lütfen listeden bir klasör seçin.",
                                   parent=self.app)
            return
        except Exception as e:
            messagebox.showerror("Hata", f"Seçili klasör bilgisi alınırken bir hata oluştu:\n{e}", parent=self.app)
            return

        if self.app.long_operation_in_progress:
            messagebox.showwarning("İşlem Devam Ediyor", "Başka bir uzun süreli işlem zaten devam ediyor.", parent=self.app)
            return

        search_pattern = simpledialog.askstring("Dosya Ara",
                                                f"'{os.path.basename(search_root_folder)}' klasöründe ve alt klasörlerinde aranacak dosya adı/deseni:\n(Örn: *.txt, rapor*, *config*)",
                                                parent=self.app)
        if search_pattern:
            self.app.status_label.config(text=f"'{search_pattern}' deseni '{os.path.basename(search_root_folder)}' içinde aranıyor...")
            self.app.activity_progressbar.pack(side=tk.RIGHT, padx=5, pady=2)
            self.app.activity_progressbar.start(10)
            self.app.update_idletasks()
            self.app.long_operation_in_progress = True

            thread = threading.Thread(target=operations.perform_search_in_thread,
                                       args=(self.app, search_pattern, search_root_folder))
            thread.daemon = True
            history_message = f"Arandı: '{search_pattern}' ({os.path.basename(search_root_folder)})"
            self.app.db.add_history(f"Dosya arandı: {history_message}", event_type="search_initiated")
            thread.start()

    def prompt_search(self):
        """Kullanıcıdan arama kriterlerini alır ve dosya aramasını başlatır."""
        selected_item_id = self.app.dir_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Klasör Seçilmedi",
                                "Lütfen önce sol taraftaki listeden dosya aranacak bir klasör seçin.",
                                parent=self.app)
            return

        try:
            search_root_folder = self.app.dir_tree.item(selected_item_id, "values")[0]
            if not os.path.isdir(search_root_folder):
                messagebox.showwarning("Geçersiz Klasör",
                                    "Seçilen öğe geçerli bir klasör değil. Lütfen bir klasör seçin.",
                                    parent=self.app)
                return
        except IndexError:
            messagebox.showwarning("Klasör Seçilemedi",
                                "Seçili klasörün yolu alınamadı. Lütfen listeden bir klasör seçin.",
                                parent=self.app)
            return
        except Exception as e:
            messagebox.showerror("Hata", f"Seçili klasör bilgisi alınırken bir hata oluştu:\n{e}", parent=self.app)
            return

        if self.app.long_operation_in_progress:
            messagebox.showwarning("İşlem Devam Ediyor", "Başka bir uzun süreli işlem zaten devam ediyor.", parent=self.app)
            return

        # Özel dialog penceresi oluştur
        dialog = tk.Toplevel(self.app)
        dialog.title("Dosya Ara")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.app)
        
        # Pencereyi merkeze yerleştir
        dialog.geometry("450x270")
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (270 // 2)
        dialog.geometry(f"450x270+{x}+{y}")
        
        # Değişkenler
        search_pattern_var = tk.StringVar()
        file_size_var = tk.StringVar()
        size_operator_var = tk.StringVar(value="eşit")
        
        # Ana frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Klasör bilgisi
        ttk.Label(main_frame, text=f"Klasör: {os.path.basename(search_root_folder)}").pack(anchor=tk.W, pady=(0, 10))
        
        # Dosya deseni girişi
        ttk.Label(main_frame, text="Dosya adı/deseni:").pack(anchor=tk.W)
        pattern_entry = ttk.Entry(main_frame, textvariable=search_pattern_var, width=50)
        pattern_entry.pack(fill=tk.X, pady=(2, 5))
        pattern_entry.focus()
        
        # Örnek bilgi
        ttk.Label(main_frame, text="Örnek: *.txt, rapor*, *config*", 
                font=("Arial", 8), foreground="gray").pack(anchor=tk.W, pady=(0, 10))
        
        # Dosya boyutu frame
        size_frame = ttk.Frame(main_frame)
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(size_frame, text="Dosya boyutu (KB):").pack(side=tk.LEFT)
        
        size_entry = ttk.Entry(size_frame, textvariable=file_size_var, width=15)
        size_entry.pack(side=tk.LEFT, padx=(10, 10))
        
        size_combo = ttk.Combobox(size_frame, textvariable=size_operator_var, 
                                values=["büyük", "eşit", "küçük"], 
                                state="readonly", width=10)
        size_combo.pack(side=tk.LEFT)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        result = {"search_pattern": None, "file_size": None, "size_operator": None}
        
        def on_ok():
            if not search_pattern_var.get().strip():
                messagebox.showwarning("Uyarı", "Lütfen aranacak dosya deseni girin.", parent=dialog)
                return
            
            # Dosya boyutu kontrolü
            if file_size_var.get().strip():
                try:
                    size_value = float(file_size_var.get().strip())
                    if size_value < 0:
                        messagebox.showwarning("Uyarı", "Dosya boyutu negatif olamaz.", parent=dialog)
                        return
                    result["file_size"] = size_value
                    result["size_operator"] = size_operator_var.get()
                except ValueError:
                    messagebox.showwarning("Uyarı", "Geçerli bir dosya boyutu girin (sayı).", parent=dialog)
                    return
            
            result["search_pattern"] = search_pattern_var.get().strip()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Ara", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="İptal", command=on_cancel).pack(side=tk.RIGHT)
        
        # Enter tuşu ile arama başlat
        def on_enter(event):
            on_ok()
        
        dialog.bind('<Return>', on_enter)
        dialog.wait_window()
        
        # Sonuç kontrolü
        if result["search_pattern"]:
            self.app.status_label.config(text=f"'{result['search_pattern']}' deseni '{os.path.basename(search_root_folder)}' içinde aranıyor...")
            self.app.activity_progressbar.pack(side=tk.RIGHT, padx=5, pady=2)
            self.app.activity_progressbar.start(10)
            self.app.update_idletasks()
            self.app.long_operation_in_progress = True

            thread = threading.Thread(target=operations.perform_search_in_thread,
                                    args=(self.app, result["search_pattern"], search_root_folder, 
                                            result["file_size"], result["size_operator"]))
            thread.daemon = True
            
            size_info = ""
            if result["file_size"] is not None:
                size_info = f" (boyut {result['size_operator']} {result['file_size']} KB)"
            
            history_message = f"'{result['search_pattern']}' ({os.path.basename(search_root_folder)}){size_info}"
            print(f"✨ Search Completed: {search_root_folder=}  {size_info=}")
            self.app.db.add_history(f"Dosya arandı: {history_message}", event_type="search_initiated")
            thread.start()

    def _finalize_search_ui(self):
        """Arama işlemi bittikten sonra (başarılı veya başarısız) UI'ı sıfırlar."""
        self.app.activity_progressbar.stop()
        self.app.activity_progressbar.pack_forget()
        self.app.status_label.config(text="Hazır.")
        self.app.update_idletasks()
        self.app.long_operation_in_progress = False

    def _handle_search_error(self, error):
        """Arama sırasında bir hata oluşursa kullanıcıyı bilgilendirir."""
        self._finalize_search_ui()
        messagebox.showerror("Arama Hatası", f"Dosya arama sırasında bir hata oluştu:\n{error}", parent=self.app)
        print(f"Arama hatası: {error}")  # Hata mesajını konsola yazdırır

    def _show_search_results(self, found_files_details, pattern, root_folder_searched):
        """Arama sonuçlarını yeni bir pencerede gösterir."""
        self._finalize_search_ui()
        if not found_files_details:
            messagebox.showinfo("Arama Sonucu",
                                f"'{pattern}' deseni için '{os.path.basename(root_folder_searched)}' klasöründe ve alt klasörlerinde dosya bulunamadı.",
                                parent=self.app)
            return
        SearchResultsWindow(self.app, found_files_details, pattern, root_folder_searched)

    def prompt_word_search(self):
        """Kullanıcıdan aranacak kelimeyi ve dosya boyutu kriterlerini alır ve .py dosyalarında aramayı başlatır."""
        selected_item_id = self.app.dir_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Klasör Seçilmedi", "Lütfen önce sol taraftaki listeden kelime aranacak bir klasör seçin.", parent=self.app)
            return
        
        try:
            search_root_folder = self.app.dir_tree.item(selected_item_id, "values")[0]
            if not os.path.isdir(search_root_folder):
                messagebox.showwarning("Geçersiz Klasör", "Seçilen öğe geçerli bir klasör değil. Lütfen bir klasör seçin.", parent=self.app)
                return
        except IndexError:
            messagebox.showwarning("Klasör Seçilemedi", "Seçili klasörün yolu alınamadı. Lütfen listeden bir klasör seçin.", parent=self.app)
            return
        except Exception as e:
            messagebox.showerror("Hata", f"Seçili klasör bilgisi alınırken bir hata oluştu:\n{e}", parent=self.app)
            return

        if self.app.long_operation_in_progress:
            messagebox.showwarning("İşlem Devam Ediyor", "Başka bir uzun süreli işlem zaten devam ediyor.", parent=self.app)
            return

        # Özel dialog penceresi oluştur
        dialog = tk.Toplevel(self.app)
        dialog.title("Kelime Ara")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.app)
        
        # Pencereyi merkeze yerleştir
        dialog.geometry("450x270")
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"450x270+{x}+{y}")
        
        # Değişkenler
        search_word_var = tk.StringVar()
        file_size_var = tk.StringVar()
        size_operator_var = tk.StringVar(value="eşit")
        
        # Ana frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Klasör bilgisi
        ttk.Label(main_frame, text=f"Klasör: {os.path.basename(search_root_folder)}").pack(anchor=tk.W, pady=(0, 10))
        
        # Kelime girişi
        ttk.Label(main_frame, text="Aranacak kelime:").pack(anchor=tk.W)
        word_entry = ttk.Entry(main_frame, textvariable=search_word_var, width=50)
        word_entry.pack(fill=tk.X, pady=(2, 10))
        word_entry.focus()
        
        # Dosya boyutu frame
        size_frame = ttk.Frame(main_frame)
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(size_frame, text="Dosya boyutu (KB):").pack(side=tk.LEFT)
        
        size_entry = ttk.Entry(size_frame, textvariable=file_size_var, width=15)
        size_entry.pack(side=tk.LEFT, padx=(10, 10))
        
        size_combo = ttk.Combobox(size_frame, textvariable=size_operator_var, 
                                values=["büyük", "eşit", "küçük"], 
                                state="readonly", width=10)
        size_combo.pack(side=tk.LEFT)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        result = {"search_word": None, "file_size": None, "size_operator": None}
        
        def on_ok():
            if not search_word_var.get().strip():
                messagebox.showwarning("Uyarı", "Lütfen aranacak kelimeyi girin.", parent=dialog)
                return
            
            # Dosya boyutu kontrolü
            if file_size_var.get().strip():
                try:
                    size_value = float(file_size_var.get().strip())
                    if size_value < 0:
                        messagebox.showwarning("Uyarı", "Dosya boyutu negatif olamaz.", parent=dialog)
                        return
                    result["file_size"] = size_value
                    result["size_operator"] = size_operator_var.get()
                except ValueError:
                    messagebox.showwarning("Uyarı", "Geçerli bir dosya boyutu girin (sayı).", parent=dialog)
                    return
            
            result["search_word"] = search_word_var.get().strip()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Ara", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="İptal", command=on_cancel).pack(side=tk.RIGHT)
        
        # Enter tuşu ile arama başlat
        def on_enter(event):
            on_ok()
        
        dialog.bind('<Return>', on_enter)
        dialog.wait_window()
        
        # Sonuç kontrolü
        if result["search_word"]:
            self.app.status_label.config(text=f"'{result['search_word']}' kelimesi '{os.path.basename(search_root_folder)}' içinde aranıyor...")
            self.app.activity_progressbar.pack(side=tk.RIGHT, padx=5, pady=2)
            self.app.activity_progressbar.start(10)
            self.app.update_idletasks()
            self.app.long_operation_in_progress = True
            
            thread = threading.Thread(target=operations.perform_word_search_in_thread,
                                    args=(self.app, result["search_word"], search_root_folder, 
                                            result["file_size"], result["size_operator"]))
            thread.daemon = True
            
            size_info = ""
            if result["file_size"] is not None:
                size_info = f" (boyut {result['size_operator']} {result['file_size']} KB)"
            
            history_message = f"'{result['search_word']}' ({os.path.basename(search_root_folder)}){size_info}"
            self.app.db.add_history(f"Kelime arandı: {history_message}", event_type="word_search_initiated")
            thread.start()


    def _finalize_word_search_ui(self):
        """Kelime arama işlemi bittikten sonra UI'ı sıfırlar."""
        self._finalize_search_ui() # Reuses the same finalization logic

    def _handle_word_search_error(self, error):
        """Kelime arama sırasında bir hata oluşursa kullanıcıyı bilgilendirir."""
        self._finalize_word_search_ui()
        messagebox.showerror("Kelime Arama Hatası", f"Kelime arama sırasında bir hata oluştu:\n{error}", parent=self.app)

    def _show_word_search_results(self, found_items, search_word, root_folder_searched):
        """Kelime arama sonuçlarını yeni bir pencerede gösterir."""
        self._finalize_word_search_ui()
        WordSearchResultsWindow(self.app, found_items, search_word, root_folder_searched)