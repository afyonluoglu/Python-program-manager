# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

class UIManager:
    def __init__(self, app_instance):
        self.app = app_instance

    def _setup_ui(self):
        """Kullanıcı arayüzü elemanlarını oluşturur."""
        # Ana PanedWindow (yeniden boyutlandırılabilir bölmeler için)
        self.app.paned_window = ttk.PanedWindow(self.app, orient=tk.HORIZONTAL)
        self.app.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sol Bölme: Klasör Ağacı
        self.app.tree_frame = ttk.Frame(self.app.paned_window, padding="3 3 3 3")
        self.app.tree_frame.columnconfigure(0, weight=1)
        self.app.tree_frame.rowconfigure(0, weight=1)

        self.app.dir_tree = ttk.Treeview(self.app.tree_frame, show="tree headings")
        self.app.tree_scroll_y = ttk.Scrollbar(self.app.tree_frame, orient=tk.VERTICAL, command=self.app.dir_tree.yview)
        self.app.tree_scroll_x = ttk.Scrollbar(self.app.tree_frame, orient=tk.HORIZONTAL, command=self.app.dir_tree.xview)
        self.app.dir_tree.configure(yscrollcommand=self.app.tree_scroll_y.set, xscrollcommand=self.app.tree_scroll_x.set)

        self.app.dir_tree.grid(row=0, column=0, sticky='nsew')
        self.app.tree_scroll_y.grid(row=0, column=1, sticky='ns')
        self.app.tree_scroll_x.grid(row=1, column=0, sticky='ew')

        self.app.paned_window.add(self.app.tree_frame, weight=1)

        # Sağ Bölme: Dosya Listesi
        self.app.file_frame = ttk.Frame(self.app.paned_window, padding="3 3 3 3")
        self.app.file_frame.columnconfigure(0, weight=1)
        self.app.file_frame.rowconfigure(0, weight=1)

        self.app.file_list = ttk.Treeview(self.app.file_frame, columns=("description", "date_modified", "fullpath"), displaycolumns=("description", "date_modified"))
        self.app.file_list.heading("#0", text="Dosya Adı", 
                                   command=lambda: self.app.sort_file_list_by_column("#0"))
        self.app.file_list.heading("description", text="Açıklama",
                                   command=lambda: self.app.sort_file_list_by_column("description"))
        self.app.file_list.heading("date_modified", text="Değiştirme Tarihi",
                                   command=lambda: self.app.sort_file_list_by_column("date_modified"))
        # self.app.file_list.heading("#0", text="Dosya Adı")
        # self.app.file_list.heading("description", text="Açıklama")
        # self.app.file_list.heading("date_modified", text="Değiştirme Tarihi")

        self.app.file_list.column("#0", width=250, stretch=tk.YES, anchor='w')
        self.app.file_list.column("description", width=300, stretch=tk.YES, anchor='w')
        self.app.file_list.column("date_modified", width=150, stretch=tk.NO, anchor='w')

        # Sütun genişliklerinin yüklenmesi artık FileBrowser.populate_file_list içinde yapılacak.
        self.app.file_scroll_y = ttk.Scrollbar(self.app.file_frame, orient=tk.VERTICAL, command=self.app.file_list.yview)
        self.app.file_list.configure(yscrollcommand=self.app.file_scroll_y.set)

        self.app.file_list.grid(row=0, column=0, sticky='nsew')
        self.app.file_scroll_y.grid(row=0, column=1, sticky='ns')

        self.app.paned_window.add(self.app.file_frame, weight=2)

        # Sağ Bölme 2: Favoriler Paneli
        self.app.favorites_pane = ttk.Frame(self.app.paned_window, padding="3 3 3 3")
        self.app.favorites_pane.columnconfigure(0, weight=1)
        self.app.favorites_pane.rowconfigure(0, weight=1)

        self.app.favorites_list_treeview = ttk.Treeview(self.app.favorites_pane, columns=("fullpath",), displaycolumns=())
        self.app.favorites_list_treeview.heading("#0", text="Favori Dosyalar", anchor='w')
        self.app.favorites_list_treeview.column("#0", width=200, stretch=tk.YES, anchor='w')
        self.app.favorites_list_treeview.column("fullpath", width=0, stretch=tk.NO, anchor='w')

        fav_scrollbar_y = ttk.Scrollbar(self.app.favorites_pane, orient=tk.VERTICAL, command=self.app.favorites_list_treeview.yview)
        self.app.favorites_list_treeview.configure(yscrollcommand=fav_scrollbar_y.set)

        self.app.favorites_list_treeview.grid(row=0, column=0, sticky='nsew')
        fav_scrollbar_y.grid(row=0, column=1, sticky='ns')

        # Favoriler paneli için kontrol butonları (Yukarı, Aşağı)
        fav_controls_frame = ttk.Frame(self.app.favorites_pane)
        fav_controls_frame.grid(row=1, column=0, columnspan=2, pady=(5,0), sticky='ew')

        self.app.fav_up_button = ttk.Button(fav_controls_frame, text="Yukarı",
                                            image=self.app.arrow_up_icon, compound=tk.LEFT,
                                            command=self.app.favorites_manager._move_favorite_up)
        self.app.fav_up_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.app.fav_down_button = ttk.Button(fav_controls_frame, text="Aşağı",
                                              image=self.app.arrow_down_icon, compound=tk.LEFT,
                                              command=self.app.favorites_manager._move_favorite_down)
        self.app.fav_down_button.pack(side=tk.LEFT, padx=2, pady=2)


        # Favoriler paneli kapatma butonu
        fav_close_button = ttk.Button(self.app.favorites_pane, text="Paneli Kapat", command=self.app.favorites_manager._hide_favorites_panel)
        fav_close_button.grid(row=2, column=0, columnspan=2, pady=(5,0), sticky='ew')

        # Olay bağlamaları App.__init__ içinde kalacak, çünkü widget'lar App'in özellikleri.
        # self.app.favorites_list_treeview.bind("<Double-1>", self.app.favorites_manager._on_favorite_double_click)
        # self.app.favorites_list_treeview.bind("<Button-3>", self.app.favorites_manager._show_favorites_context_menu)

        # Durum Çubuğu
        self.app.status_bar_frame = ttk.Frame(self.app, relief=tk.SUNKEN)
        self.app.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(2,0), padx=0)

        self.app.status_label = ttk.Label(self.app.status_bar_frame, text="Hazır.")
        self.app.status_label.pack(side=tk.LEFT, padx=(5,0), pady=2)

        # --- MP3 Kontrol Çerçevesi (Başlangıçta gizli) ---
        self.app.mp3_controls_frame = ttk.Frame(self.app.status_bar_frame)
        # mp3_controls_frame, status_label yerine pack edilecek, bu yüzden burada pack etmiyoruz.

        self.app.mp3_play_pause_button = ttk.Button(self.app.mp3_controls_frame,
                                                    image=self.app.play_button_icon, # Başlangıç ikonu
                                                    command=self.app.on_mp3_play_pause)
        self.app.mp3_play_pause_button.pack(side=tk.LEFT, padx=(0, 2))

        self.app.mp3_stop_button = ttk.Button(self.app.mp3_controls_frame,
                                              image=self.app.stop_button_icon,
                                              command=self.app.on_mp3_stop)
        self.app.mp3_stop_button.pack(side=tk.LEFT, padx=2)

        self.app.mp3_time_label = ttk.Label(self.app.mp3_controls_frame, text="00:00 / 00:00", width=12, anchor='w')
        self.app.mp3_time_label.pack(side=tk.LEFT, padx=(5,2))

        self.app.mp3_seek_scale = ttk.Scale(self.app.mp3_controls_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                            command=self.app.on_mp3_seek_user_initiated, length=200)
        self.app.mp3_seek_scale.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        # Kullanıcının scale'i sürükleyip bırakmasını yakalamak için
        self.app.mp3_seek_scale.bind("<ButtonPress-1>", self.app.on_mp3_seek_start)
        self.app.mp3_seek_scale.bind("<ButtonRelease-1>", self.app.on_mp3_seek_end)

        self.app.mp3_current_file_label = ttk.Label(self.app.mp3_controls_frame, text="", anchor='w', width=25)
        self.app.mp3_current_file_label.pack(side=tk.LEFT, padx=(5,0), fill=tk.X, expand=False)

        # --- Aktivite İlerleme Çubuğu ---
        self.app.activity_progressbar = ttk.Progressbar(self.app.status_bar_frame, orient=tk.HORIZONTAL, mode='indeterminate', length=200)
        # activity_progressbar her zaman sağda kalacak şekilde en son pack edilecek.
        self.app.activity_progressbar.pack(side=tk.RIGHT, padx=5, pady=2)

        self.app.long_operation_in_progress = False
        self.app._mp3_polling_active = False
        self.app._user_is_seeking_mp3 = False # Kullanıcı seek bar'ı aktif olarak kullanıyor mu?

    def _setup_menus(self):
        """Menü çubuğunu ve menüleri oluşturur."""
        self.app.menu_bar = tk.Menu(self.app)
        self.app.config(menu=self.app.menu_bar)

        file_menu = tk.Menu(self.app.menu_bar, tearoff=0)
        self.app.menu_bar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Dosya Ara...", command=self.app.search_manager.prompt_search, accelerator="Ctrl+D")
        file_menu.add_command(label="Kelime Ara...", command=self.app.search_manager.prompt_word_search, accelerator="Ctrl+F")
        file_menu.add_separator()
        file_menu.add_command(label="Klasör Seç...", command=self.app.file_browser.select_folder, accelerator="Ctrl+O") 
        file_menu.add_command(label="Güncelle", command=self._refresh_selected_folder, accelerator="F5")  # Yeni eklenen satır
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.app.on_closing, accelerator="Ctrl+Q")

        settings_menu = tk.Menu(self.app.menu_bar, tearoff=0)
        self.app.menu_bar.add_cascade(label="Ayarlar", menu=settings_menu)
        settings_menu.add_command(label="Pencere Ayarları...", command=self.app.open_window_settings_dialog, accelerator="Ctrl+P")

        view_menu = tk.Menu(self.app.menu_bar, tearoff=0)
        self.app.menu_bar.add_cascade(label="Görünüm", menu=view_menu)
        view_menu.add_command(label="Favoriler Panelini Göster/Gizle", command=self.app.favorites_manager._toggle_favorites_panel, accelerator="Ctrl+B")
        view_menu.add_command(label="Geçmiş İşlemler...", command=self.app.history_manager.show_history, accelerator="Ctrl+H")
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Temalar", menu=theme_menu)
        theme_menu.add_command(label="Tema Yönetimi...", command=self.app.theme_manager.manage_themes, accelerator="Ctrl+T")

        help_menu = tk.Menu(self.app.menu_bar, tearoff=0)
        self.app.menu_bar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Yardım", command=self.app.show_help, accelerator="F1")
        help_menu.add_command(label="Hakkında", command=self.app.show_about)

        self.app.bind('<F5>', lambda e: self._refresh_selected_folder())

    def _refresh_selected_folder(self):
        """Seçili olan klasörün içeriğini yeniden günceller."""
        # selected_item = self.app.dir_tree.focus()
        # if not selected_item:
        #     return
        # folder_path = self.app.dir_tree.item(selected_item, "values")

        folder_path = self.app.current_folder
        print(f"✨ Güncellenen klasör: {folder_path}")
        
        self.app.file_browser.populate_tree(self.app.current_folder) # Kendi içindeki populate_tree'yi çağırır
        # Yeni kök seçildiğinde dosya listesini temizle (file_list App'de olduğu için App üzerinden)
        for i in self.app.file_list.get_children():
            self.app.file_list.delete(i)

if __name__ == "__main__":
    print("##########################################################################################")
    print("   🔸  Bu dosya doğrudan çalıştırılamaz, Python Program Yöneticisi UIManager modülüdür.")
    print("##########################################################################################")



