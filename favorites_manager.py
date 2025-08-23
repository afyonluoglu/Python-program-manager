# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, simpledialog # simpledialog eklendi
import os

class FavoritesManager:
    def __init__(self, app_instance):
        self.app = app_instance # Ana App örneğini sakla

    def _populate_favorites_list(self):
        """Favoriler listesini (Treeview) doldurur."""
        if not self.app.favorites_list_treeview:
            return
        for i in self.app.favorites_list_treeview.get_children():
            self.app.favorites_list_treeview.delete(i)

        favorites_data = self.app.db.get_favorites() # (path, timestamp, alias, order_index) listesi döner
        for fav_path, _timestamp, alias, _order_index in favorites_data:
            display_name = alias
            if not display_name: # Eğer alias veritabanında boş veya None ise
                filename_base = os.path.basename(fav_path)
                if filename_base.lower().endswith(".py"):
                    display_name = filename_base[:-3] # .py uzantısını kaldır
                else:
                    display_name = filename_base # Diğer dosya türleri için (eğer favorilere eklenebilirse)

            icon_to_use = self.app.file_icon if self.app.file_icon else None
            self.app.favorites_list_treeview.insert("", tk.END, text=display_name, image=icon_to_use,
                                                values=(fav_path,))

    def _show_favorites_panel(self):
        """Favoriler panelini gösterir."""
        if self.app.favorites_pane:
            is_currently_in_panes = False
            try:
                is_currently_in_panes = str(self.app.favorites_pane) in self.app.paned_window.panes()
            except tk.TclError: # panes() hata verebilir
                pass

            if not is_currently_in_panes:
                try:
                    self.app.paned_window.add(self.app.favorites_pane, weight=1)
                    self.app.update_idletasks() # Ekleme sonrası UI güncellemesi
                except tk.TclError as e:
                    if "already managed" in str(e).lower() or "already added" in str(e).lower():
                        pass 
                    else:
                        print(f"❗ HATA: Favoriler paneli eklenirken TclError: {e}")
                        return 

            self._populate_favorites_list()
            self.app.db.set_setting("favorites_panel_visible", "1")
            self.app.paned_window.update_idletasks()
            self.app._apply_saved_sash_position(manage_visibility=False)

    def _hide_favorites_panel(self):
        """Favoriler panelini gizler."""
        if self.app.favorites_pane:
            self.app.db.set_setting("favorites_panel_visible", "0")
            is_currently_in_panes = False
            try:
                is_currently_in_panes = str(self.app.favorites_pane) in self.app.paned_window.panes()
            except tk.TclError: 
                pass

            if is_currently_in_panes:
                try:
                    self.app.paned_window.forget(self.app.favorites_pane)
                    self.app.update_idletasks()
                except tk.TclError as e:
                    print(f"❗ HATA: Favoriler paneli gizlenirken TclError: {e}")
            self.app.paned_window.update_idletasks()

    def _toggle_favorites_panel(self):
        """Favoriler panelinin görünürlüğünü değiştirir."""
        is_currently_visible = False
        if self.app.favorites_pane:
            try:
                is_currently_visible = str(self.app.favorites_pane) in self.app.paned_window.panes()
            except tk.TclError: 
                 pass 

        if is_currently_visible:
            self._hide_favorites_panel()
        else:
            self._show_favorites_panel()

    def _add_to_favorites(self, file_path):
        """Bir dosyayı favorilere ekler."""
        if not os.path.exists(file_path):
            messagebox.showerror("Hata", f"Dosya bulunamadı: {file_path}", parent=self.app)
            return

        filename_base = os.path.basename(file_path)
        suggested_alias = filename_base
        if filename_base.lower().endswith(".py"):
            suggested_alias = filename_base[:-3]

        alias = simpledialog.askstring("Favori Adı",
                                       f"'{filename_base}' için favorilerde görünecek bir ad girin:",
                                       initialvalue=suggested_alias,
                                       parent=self.app)

        if alias is None: # Kullanıcı iptal etti
            return
        alias = alias.strip()
        if not alias: # Kullanıcı boş bir dize girdiyse, önerilen adı kullan
            alias = suggested_alias

        self.app.db.add_favorite(file_path, alias)
        self._populate_favorites_list()
        self.app.status_label.config(text=f"'{alias}' favorilere eklendi.")
        is_fav_panel_visible_now = False
        if self.app.favorites_pane:
            try:
                is_fav_panel_visible_now = str(self.app.favorites_pane) in self.app.paned_window.panes()
            except tk.TclError: pass
        if not is_fav_panel_visible_now:
            messagebox.showinfo("Favorilere Eklendi",
                                f"'{alias}' favorilere eklendi.\n"
                                "Görünüm menüsünden favoriler panelini açabilirsiniz.", parent=self.app)

    def _remove_from_favorites(self, file_path):
        """Bir dosyayı favorilerden kaldırır."""
        filename_to_display = os.path.basename(file_path)
        self.app.db.remove_favorite(file_path)

        # Kalan favorilerin sıralamasını güncelle (order_index'leri ardışık yapmak için)
        remaining_favorites_data = self.app.db.get_favorites()
        if remaining_favorites_data:
            paths_to_reorder = [fav_data[0] for fav_data in remaining_favorites_data]
            self.app.db.update_favorites_order(paths_to_reorder)

        self._populate_favorites_list()
        self.app.status_label.config(text=f"'{filename_to_display}' favorilerden kaldırıldı.")

    def _edit_favorite_alias(self, file_path):
        """Favori bir dosyanın takma adını düzenler."""
        current_alias_in_db = None
        # Veritabanından mevcut takma adı al
        favorites_data = self.app.db.get_favorites()
        # favorites_data artık (path, timestamp, alias, order_index) içeriyor
        # Bu yüzden döngüdeki unpacking'i düzeltmemiz gerekiyor.
        # Ancak _edit_favorite_alias sadece alias'a ihtiyaç duyuyor, bu yüzden
        # _order_index'i yok sayabiliriz.
        for fav_p, _ts, alias_val, _oi in favorites_data:
            if fav_p == file_path:
                current_alias_in_db = alias_val
                break

        filename_base = os.path.basename(file_path)
        initial_prompt_value = current_alias_in_db
        if not initial_prompt_value: # Eğer DB'de alias yoksa veya boşsa, dosya adından türet
            if filename_base.lower().endswith(".py"):
                initial_prompt_value = filename_base[:-3]
            else:
                initial_prompt_value = filename_base

        new_alias = simpledialog.askstring("Takma Adı Düzenle",
                                           f"'{filename_base}' için yeni takma ad:",
                                           initialvalue=initial_prompt_value,
                                           parent=self.app)
        if new_alias is not None: # Kullanıcı iptal etmediyse
            new_alias = new_alias.strip()
            if not new_alias: # Kullanıcı boş bir dize girdiyse, varsayılanı (uzantısız dosya adı) kullan
                messagebox.showwarning("Geçersiz Takma Ad", "Takma ad boş olamaz. Değişiklik yapılmadı.", parent=self.app)
                return
            self.app.db.update_favorite_alias(file_path, new_alias)
            self._populate_favorites_list()
            self.app.status_label.config(text=f"'{filename_base}' için takma ad '{new_alias}' olarak güncellendi.")

    def _show_favorites_context_menu(self, event):
        """Favoriler listesinde sağ tıklandığında içerik menüsünü gösterir."""
        selected_item_id = self.app.favorites_list_treeview.identify_row(event.y)
        if not selected_item_id: return

        self.app.favorites_list_treeview.selection_set(selected_item_id)
        self.app.favorites_list_treeview.focus(selected_item_id)

        item_data = self.app.favorites_list_treeview.item(selected_item_id)
        file_path = item_data["values"][0]

        context_menu = tk.Menu(self.app, tearoff=0)
        
        def run_and_select_file():
            # Dosyanın bulunduğu klasörü al
            folder_path = os.path.dirname(file_path)
            
            # Klasörün yolunu tutan TreeView öğesini bul
            folder_found = False
            for node_id in self.app.dir_tree.get_children(''):
                node_path = self.app.dir_tree.item(node_id)['values'][0]
                # Alt klasörleri de kontrol et
                if folder_path.startswith(node_path):
                    folder_found = True
                    # Alt klasörlere git
                    current_node = node_id
                    remaining_path = folder_path[len(node_path):].strip(os.sep).split(os.sep)
                    
                    for subfolder in remaining_path:
                        found = False
                        for child_id in self.app.dir_tree.get_children(current_node):
                            if self.app.dir_tree.item(child_id)['text'] == subfolder:
                                current_node = child_id
                                found = True
                                # Klasörü genişlet
                                self.app.dir_tree.item(current_node, open=True)
                                break
                        if not found:
                            break
                    
                    # Klasörü seç
                    self.app.dir_tree.focus(current_node)
                    self.app.dir_tree.selection_set(current_node)
                    self.app.dir_tree.see(current_node)
                    
                    # Sağ paneli güncelle
                    self.app.file_browser.populate_file_list(folder_path)
                    
                    # GUI güncellemesinin tamamlanması için biraz bekle ve sonra seçim yap
                    def select_file():
                        for item_id in self.app.file_list.get_children():
                            item_values = self.app.file_list.item(item_id)["values"]
                            if len(item_values) > 2 and item_values[2] == file_path:  # values[2] dosyanın tam yolu
                                self.app.file_list.selection_set(item_id)
                                self.app.file_list.focus(item_id)
                                self.app.file_list.see(item_id)  # Seçili öğeyi görünür yap
                                break
                    
                    self.app.after(100, select_file)  # 100ms sonra seçim yap
                    break
            
            if not folder_found:
                messagebox.showwarning("Uyarı", f"Dosyanın klasörü ({folder_path}) sol panelde bulunamadı.", parent=self.app)
                return
            
            # Dosyayı çalıştır
            self.app.run_python_file(file_path, source="run_normal")
        
        context_menu.add_command(label="Çalıştır", command=run_and_select_file)
        context_menu.add_command(label="Favorilerden Kaldır",
                               command=lambda p=file_path: self._remove_from_favorites(p))
        context_menu.add_command(label="Takma Adı Düzenle",
                               command=lambda p=file_path: self._edit_favorite_alias(p))
        context_menu.add_command(label="Dosyaya Git", 
                               command=lambda p=file_path: self.app.file_browser.go_to_file(p))
        context_menu.tk_popup(event.x_root, event.y_root)

    def _on_favorite_double_click(self, event):
        """Favoriler listesindeki bir dosyaya çift tıklandığında çalıştırır."""
        selected_item_id = self.app.favorites_list_treeview.focus()
        if not selected_item_id: return
        item_data = self.app.favorites_list_treeview.item(selected_item_id)
        file_path = item_data["values"][0]        

        # Dosyanın bulunduğu klasörü al
        folder_path = os.path.dirname(file_path)
        
        # SEÇİLEN FAVORİ PYTHON DOSYASINI TREEVIEW'LERDE KOINUMLANDIRAN KOD - İPTAL EDİLDİ: 26.07.2025
        # # Klasörün yolunu tutan TreeView öğesini bul
        # folder_found = False
        # for node_id in self.app.dir_tree.get_children(''):
        #     node_path = self.app.dir_tree.item(node_id)['values'][0]
        #     # Alt klasörleri de kontrol et
        #     if folder_path.startswith(node_path):
        #         folder_found = True
        #         current_node = node_id
        #         remaining_path = folder_path[len(node_path):].strip(os.sep).split(os.sep)
                
        #         for subfolder in remaining_path:
        #             # Eğer placeholder '...' varsa, alt düğümleri yükle
        #             children = self.app.dir_tree.get_children(current_node)
        #             if children and self.app.dir_tree.item(children[0], 'text') == '...':
        #                 self.app.dir_tree.delete(children[0])
        #                 try:
        #                     node_val = self.app.dir_tree.item(current_node, 'values')[0]
        #                     self.app.file_browser._populate_node_children(current_node, node_val)
        #                 except Exception:
        #                     pass
        #             found = False
        #             for child_id in self.app.dir_tree.get_children(current_node):
        #                 if self.app.dir_tree.item(child_id)['text'] == subfolder:
        #                     current_node = child_id
        #                     found = True
        #                     # Klasörü genişlet
        #                     self.app.dir_tree.item(current_node, open=True)
        #                     break
        #             if not found:
        #                 break
                
        #         # Klasörü seç
        #         self.app.dir_tree.focus(current_node)
        #         self.app.dir_tree.selection_set(current_node)
        #         self.app.dir_tree.see(current_node)
                
        #         # Sağ paneli güncelle
        #         self.app.file_browser.populate_file_list(folder_path)
                
        #         # GUI güncellemesinin tamamlanması için biraz bekle ve sonra seçim yap
        #         def select_file():
        #             for item_id in self.app.file_list.get_children():
        #                 item_values = self.app.file_list.item(item_id)["values"]
        #                 if len(item_values) > 2 and item_values[2] == file_path:  # values[2] dosyanın tam yolu
        #                     self.app.file_list.selection_set(item_id)
        #                     self.app.file_list.focus(item_id)
        #                     self.app.file_list.see(item_id)  # Seçili öğeyi görünür yap
        #                     break
                
        #         self.app.after(100, select_file)  # 100ms sonra seçim yap
        #         break
        
        # if not folder_found:
        #     messagebox.showwarning("Uyarı", f"Dosyanın klasörü ({folder_path}) sol panelde bulunamadı.", parent=self.app)
        #     return
        
        # Dosyayı çalıştır
        self.app.run_python_file(file_path, source="run_normal")

    def _move_favorite_up(self):
        """Seçili favoriyi listede bir yukarı taşır."""
        self._move_favorite_selected_item("up")

    def _move_favorite_down(self):
        """Seçili favoriyi listede bir aşağı taşır."""
        self._move_favorite_selected_item("down")

    def _move_favorite_selected_item(self, direction):
        """Seçili favoriyi belirtilen yönde taşır."""
        selected_item_id = self.app.favorites_list_treeview.focus()
        if not selected_item_id:
            messagebox.showwarning("Seçim Yok", "Lütfen yukarı/aşağı taşımak için bir favori seçin.", parent=self.app)
            return

        all_current_favorites_data = self.app.db.get_favorites() # (path, ts, alias, order_idx)
        if not all_current_favorites_data:
            return

        ordered_paths = [fav_data[0] for fav_data in all_current_favorites_data]
        selected_path_from_treeview = self.app.favorites_list_treeview.item(selected_item_id, "values")[0]

        try:
            current_idx = ordered_paths.index(selected_path_from_treeview)
        except ValueError:
            messagebox.showerror("Hata", "Seçili favori mevcut favoriler listesinde bulunamadı.", parent=self.app)
            return

        if direction == "up":
            if current_idx > 0:
                ordered_paths.insert(current_idx - 1, ordered_paths.pop(current_idx))
            else: return # Zaten en üstte
        elif direction == "down":
            if current_idx < len(ordered_paths) - 1:
                ordered_paths.insert(current_idx + 1, ordered_paths.pop(current_idx))
            else: return # Zaten en altta
        else: return

        self.app.db.update_favorites_order(ordered_paths)
        self._populate_favorites_list()

        for item_id_in_tree in self.app.favorites_list_treeview.get_children():
            item_data = self.app.favorites_list_treeview.item(item_id_in_tree)
            if item_data["values"] and item_data["values"][0] == selected_path_from_treeview:
                self.app.favorites_list_treeview.selection_set(item_id_in_tree)
                self.app.favorites_list_treeview.focus(item_id_in_tree)
                self.app.favorites_list_treeview.see(item_id_in_tree)
                break