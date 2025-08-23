# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog # simpledialog for prompt_compression_options (though not directly used there)
import os
import shutil
import threading
from datetime import datetime

import operations # For calling threaded operations
from utils import BACKUP_FOLDER_BASENAME # Yedekleme klasörü adı için

class ActionManager:
    def __init__(self, app_instance):
        self.app = app_instance

    # --- Compression Methods ---
    def prompt_compression_options(self, folder_path):
        """Kullanıcıya sıkıştırma seçeneklerini soran bir dialog açar."""
        dialog = tk.Toplevel(self.app)
        dialog.title("Sıkıştırma Seçenekleri")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.resizable(False, False)

        self.app.center_window(dialog, 350, 250)

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        include_subfolders_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Alt klasörleri dahil et", variable=include_subfolders_var).pack(pady=5, anchor='w')

        ttk.Label(main_frame, text="Dosya Deseni (örn: *.*, *.txt, resim_*.jpg):").pack(anchor='w', pady=(5,0))
        file_pattern_var = tk.StringVar(value="*.*")
        ttk.Entry(main_frame, textvariable=file_pattern_var, width=40).pack(fill='x', expand=True, pady=(0,5))

        ttk.Label(main_frame, text="ZIP Dosya Adı:").pack(anchor='w', pady=(5,0))
        # yedekleme dosyası ismi için varsayılan ad
        default_zip_name = f"{os.path.basename(folder_path)}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        zip_name_var = tk.StringVar(value=default_zip_name)
        ttk.Entry(main_frame, textvariable=zip_name_var, width=40).pack(fill='x', expand=True, pady=(0,10))

        dialog.update_idletasks()
        desired_min_height = 280
        calculated_content_height = dialog.winfo_reqheight() + 20
        final_dialog_height = max(desired_min_height, calculated_content_height)
        self.app.center_window(dialog, dialog.winfo_reqwidth() + 40, final_dialog_height)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10,0), fill='x')

        def on_ok():
            dialog.destroy()
            self._execute_compression(folder_path, include_subfolders_var.get(), file_pattern_var.get(), zip_name_var.get())

        def on_cancel():
            dialog.destroy()

        ok_button = ttk.Button(button_frame, text="Tamam", command=on_ok)
        ok_button.pack(side=tk.LEFT, expand=True, padx=5)
        cancel_button = ttk.Button(button_frame, text="İptal", command=on_cancel)
        cancel_button.pack(side=tk.LEFT, expand=True, padx=5)

        dialog.bind("<Escape>", lambda e: on_cancel())
        self.app.wait_window(dialog)

    def _execute_compression(self, source_folder_path, include_subfolders, file_pattern, user_zip_filename):
        # backup_dir_name = "backups" # utils'den BACKUP_FOLDER_BASENAME kullanılacak
        abs_source_folder_path = os.path.abspath(source_folder_path)
        abs_backup_dir_path = os.path.abspath(os.path.join(self.app.base_path, BACKUP_FOLDER_BASENAME))
        normcase_abs_backup_dir_path = os.path.normcase(abs_backup_dir_path)
        os.makedirs(abs_backup_dir_path, exist_ok=True)
        folder_name = os.path.basename(abs_source_folder_path)
        zip_filename = user_zip_filename.strip()
        if not zip_filename.lower().endswith(".zip"):
            zip_filename += ".zip"
        abs_zip_file_path = os.path.abspath(os.path.join(abs_backup_dir_path, zip_filename))
        normcase_abs_zip_file_path = os.path.normcase(abs_zip_file_path)

        self.app.status_label.config(text=f"'{folder_name}' sıkıştırılıyor...")
        self.app.activity_progressbar.pack(side=tk.RIGHT, padx=5, pady=2)
        self.app.activity_progressbar.start(10)
        self.app.update_idletasks()
        self.app.long_operation_in_progress = True
        
        thread = threading.Thread(target=operations.perform_compression_in_thread,
                                   args=(self.app, abs_source_folder_path, include_subfolders,
                                         abs_zip_file_path, normcase_abs_zip_file_path,
                                         abs_backup_dir_path, normcase_abs_backup_dir_path, folder_name, # backup_dir_name operations'a gönderiliyor
                                         BACKUP_FOLDER_BASENAME, file_pattern)) # Burada da BACKUP_FOLDER_BASENAME kullanılıyor
        thread.daemon = True
        thread.start()

    def _handle_compression_success(self, folder_name, abs_zip_file_path, abs_backup_dir_path):
        self.app.activity_progressbar.stop()
        self.app.status_label.config(text=f"'{folder_name}' başarıyla sıkıştırıldı.")
        self.app.update_idletasks()
        self.app.long_operation_in_progress = False
        history_message = f"'{folder_name}' -> '{os.path.basename(abs_zip_file_path)}' ({abs_backup_dir_path})"
        self.app.db.add_history(f"Sıkıştırıldı: {history_message}", event_type="compress")
        messagebox.showinfo("Sıkıştırma Başarılı",
                            f"'{folder_name}' klasörü başarıyla sıkıştırıldı.\n\n"
                            f"Kaydedilen yer: {abs_zip_file_path}",
                            parent=self.app)
        self.app.activity_progressbar.pack_forget()
        self.app.file_browser.populate_file_list(abs_backup_dir_path) # Call via app.file_browser
        self.app.status_label.config(text="Hazır.")
        self.app.update_idletasks()

    def _handle_compression_error(self, folder_name, e, abs_zip_file_path):
        self.app.activity_progressbar.stop()
        self.app.status_label.config(text="Sıkıştırma hatası!")
        self.app.update_idletasks()
        self.app.long_operation_in_progress = False
        messagebox.showerror("Sıkıştırma Hatası",
                             f"'{folder_name}' klasörü sıkıştırılırken bir hata oluştu:\n{e}",
                             parent=self.app)
        self.app.activity_progressbar.pack_forget()
        self.app.status_label.config(text="Hazır.")
        self.app.update_idletasks()
        if os.path.exists(abs_zip_file_path):
            try: os.remove(abs_zip_file_path)
            except OSError: pass

    # --- EXE Conversion Methods ---
    def convert_py_to_exe(self, py_file_path):
        if self.app.long_operation_in_progress:
            messagebox.showwarning("İşlem Devam Ediyor", "Başka bir uzun süreli işlem (sıkıştırma veya EXE çevirme) zaten devam ediyor.", parent=self.app)
            return
        py_file_name = os.path.basename(py_file_path)
        if not messagebox.askyesno("EXE'ye Çevir",
                                   f"'{py_file_name}' dosyasını tek bir EXE dosyasına çevirmek istediğinizden emin misiniz?\n\n"
                                   "Bu işlem biraz zaman alabilir ve PyInstaller'ın sisteminizde kurulu ve PATH'e ekli olmasını gerektirir.",
                                   parent=self.app):
            return
        pyinstaller_exe = shutil.which("pyinstaller")
        if not pyinstaller_exe:
            messagebox.showerror("Hata", "PyInstaller bulunamadı.\nLütfen PyInstaller'ı kurun ve PATH ortam değişkeninize ekleyin.", parent=self.app)
            return
        self.app.status_label.config(text=f"'{py_file_name}' EXE'ye çevriliyor...")
        self.app.activity_progressbar.pack(side=tk.RIGHT, padx=5, pady=2)
        self.app.activity_progressbar.start(10)
        self.app.update_idletasks()
        self.app.long_operation_in_progress = True
        thread = threading.Thread(target=operations.perform_exe_conversion_in_thread,
                                   args=(self.app, py_file_path, pyinstaller_exe))
        thread.daemon = True
        thread.start()

    def _handle_exe_conversion_success(self, original_py_name, exe_path):
        messagebox.showinfo("Başarılı", f"'{original_py_name}' başarıyla '{os.path.basename(exe_path)}' olarak EXE'ye çevrildi.\n\nKaydedilen yer: {exe_path}", parent=self.app)
        self.app.file_browser.populate_file_list(os.path.dirname(exe_path)) # Call via app.file_browser

    def _handle_exe_conversion_error(self, original_py_name, error_message):
        messagebox.showerror("EXE Çevirme Hatası", f"'{original_py_name}' dosyası EXE'ye çevrilirken hata oluştu:\n\n{error_message}", parent=self.app)

    def _finalize_exe_conversion_ui(self):
        self.app.activity_progressbar.stop()
        self.app.activity_progressbar.pack_forget()
        self.app.status_label.config(text="Hazır.")
        self.app.update_idletasks()
        self.app.long_operation_in_progress = False