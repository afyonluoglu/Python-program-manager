# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser

from utils import DEFAULT_DARK_THEME_COLORS # utils'dan import

class ThemeManager:
    def __init__(self, app_instance):
        self.app = app_instance

    def apply_custom_theme(self):
        """Veritabanından özel tema renklerini okur ve uygular."""
        active_theme_name = self.app.db.get_active_theme_name()
        
        if active_theme_name:
            colors_config = self.app.db.get_theme(active_theme_name)
            if colors_config: # Tema bulundu ve yapılandırma yüklendi
                self._apply_colors(colors_config)
            else:
                # Aktif tema adı ayarlanmış, ancak yapılandırma bulunamadı (örn. silinmiş tema)
                print(f"UYARI: Aktif tema '{active_theme_name}' için yapılandırma bulunamadı. Varsayılan koyu tema uygulanıyor.")
                self._apply_colors(DEFAULT_DARK_THEME_COLORS.copy())
                self.app.db.set_active_theme_name("") # Geçersiz aktif tema adını temizle
        else:
            # Aktif tema ayarlanmamış (örn. sıfırlama sonrası veya ilk çalıştırma)
            # Varsayılan koyu temayı uygula
            self._apply_colors(DEFAULT_DARK_THEME_COLORS.copy())

    def _apply_colors(self, colors_config):
        """Verilen renk sözlüğünü ilgili widget'lara uygular."""
        try:
            if colors_config.get("main_bg"):
                try:
                    self.app.config(background=colors_config["main_bg"])
                except tk.TclError:
                     print(f"Ana pencere arka planı ayarlanamadı: {colors_config['main_bg']}")
                self.app.style.configure("TFrame", background=colors_config["main_bg"])
                self.app.style.configure(".", background=colors_config["main_bg"]) 

            tree_style_options_to_set = {}
            tree_bg_val = colors_config.get("tree_bg")
            if tree_bg_val:
                tree_style_options_to_set["background"] = tree_bg_val
                tree_style_options_to_set["fieldbackground"] = tree_bg_val

            tree_fg_val = colors_config.get("tree_fg")
            if tree_fg_val:
                tree_style_options_to_set["foreground"] = tree_fg_val

            if tree_style_options_to_set:
                try:
                    self.app.style.configure("Treeview", **tree_style_options_to_set)
                except tk.TclError as e:
                    print(f"Treeview temel renkleri ayarlanamadı (_apply_colors içinde): {e}")

            map_options = {}
            tree_select_fg_val = colors_config.get("tree_select_fg")
            if tree_select_fg_val:
                 map_options['foreground'] = [('selected', tree_select_fg_val)]

            tree_select_bg_val = colors_config.get("tree_select_bg")
            if tree_select_bg_val:
                 map_options['background'] = [('selected', tree_select_bg_val)]

            if map_options:
                try:
                    self.app.style.map('Treeview', **map_options)
                except tk.TclError as e:
                    print(f"Treeview seçili durum renkleri ayarlanamadı (_apply_colors içinde): {e}")

            if colors_config.get("button_bg"):
                 self.app.style.configure("TButton", background=colors_config["button_bg"])
        except tk.TclError as e:
            print(f"Renkler uygulanırken hata: {e}")

    def manage_themes(self):
        """Tema renklerini yönetmek için pencere açar."""
        theme_window = tk.Toplevel(self.app)
        theme_window.title("Tema Yönetimi")
        theme_window.geometry("550x450")
        theme_window.transient(self.app)
        
        self.app.load_or_center_window("themes", theme_window, 550, 450)

        def close_themes():
            geom = theme_window.winfo_geometry()
            self.app.db.save_window_geometry("themes", geom)
            theme_window.destroy()

        theme_window.grab_set()
        theme_window.focus_set()
        theme_window.protocol("WM_DELETE_WINDOW", close_themes)
        
        main_frame = ttk.Frame(theme_window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(main_frame, text="Kaydedilmiş Temalar", padding="5")
        list_frame.grid(row=0, column=0, padx=(0, 10), pady=(0, 10), sticky="ns")
        list_frame.rowconfigure(0, weight=1)

        theme_listbox = tk.Listbox(list_frame, exportselection=False, height=10)
        theme_listbox.grid(row=0, column=0, sticky="nsew")
        theme_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=theme_listbox.yview)
        theme_listbox.config(yscrollcommand=theme_scrollbar.set)
        theme_scrollbar.grid(row=0, column=1, sticky="ns")

        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=0, column=1, pady=(0, 10), sticky="nsew")
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Tema Adı:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        theme_name_var = tk.StringVar()
        theme_name_entry = ttk.Entry(settings_frame, textvariable=theme_name_var, width=30)
        theme_name_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky='ew')

        current_colors_vars = {
            "main_bg": tk.StringVar(), "tree_bg": tk.StringVar(),
            "tree_fg": tk.StringVar(), "button_bg": tk.StringVar(),
            "tree_select_fg": tk.StringVar(), "tree_select_bg": tk.StringVar()
        }
        swatches = {}

        def pick_color_for_theme(color_var, swatch_label):
            initial_color = color_var.get()
            try:
                result = colorchooser.askcolor(initialcolor=initial_color, title="Renk Seçin", parent=theme_window)
                if result and result[1]:
                    new_color = result[1]
                    color_var.set(new_color)
                    swatch_label.config(bg=new_color)
            except tk.TclError:
                 result = colorchooser.askcolor(title="Renk Seçin", parent=theme_window)
                 if result and result[1]:
                    new_color = result[1]
                    color_var.set(new_color)
                    swatch_label.config(bg=new_color)

        row_idx = 1
        for key, label_text in [("main_bg", "Ana Arka Plan:"), ("tree_bg", "Liste Arka Plan:"),
                                ("tree_fg", "Liste Yazı Rengi:"), ("button_bg", "Düğme Arka Plan:"),
                                ("tree_select_fg", "Liste Seçili Yazı:"), ("tree_select_bg", "Liste Seçili Arka Plan:")]:
            ttk.Label(settings_frame, text=label_text).grid(row=row_idx, column=0, padx=5, pady=5, sticky='w')
            swatch = tk.Label(settings_frame, text="    ", bg="white", relief="sunken", borderwidth=1)
            swatch.grid(row=row_idx, column=1, padx=5, pady=5, sticky='w')
            swatches[key] = swatch
            btn = ttk.Button(settings_frame, text="Seç...", command=lambda k=key, s=swatch: pick_color_for_theme(current_colors_vars[k], s))
            btn.grid(row=row_idx, column=2, padx=5, pady=5, sticky='ew')
            row_idx += 1

        def style_theme_listbox_local():
            active_theme_name = self.app.db.get_active_theme_name()
            colors_dict = self.app.db.get_theme(active_theme_name) if active_theme_name else {}
            list_bg = colors_dict.get("tree_bg", DEFAULT_DARK_THEME_COLORS.get("tree_bg", self.app.style.lookup("Listbox", "background", default="white")))
            list_fg = colors_dict.get("tree_fg", DEFAULT_DARK_THEME_COLORS.get("tree_fg", self.app.style.lookup("Listbox", "foreground", default="black")))
            list_select_bg = colors_dict.get("tree_select_bg", DEFAULT_DARK_THEME_COLORS.get("tree_select_bg", self.app.style.lookup("Listbox", "selectbackground", default="#0078D7")))
            list_select_fg = colors_dict.get("tree_select_fg", DEFAULT_DARK_THEME_COLORS.get("tree_select_fg", self.app.style.lookup("Listbox", "selectforeground", default="white")))
            theme_listbox.config(background=list_bg, foreground=list_fg, selectbackground=list_select_bg, selectforeground=list_select_fg)

        def load_theme_settings_to_ui(theme_name_to_load):
            theme_config = self.app.db.get_theme(theme_name_to_load) or {}
            theme_name_var.set(theme_name_to_load)
            default_main_bg = self.app.style.lookup('TFrame', 'background')
            default_tree_bg = self.app.style.lookup('Treeview', 'background')
            default_tree_fg = self.app.style.lookup('Treeview', 'foreground')
            default_button_bg = self.app.style.lookup('TButton', 'background')
            default_tree_select_fg = self.app.style.lookup('Treeview', 'foreground', ['selected']) or 'white'
            default_tree_select_bg = self.app.style.lookup('Treeview', 'background', ['selected']) or '#0078D7'

            current_colors_vars["main_bg"].set(theme_config.get("main_bg", default_main_bg))
            current_colors_vars["tree_bg"].set(theme_config.get("tree_bg", default_tree_bg))
            current_colors_vars["tree_fg"].set(theme_config.get("tree_fg", default_tree_fg))
            current_colors_vars["button_bg"].set(theme_config.get("button_bg", default_button_bg))
            current_colors_vars["tree_select_fg"].set(theme_config.get("tree_select_fg", default_tree_select_fg))
            current_colors_vars["tree_select_bg"].set(theme_config.get("tree_select_bg", default_tree_select_bg))

            for key, var in current_colors_vars.items():
                if key in swatches:
                    try: swatches[key].config(bg=var.get())
                    except tk.TclError: swatches[key].config(bg="white")

        def refresh_theme_listbox():
            theme_listbox.delete(0, tk.END)
            saved_themes = self.app.db.get_all_theme_names()
            for name in saved_themes: theme_listbox.insert(tk.END, name)
            active_theme = self.app.db.get_active_theme_name()
            if active_theme in saved_themes:
                try:
                    index = saved_themes.index(active_theme)
                    theme_listbox.selection_set(index)
                    theme_listbox.activate(index)
                    theme_listbox.see(index)
                    load_theme_settings_to_ui(active_theme)
                except ValueError:
                    theme_listbox.selection_clear(0, tk.END)
                    load_theme_settings_to_ui("")
            else:
                theme_listbox.selection_clear(0, tk.END)
                load_theme_settings_to_ui("")

        def on_theme_select_listbox(event):
            selected_indices = theme_listbox.curselection()
            if selected_indices:
                load_theme_settings_to_ui(theme_listbox.get(selected_indices[0]))

        theme_listbox.bind('<<ListboxSelect>>', on_theme_select_listbox)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(5, weight=1)

        def save_current_theme_settings():
            name = theme_name_var.get().strip()
            if not name:
                messagebox.showwarning("Eksik Bilgi", "Lütfen bir tema adı girin.", parent=theme_window)
                return
            current_settings = {k: v.get() for k, v in current_colors_vars.items() if v.get()}
            self.app.db.save_theme(name, current_settings)
            refresh_theme_listbox()
            try:
                 idx = list(theme_listbox.get(0, tk.END)).index(name)
                 theme_listbox.selection_clear(0, tk.END)
                 theme_listbox.selection_set(idx)
                 theme_listbox.activate(idx)
            except ValueError: pass
            messagebox.showinfo("Başarılı", f"'{name}' teması kaydedildi.", parent=theme_window)

        def delete_selected_theme_from_db():
            selected_indices = theme_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Seçim Yok", "Lütfen silmek için bir tema seçin.", parent=theme_window)
                return
            selected_theme_name = theme_listbox.get(selected_indices[0])
            if messagebox.askyesno("Tema Sil", f"'{selected_theme_name}' temasını silmek istediğinizden emin misiniz?", parent=theme_window):
                self.app.db.delete_theme(selected_theme_name)
                if self.app.db.get_active_theme_name() == selected_theme_name:
                    self.app.db.set_active_theme_name("")
                    self._apply_colors(DEFAULT_DARK_THEME_COLORS.copy()) # Apply default immediately
                    style_theme_listbox_local()
                refresh_theme_listbox()

        def apply_selected_theme_and_close(close_after_apply=False):
            selected_indices = theme_listbox.curselection()
            if not selected_indices:
                if close_after_apply:
                    close_themes()
                    return
                messagebox.showwarning("Seçim Yok", "Lütfen uygulamak için bir tema seçin.", parent=theme_window)
                return
            selected_theme_name = theme_listbox.get(selected_indices[0])
            theme_config = self.app.db.get_theme(selected_theme_name)
            if theme_config is not None:
                self._apply_colors(theme_config)
                self.app.db.set_active_theme_name(selected_theme_name)
                style_theme_listbox_local()
                if close_after_apply: close_themes()
            elif not close_after_apply:
                 messagebox.showerror("Hata", f"'{selected_theme_name}' teması yüklenemedi.", parent=theme_window)

        def reset_themes_to_default():
            self.app.db.set_active_theme_name("")
            self.app.style = ttk.Style(self.app)
            base_ttk_theme = self.app.db.get_setting("chosen_theme") or \
                             next((t for t in ['vista', 'xpnative', 'clam', 'alt', 'default'] if t in self.app.style.theme_names()), 'default')
            try: self.app.style.theme_use(base_ttk_theme)
            except tk.TclError: print(f"Temel ttk teması ({base_ttk_theme}) yüklenemedi, varsayılan kullanılıyor.")
            style_font = ("Segoe UI", 10)
            self.app.style.configure("Treeview", rowheight=25, font=style_font)
            self.app.style.configure("Treeview.Heading", font=(style_font[0], style_font[1], 'bold'))
            self._apply_colors(DEFAULT_DARK_THEME_COLORS.copy())
            style_theme_listbox_local()
            refresh_theme_listbox()

        save_btn = ttk.Button(button_frame, text="Kaydet", command=save_current_theme_settings)
        save_btn.grid(row=0, column=1, padx=5, pady=5)
        delete_btn = ttk.Button(button_frame, text="Sil", command=delete_selected_theme_from_db)
        delete_btn.grid(row=0, column=2, padx=5, pady=5)
        apply_btn = ttk.Button(button_frame, text="Uygula ve Kapat", command=lambda: apply_selected_theme_and_close(close_after_apply=True))
        apply_btn.grid(row=0, column=3, padx=5, pady=5)
        reset_btn = ttk.Button(button_frame, text="Varsayılana Dön", command=reset_themes_to_default)
        reset_btn.grid(row=0, column=4, padx=5, pady=5)

        refresh_theme_listbox()
        style_theme_listbox_local()
        theme_window.bind("<Escape>", lambda e: close_themes())
        self.app.wait_window(theme_window)