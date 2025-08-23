# -*- coding: utf-8 -*-

import json # Sütun genişliklerini yüklemek için
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog 
import os
from datetime import datetime
import zipfile # ZIP dosyalarını okumak için
import subprocess # ZIP içeriğini göstermek için
import platform # ZIP içeriğini göstermek için

# Yerel modüllerden importlar (App'den çağrılacakları için App'in importlarına benzer)
from db_manager import DatabaseManager # Sadece tip belirtmek için gerekebilir, App üzerinden erişilecek
from utils import ICON_FOLDER, ICON_PYTHON_FILE, ICON_COMPRESS, ICON_EXECUTABLE, ICON_UNKNOWN, BACKUP_FOLDER_BASENAME # İkon sabitleri ve yedekleme klasörü adı
from ui_dialogs import ZipContentsWindow # ZIP içeriği penceresi

class FileBrowser:
    def __init__(self, app_instance):
        self.app = app_instance

    def populate_tree(self, start_path):
        """Klasör ağacını belirtilen yoldan başlayarak doldurur."""
        for i in self.app.dir_tree.get_children():
            self.app.dir_tree.delete(i)

        try:
            if not os.path.isdir(start_path):
                 messagebox.showerror("Hata", f"Başlangıç klasörü bulunamadı veya geçerli değil:\n{start_path}", parent=self.app)
                 self.app.current_folder = None
                 self.app.db.set_setting("last_folder", "")
                 return

            root_name = os.path.basename(start_path) or start_path
            root_node = self.app.dir_tree.insert("", tk.END, text=root_name, open=True, values=[start_path])
            if self.app.folder_icon:
                self.app.dir_tree.item(root_node, image=self.app.folder_icon)

            self._populate_node_children(root_node, start_path)
            self.app.dir_tree.focus(root_node)
            self.app.dir_tree.selection_set(root_node)
            self.on_tree_select(None) # Manuel tetikleme
        except Exception as e:
             messagebox.showerror("Ağaç Doldurma Hatası", f"Klasör ağacı oluşturulurken hata:\n{e}", parent=self.app)

    def _populate_node_children(self, parent_node, parent_path):
        """Bir düğümün alt klasörlerini ağaca ekler (lazy loading için)."""
        try:
            for item in sorted(os.scandir(parent_path), key=lambda e: e.name):
                if item.is_dir() and not item.name.startswith('.'):
                    node_options = {"text": item.name, "open": False, "values": [item.path]}
                    if self.app.folder_icon:
                        node_options["image"] = self.app.folder_icon
                    node = self.app.dir_tree.insert(parent_node, tk.END, **node_options)
                    # Placeholder only if there are subdirectories
                    try:
                        if any(child.is_dir() and not child.name.startswith('.') for child in os.scandir(item.path)):
                            self.app.dir_tree.insert(node, tk.END, text="...")
                    except OSError:
                        pass
        except OSError as e:
            print(f"❗ Klasör taranırken hata {parent_path}: {e}")

    def on_node_expand(self, event=None):
        """Bir klasör düğümü genişletildiğinde alt klasörleri yükler."""
        node_id = self.app.dir_tree.focus()
        if not node_id: return

        children = self.app.dir_tree.get_children(node_id)
        if children and self.app.dir_tree.item(children[0], "text") == "...":
            self.app.dir_tree.delete(children[0])
            try:
                node_path = self.app.dir_tree.item(node_id, "values")[0]
                self._populate_node_children(node_id, node_path)
            except IndexError:
                 print(f"❗ Hata: Düğüm yolu alınamadı: {node_id}")
            except Exception as e:
                 print(f"❗ Düğüm genişletilirken hata: {e}")

    def on_tree_select(self, event):
        """Ağaçta bir klasör seçildiğinde dosya listesini günceller."""
        selected_item = self.app.dir_tree.focus()
        # Eğer placeholder '...' seçildiyse, işlemi iptal et
        try:
            if self.app.dir_tree.item(selected_item, 'text') == '...':
                return
        except Exception:
            pass

        if not selected_item:
            return
        
        # --- Mevcut (bir önceki) klasör için sütun genişliklerini kaydet ---
        if hasattr(self.app, 'file_list') and self.app.file_list.winfo_exists() and \
           hasattr(self.app, 'currently_displayed_folder_in_file_list') and \
           self.app.currently_displayed_folder_in_file_list and \
           os.path.isdir(self.app.currently_displayed_folder_in_file_list):
            try:
                current_col_widths = {
                    "#0": self.app.file_list.column("#0", "width"),
                    "description": self.app.file_list.column("description", "width"),
                    "date_modified": self.app.file_list.column("date_modified", "width")
                }

                abs_current_displayed_path = os.path.abspath(self.app.currently_displayed_folder_in_file_list)
                abs_backup_dir_path = os.path.abspath(os.path.join(self.app.base_path, BACKUP_FOLDER_BASENAME))
                is_backup_folder_displayed = os.path.normcase(abs_current_displayed_path) == os.path.normcase(abs_backup_dir_path)

                setting_key_to_save = "backup_list_column_widths" if is_backup_folder_displayed else "file_list_column_widths"
                
                self.app.db.set_setting(setting_key_to_save, json.dumps(current_col_widths))
                # print(f"BİLGİ: Dosya listesi sütun genişlikleri '{setting_key_to_save}' anahtarına kaydedildi (klasör değişikliği).")
            except tk.TclError as e_tcl: # Sütun bilgisi alınamazsa TclError oluşabilir
                print(f"🔸 UYARI: Dosya listesi sütun genişlikleri (klasör değişikliği) okunurken/kaydedilirken TclError: {e_tcl}")
            except Exception as e:
                print(f"❗ HATA: Dosya listesi sütun genişlikleri (klasör değişikliği) kaydedilemedi: {e}")
        # else:
            # print("BİLGİ: Önceki klasör için sütun genişlikleri kaydedilmedi (koşullar sağlanmadı).")
        # --- Sütun genişliklerini kaydetme sonu ---

        try:
            folder_path = self.app.dir_tree.item(selected_item, "values")[0]
            self.populate_file_list(folder_path)
        except IndexError:
             print(f"❗ Hata: Seçili düğüm yolu alınamadı: {selected_item}")
             for i in self.app.file_list.get_children():
                self.app.file_list.delete(i)
        except Exception as e:
             print(f"❗ Ağaç seçimi işlenirken hata: {e}")
             messagebox.showerror("Hata", f"Klasör seçimi işlenirken bir hata oluştu:\n{e}", parent=self.app)

    def setup_file_list_colors(self):
        """Dosya listesi için dosya türüne göre renk ayarlarını yapar."""
        # self.app.file_list.tag_configure("python_file", background="#E6F3FF", foreground="#CF0101")
        self.app.file_list.tag_configure("python_file", foreground="#CF0101")
        
        self.app.file_list.tag_configure("folder_item", background="#FAEDD9", foreground="#956B00")
        # self.app.file_list.tag_configure("zip_file", background="#FFF8E6", foreground="#CC6600")
        self.app.file_list.tag_configure("exe_file", foreground="#008414")
        self.app.file_list.tag_configure("json_file", foreground="#FF6600", background="#FFF8E6")  # Turuncu renk
        self.app.file_list.tag_configure("markdown_file", foreground="#0366D6", background="#F6F8FA")  # GitHub benzeri mavi
        self.app.file_list.tag_configure("other_file", foreground="#666666")

    @staticmethod
    def format_file_size(size_bytes):
        """Dosya boyutunu uygun birimle (KB, MB, GB) formatlı string olarak döndürür."""
        if size_bytes < 1024:
            return f"{size_bytes:,} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:,.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):,.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):,.2f} GB"

    def populate_file_list(self, folder_path):
        """Belirtilen klasördeki Python dosyalarını sağ bölmede listeler."""
        for i in self.app.file_list.get_children():
            self.app.file_list.delete(i)

        # Hangi klasörün görüntülendiğini App'e bildir
        self.app.currently_displayed_folder_in_file_list = folder_path

        try:
            if not os.path.isdir(folder_path):
                return

            # Add ".." entry to navigate to parent directory if not at the drive root
            parent_folder_path = os.path.dirname(folder_path)
            if os.path.normpath(parent_folder_path) != os.path.normpath(folder_path):
                # Check if folder_icon exists before using it
                parent_icon = self.app.folder_icon if hasattr(self.app, 'folder_icon') else None
                self.app.file_list.insert("", tk.END,
                                          text="..",
                                          image=parent_icon,
                                          values=("Üst Klasör", "<YOK>", parent_folder_path),
                                          tags=("parent_folder_item",))

            # Klasör içeriğini al ve sıralama için hazırla
            items_to_process = []
            try:
                for entry in os.scandir(folder_path):
                    items_to_process.append(entry)
            except OSError as e:
                messagebox.showerror("Hata", f"'{folder_path}' klasörü okunurken hata oluştu:\n{e}", parent=self.app)
                return

            # Yedekleme klasörü olup olmadığını kontrol et
            abs_current_folder_path = os.path.abspath(folder_path)
            abs_backup_dir_path = os.path.abspath(os.path.join(self.app.base_path, BACKUP_FOLDER_BASENAME))
            is_backup_folder = os.path.normcase(abs_current_folder_path) == os.path.normcase(abs_backup_dir_path)

            # Sütun genişliklerini yükle (yedekleme klasörüne özel veya genel)
            width_setting_key = "backup_list_column_widths" if is_backup_folder else "file_list_column_widths"
            saved_widths_json = self.app.db.get_setting(width_setting_key)
            if saved_widths_json:
                try:
                    saved_widths = json.loads(saved_widths_json)
                    if isinstance(saved_widths, dict):
                        for col_id, width_val in saved_widths.items():
                            if col_id in ("#0", "description", "date_modified"): # Geçerli sütunlar
                                try:
                                    self.app.file_list.column(col_id, width=int(width_val))
                                except (ValueError, tk.TclError) as e_col:
                                    print(f"❗ HATA: '{width_setting_key}' için '{col_id}' sütun genişliği ({width_val}) uygulanamadı: {e_col}")
                except json.JSONDecodeError as e:
                    print(f"❗ HATA: Kayıtlı sütun genişlikleri ('{width_setting_key}') okunamadı (JSON): {e}")
            else:
                # Kayıtlı ayar yoksa, varsayılan genişlikleri (UIManager._setup_ui'de tanımlanan) kullan
                # veya burada tekrar ayarla (güvenlik için)
                self.app.file_list.column("#0", width=250)
                self.app.file_list.column("description", width=300)
                self.app.file_list.column("date_modified", width=150)

            if is_backup_folder:
                # Yedekleme klasörü ise değiştirme tarihine göre azalan sırada sırala
                def get_mtime_for_sort(scandir_entry):
                    try:
                        return os.stat(scandir_entry.path).st_mtime
                    except OSError:
                        return -1 # Hata durumunda en sona at
                items_to_process.sort(key=get_mtime_for_sort, reverse=True)
                if hasattr(self.app, 'file_list_sort_column'):
                    self.app.file_list_sort_column = "date_modified"
                    self.app.file_list_sort_order_asc = False
            else:
                # Diğer klasörler için isme göre artan sırada sırala
                items_to_process.sort(key=lambda e: e.name.lower())
                if hasattr(self.app, 'file_list_sort_column'):
                    self.app.file_list_sort_column = "#0" # Dosya Adı
                    self.app.file_list_sort_order_asc = True

            datetime_str = '%Y.%m.%d - %H:%M'
            # item.name.lower() yerine item_name_lower kullanılacak
            for item in items_to_process:
                item_path = item.path
                item_name = item.name
                description = ""
                current_icon = None
                file_type_tag = None
                date_modified_str = "N/A"

                if item.is_dir():
                    description = "Klasör"
                    current_icon = self.app.folder_icon if hasattr(self.app, 'folder_icon') else None
                    file_type_tag = "folder_item"
                    try:
                        mod_timestamp = os.stat(item_path).st_mtime
                        date_modified_str = datetime.fromtimestamp(mod_timestamp).strftime(datetime_str)
                    except OSError:
                        date_modified_str = "N/A"
                elif item.is_file():
                    item_name_lower = item_name.lower()
                    if item_name_lower.endswith(".py"):
                        file_stat = os.stat(item_path)
                        size_in_bytes = file_stat.st_size
                        desc = self.app.db.get_description(item_path)
                        description = desc if desc else f" [{self.format_file_size(size_in_bytes)}]"
                        current_icon = self.app.file_icon if hasattr(self.app, 'file_icon') else None
                        file_type_tag = "python_file"
                    elif item_name_lower.endswith(".json"):
                        file_stat = os.stat(item_path)
                        size_in_bytes = file_stat.st_size
                        description = f"JSON Dosyası [{self.format_file_size(size_in_bytes)}]"
                        current_icon = self.app.file_icon if hasattr(self.app, 'file_icon') else None
                        file_type_tag = "json_file"
                    elif item_name_lower.endswith((".md", ".markdown")):
                        file_stat = os.stat(item_path)
                        size_in_bytes = file_stat.st_size
                        description = f"Markdown Dosyası [{self.format_file_size(size_in_bytes)}]"
                        current_icon = self.app.file_icon if hasattr(self.app, 'file_icon') else None
                        file_type_tag = "markdown_file"
                    elif item_name_lower.endswith(".zip"):
                        file_stat = os.stat(item_path)
                        mod_time_for_desc = datetime.fromtimestamp(file_stat.st_mtime).strftime(datetime_str)
                        size_in_bytes = file_stat.st_size
                        description = f"ZIP Arşivi - {self.format_file_size(size_in_bytes)}"
                        current_icon = self.app.zip_icon if hasattr(self.app, 'zip_icon') else None
                        file_type_tag = "zip_file"
                    elif item_name_lower.endswith(".exe"):
                        file_stat = os.stat(item_path)
                        mod_time_for_desc = datetime.fromtimestamp(file_stat.st_mtime).strftime(datetime_str)
                        size_in_bytes = file_stat.st_size
                        description = f"EXE Uygulaması - {self.format_file_size(size_in_bytes)}"
                        current_icon = self.app.exe_icon if hasattr(self.app, 'exe_icon') else None
                        file_type_tag = "exe_file"
                    elif item_name_lower.endswith(".db"):
                        try:
                            file_stat = os.stat(item_path)
                            mod_time_for_desc = datetime.fromtimestamp(file_stat.st_mtime).strftime(datetime_str)
                            size_in_bytes = file_stat.st_size
                            description = f"Veritabanı Dosyası - {self.format_file_size(size_in_bytes)}"
                        except OSError:
                            description = "Veritabanı Dosyası"
                        current_icon = self.app.db_icon if hasattr(self.app, 'db_icon') else None
                        file_type_tag = "db_file"
                    elif item_name_lower.endswith(".mp3"):
                        file_stat = os.stat(item_path)
                        mod_time_for_desc = datetime.fromtimestamp(file_stat.st_mtime).strftime(datetime_str)
                        size_in_bytes = file_stat.st_size
                        size_in_kb = size_in_bytes / (1024)
                        description = f"MP3 Ses Dosyası - {size_in_kb:,.2f} KB"
                        current_icon = self.app.mp3_icon if hasattr(self.app, 'mp3_icon') else None
                        file_type_tag = "mp3_file"
                    else: # Diğer tüm dosya türleri
                        try:
                            file_stat = os.stat(item_path)
                            mod_time_for_desc = datetime.fromtimestamp(file_stat.st_mtime).strftime(datetime_str)
                            size_in_bytes = file_stat.st_size
                            if size_in_bytes < 1024:
                                size_str = f"{size_in_bytes} B"
                            elif size_in_bytes < 1024 * 1024:
                                size_str = f"{size_in_bytes / 1024:,.1f} KB"
                            else:
                                size_str = f"{size_in_bytes / (1024 * 1024):,.2f} MB"
                            description = f"Dosya - {size_str}"
                        except OSError:
                            description = "Dosya" # Fallback
                        current_icon = self.app.unknown_icon if hasattr(self.app, 'unknown_icon') else None
                        file_type_tag = "other_file"

                    try:
                        mod_timestamp = os.stat(item_path).st_mtime
                        date_modified_str = datetime.fromtimestamp(mod_timestamp).strftime(datetime_str)
                    except OSError:
                        date_modified_str = "N/A"
                else:
                    continue # Skip other types like symlinks for now

                file_node_options = {"text": item_name, "values": (description, date_modified_str, item_path)}
                if current_icon:
                    file_node_options["image"] = current_icon
                
                if file_type_tag:
                    file_node_options["tags"] = (file_type_tag,)

                self.app.file_list.insert("", tk.END, **file_node_options)

            # Dosya listesi doldurulduktan sonra App'deki sıralama durumunu (yukarıda ayarlandı)
            # yansıtacak şekilde başlıkları güncelle.
            # Eğer yedekleme klasörü değilse ve kullanıcı daha önce bir sıralama yapmadıysa,
            # varsayılan olarak isme göre sıralanmış olacak ve başlıkta ok görünmeyecek
            # (eğer file_list_sort_column = None ve _update_file_list_header_indicators buna göre davranıyorsa)
            # veya "#0" (Dosya Adı) için artan ok görünecek.
            if hasattr(self.app, '_update_file_list_header_indicators'):
                self.app._update_file_list_header_indicators()

        except OSError as e:
            messagebox.showerror("Hata", f"Klasör okunurken hata oluştu:\n{e}", parent=self.app)
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya listesi doldurulurken beklenmedik hata:\n{e}", parent=self.app)

    def select_folder(self):
        """Kullanıcının yeni bir ana klasör seçmesini sağlar."""
        initial_dir = self.app.current_folder or os.path.expanduser("~")
        new_folder = filedialog.askdirectory(
            title="Python Dosyalarının Bulunduğu Ana Klasörü Seçin",
            initialdir=initial_dir,
            parent=self.app
        )
        if new_folder:
            self.app.current_folder = os.path.normpath(new_folder)
            self.app.db.set_setting("last_folder", self.app.current_folder)
            self.populate_tree(self.app.current_folder) # Kendi içindeki populate_tree'yi çağırır
            # Yeni kök seçildiğinde dosya listesini temizle (file_list App'de olduğu için App üzerinden)
            for i in self.app.file_list.get_children():
                self.app.file_list.delete(i)

    # Helper methods that might be called from App or other managers
    # These are kept here as they are tightly coupled with file browsing/listing

    def show_zip_contents(self, zip_file_path):
        """Belirtilen ZIP dosyasının içeriğini yeni bir pencerede gösterir."""
        try:
            if not zipfile.is_zipfile(zip_file_path):
                messagebox.showerror("Hata", f"'{os.path.basename(zip_file_path)}' geçerli bir ZIP dosyası değil.", parent=self.app)
                return
            with zipfile.ZipFile(zip_file_path, 'r') as zf:
                zip_items_info = zf.infolist()
        
            # ZIP dosyasının tam yolunu da geçir
            zip_window = ZipContentsWindow(self.app, zip_items_info, os.path.basename(zip_file_path), zip_file_path)
            zip_window.zip_file_path = zip_file_path  # Tam yolu manuel olarak ata
        except Exception as e:
            print(f"⚠️ ZIP içeriği gösterilirken hata: {e}")
            messagebox.showerror("❗ ZIP Okuma Hatası", f"ZIP dosyası ('{os.path.basename(zip_file_path)}') okunurken bir hata oluştu:\n{e}", parent=self.app)

    def go_to_file(self, file_path):
        """Seçili dosyanın bulunduğu klasörü dosya gezgininde açar."""
        folder_path = os.path.dirname(file_path)
        try:
            if not os.path.isdir(folder_path):
                 messagebox.showerror("Hata", f"Klasör bulunamadı:\n{folder_path}", parent=self.app)
                 return

            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)]) # check=True kaldırıldı
            elif system == "Darwin": # macOS
                subprocess.run(['open', '-R', os.path.normpath(file_path)], check=True)
            elif system == "Linux":
                subprocess.run(['xdg-open', os.path.normpath(folder_path)], check=True)
            else:
                messagebox.showinfo("Bilgi", f"'{system}' sistemi için 'Dosyaya Git' özelliği henüz desteklenmiyor.\nKlasör: {folder_path}", parent=self.app)
        except FileNotFoundError as e:
             messagebox.showerror("Hata", f"Dosya gezgini komutu bulunamadı: {e.cmd if hasattr(e, 'cmd') else ''}\nSisteminizde ilgili komut (explorer, open, xdg-open) bulunmuyor veya PATH'de değil.", parent=self.app)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Hata", f"Dosya gezgini komutu çalıştırılırken hata:\n{e}", parent=self.app)
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı:\n{e}", parent=self.app)

    def edit_description(self, file_path, item_id):
        """Seçili dosyanın açıklamasını düzenlemek için dialog açar."""
        current_desc = self.app.db.get_description(file_path) or ""
        file_name = os.path.basename(file_path)
        new_desc = simpledialog.askstring(
            "Dosya Açıklaması",
            f"'{file_name}' için açıklama:",
            initialvalue=current_desc,
            parent=self.app
        )

        if new_desc is not None:
            self.app.db.set_description(file_path, new_desc.strip())
            if self.app.file_list.exists(item_id):
                current_values = list(self.app.file_list.item(item_id, "values"))
                if len(current_values) == 3 and current_values[2] == file_path:
                    current_values[0] = new_desc.strip()
                    self.app.file_list.item(item_id, values=tuple(current_values))

    def rename_selected_file(self, old_file_path, item_id, file_type_hint):
        """Seçili dosyayı (ZIP) yeniden adlandırır."""
        current_name = os.path.basename(old_file_path)
        current_name_no_ext, current_ext = os.path.splitext(current_name)

        new_name_no_ext = simpledialog.askstring(
            "Dosya Adını Değiştir",
            f"'{current_name}' için yeni ad (uzantısız '{current_ext}'):",
            initialvalue=current_name_no_ext,
            parent=self.app
        )

        if new_name_no_ext is None:
            return

        new_name_no_ext = new_name_no_ext.strip()
        if not new_name_no_ext:
            messagebox.showerror("Hata", "Dosya adı boş olamaz.", parent=self.app)
            return

        new_filename = new_name_no_ext + current_ext
        folder_path = os.path.dirname(old_file_path)
        new_file_path = os.path.join(folder_path, new_filename)

        if old_file_path == new_file_path:
            return

        if os.path.exists(new_file_path):
            messagebox.showerror("Hata", f"'{new_filename}' adında bir dosya zaten var.", parent=self.app)
            return
        try:
            os.rename(old_file_path, new_file_path)
            self.app.db.add_history(f"Yeniden adlandırıldı: '{current_name}' -> '{new_filename}' ({folder_path})", event_type="rename")
            self.populate_file_list(folder_path)
            messagebox.showinfo("Başarılı", f"Dosya '{new_filename}' olarak yeniden adlandırıldı.", parent=self.app)
        except OSError as e:
            messagebox.showerror("Yeniden Adlandırma Hatası", f"Dosya yeniden adlandırılamadı:\n{e}", parent=self.app)

    def delete_file(self, file_path, item_id):
        """Seçili dosyayı onay alarak siler."""
        file_name = os.path.basename(file_path)
        if messagebox.askyesno("Dosya Sil",
                               f"'{file_name}' dosyasını kalıcı olarak silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                               icon='warning', parent=self.app):
            try:
                os.remove(file_path)
                self.app.db.delete_description(file_path)
                if self.app.file_list.exists(item_id):
                    self.app.file_list.delete(item_id)
                messagebox.showinfo("Başarılı", f"'{file_name}' dosyası başarıyla silindi.", parent=self.app)
            except OSError as e:
                messagebox.showerror("Silme Hatası", f"Dosya silinemedi:\n{e}", parent=self.app)
            except Exception as e:
                 messagebox.showerror("Hata", f"Dosya silinirken beklenmedik bir hata oluştu:\n{e}", parent=self.app)

    def on_file_delete_key(self, event):
        """Dosya listesinde DELETE tuşuna basıldığında seçili dosyayı siler."""
        selected_item = self.app.file_list.focus()
        if not selected_item: return
        try:
            file_path = self.app.file_list.item(selected_item, "values")[2]
            self.delete_file(file_path, selected_item)
        except IndexError:
            print(f"❗ Hata: DELETE tuşu ile silme için dosya yolu alınamadı: {selected_item}")
        except Exception as e:
            print(f"❗ DELETE tuşu ile silme işlenirken hata: {e}")

if __name__ == "__main__":
    print("##########################################################################################")
    print("  🔸  Bu dosya doğrudan çalıştırılamaz, Python Program Yöneticisi Filemanager modülüdür.")
    print("##########################################################################################")


