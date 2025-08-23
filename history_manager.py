# -*- coding: utf-8 -*-

from collections import Counter
import tkinter as tk
from tkinter import ttk
import json # For loading/saving column widths
import datetime

class HistoryManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.stats_window_open = False # İstatistik penceresinin zaten açık olup olmadığını takip etmek için

    def show_history(self):
        """Çalıştırma geçmişini yeni bir pencerede gösterir."""
        self.window = history_window = tk.Toplevel(self.app)
        history_window.title("Geçmiş İşlemler")
        history_window.geometry("900x550") 
        history_window.transient(self.app)

        self.app.load_or_center_window("history", history_window, 1200, 550)

        main_frame = ttk.Frame(history_window, padding="10 10 10 10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        filter_controls_frame = ttk.Frame(main_frame)
        filter_controls_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        run_filter_var = tk.BooleanVar(value=True)
        compress_filter_var = tk.BooleanVar(value=True)
        zip_extraction_filter_var = tk.BooleanVar(value=True)
        search_filter_var = tk.BooleanVar(value=True)
        rename_filter_var = tk.BooleanVar(value=True)
        open_default_filter_var = tk.BooleanVar(value=True)
        play_mp3_filter_var = tk.BooleanVar(value=True)
        method_analysis_filter_var = tk.BooleanVar(value=True)  
        python_editor_filter_var = tk.BooleanVar(value=True)   

        # Tarih aralığı filtresi
        start_date_var = tk.StringVar()
        end_date_var = tk.StringVar()
        option_var = tk.StringVar(value="Bugün")

        def update_date_range(*args):
            today = datetime.date.today()
            opt = option_var.get()
            if opt == "Bugün":
                start = today
                end = today
            elif opt == "Dün":
                start = today - datetime.timedelta(days=1)
                end = start
            elif opt == "Son Hafta":
                start = today - datetime.timedelta(days=6)
                end = today
            elif opt == "Son Ay":
                start = today - datetime.timedelta(days=30)
                end = today
            elif opt == "Son 3 Ay":
                start = today - datetime.timedelta(days=90)
                end = today
            elif opt == "Son 6 Ay":
                start = today - datetime.timedelta(days=180)
                end = today
            else:  # Hepsi
                start_date_var.set("")
                end_date_var.set("")
                update_history_filter()
                return
            start_date_var.set(start.strftime("%Y-%m-%d"))
            end_date_var.set(end.strftime("%Y-%m-%d"))
            update_history_filter()

        ttk.Label(filter_controls_frame, text="Tarih Aralığı:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(filter_controls_frame, textvariable=option_var, values=["Bugün", "Dün", "Son Hafta", "Son Ay", "Son 3 Ay", "Son 6 Ay", "Hepsi"], state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_controls_frame, textvariable=start_date_var, width=12).pack(side=tk.LEFT)
        ttk.Label(filter_controls_frame, text=" - ").pack(side=tk.LEFT)
        ttk.Entry(filter_controls_frame, textvariable=end_date_var, width=12).pack(side=tk.LEFT)

        all_history_data = self.app.db.get_history() 

        tree = None # Define tree here to be accessible in populate_history_tree

        def populate_history_tree(data_to_populate):
            """Verilen verilerle geçmiş ağacını doldurur."""
            if tree is None: return # Should not happen if called after tree creation

            event_type_tags = {
                "search_initiated": "history_search", 
                "word_search_initiated": "history_search",
                "run_normal": "history_run_normal", 
                "compress": "history_compress", 
                "zip_extraction": "history_zip_extract",
                "run_search": "history_run_search", 
                "rename": "history_rename", 
                "open_default": "history_open_default",
                "play_mp3": "history_play_mp3",
                "method_analysis": "history_method_analysis",
                "python_editor": "history_python_editor", 
                "unknown": "history_unknown"
            }

            if data_to_populate:
                for timestamp, path, event_type in data_to_populate:
                    tag_to_apply = event_type_tags.get(event_type, "history_unknown")
                    tree.insert("", tk.END, values=(timestamp, path), tags=(tag_to_apply,))
            else:
                tree.insert("", tk.END, values=("", "Gösterilecek geçmiş kaydı bulunamadı veya filtreye uyan kayıt yok."))
            self.window.title(f"🔍 Geçmiş listesi:  Toplam {len(data_to_populate)}  kayıt")
            # print(f"🔍 Geçmiş listesi: Toplam {len(data_to_populate)} Listelenen: {displayCount} kayıt")

        def update_history_filter():
            """Checkbox durumlarına göre geçmiş listesini filtreler ve günceller."""
            if tree is None: return # Should not happen
            tree.delete(*tree.get_children()) 

            show_run = run_filter_var.get()
            show_compress = compress_filter_var.get()
            show_zip_extraction = zip_extraction_filter_var.get()
            show_search = search_filter_var.get()
            show_rename = rename_filter_var.get()
            show_open_default = open_default_filter_var.get() 
            show_play_mp3 = play_mp3_filter_var.get()
            show_method_analysis = method_analysis_filter_var.get()
            show_python_editor = python_editor_filter_var.get()    
            
            filtered_data = []
            for timestamp, path, event_type in all_history_data:
                # Tarih filtresi
                sd = start_date_var.get()
                ed = end_date_var.get()
                if sd and ed:
                    try:
                        ts_date = datetime.datetime.strptime(timestamp.split()[0], "%Y-%m-%d").date()
                        start = datetime.datetime.strptime(sd, "%Y-%m-%d").date()
                        end = datetime.datetime.strptime(ed, "%Y-%m-%d").date()
                        if not (start <= ts_date <= end):
                            continue
                    except:
                        pass
                if show_run and event_type in ("run_normal", "run_search"):
                    filtered_data.append((timestamp, path, event_type))
                elif show_compress and event_type == "compress":
                    filtered_data.append((timestamp, path, event_type))
                elif show_zip_extraction and event_type == "zip_extraction":
                    filtered_data.append((timestamp, path, event_type))
                elif show_search and event_type in ("search_initiated", "word_search_initiated"):
                    filtered_data.append((timestamp, path, event_type))
                elif show_rename and event_type == "rename":
                    filtered_data.append((timestamp, path, event_type))
                elif show_open_default and event_type == "open_default": 
                    filtered_data.append((timestamp, path, event_type))
                elif show_play_mp3 and event_type == "play_mp3": 
                    filtered_data.append((timestamp, path, event_type))
                elif show_method_analysis and event_type == "method_analysis":
                    filtered_data.append((timestamp, path, event_type))
                elif show_python_editor and event_type == "python_editor":  
                    filtered_data.append((timestamp, path, event_type))
            
            populate_history_tree(filtered_data)

        ttk.Checkbutton(filter_controls_frame, text="Çalıştırma", variable=run_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Sıkıştırma", variable=compress_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Extract", variable=zip_extraction_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Arama", variable=search_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Yeniden Adlandırma", variable=rename_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Varsayılanla Aç", variable=open_default_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="MP3 Çalma", variable=play_mp3_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Analizler", variable=method_analysis_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_controls_frame, text="Python Editör", variable=python_editor_filter_var, command=update_history_filter).pack(side=tk.LEFT, padx=5)  

        stats_button = ttk.Button(filter_controls_frame, text="İstatistikler",
                                  command=lambda: self._show_history_statistics(
                                      all_history_data,
                                      run_filter_var.get(),
                                      compress_filter_var.get(),
                                      zip_extraction_filter_var.get(),
                                      search_filter_var.get(),
                                      rename_filter_var.get(),
                                      open_default_filter_var.get(),
                                      play_mp3_filter_var.get(),
                                      method_analysis_filter_var.get(),
                                      python_editor_filter_var.get()  
                                  ))
        stats_button.pack(side=tk.LEFT, padx=10)

        def close_history():
            geom = history_window.winfo_geometry()
            self.app.db.save_window_geometry("history", geom)
            if tree: # Ensure tree exists before accessing columns
                try:
                    history_col_widths = {
                        "Tarih/Saat": tree.column("Tarih/Saat", "width"),
                        "Dosya Yolu": tree.column("Dosya Yolu", "width")
                    }
                    self.app.db.set_setting("history_list_column_widths", json.dumps(history_col_widths))
                except Exception as e:
                    print(f"❗ HATA: Geçmiş listesi sütun genişlikleri kaydedilemedi: {e}")
            history_window.destroy()

        history_window.grab_set()      
        history_window.focus_set()     
        history_window.protocol("WM_DELETE_WINDOW", close_history) # Ensure close_history is defined

        frame = ttk.Frame(main_frame)
        frame.pack(expand=True, fill=tk.BOTH)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        cols = ("Tarih/Saat", "Dosya Yolu")
        tree = ttk.Treeview(frame, columns=cols, show="headings") # Assign to the outer scope 'tree'
        tree.heading("Tarih/Saat", text="Tarih/Saat", anchor='w')
        tree.heading("Dosya Yolu", text="Dosya Yolu", anchor='w')
        tree.column("Tarih/Saat", width=180, stretch=tk.NO) 
        tree.column("Dosya Yolu", width=500) 

        saved_history_widths_json = self.app.db.get_setting("history_list_column_widths")
        if saved_history_widths_json:
            try:
                saved_history_widths = json.loads(saved_history_widths_json)
                if isinstance(saved_history_widths, dict):
                    for col_id, width_val in saved_history_widths.items():
                        if col_id in ("Tarih/Saat", "Dosya Yolu"):
                            try: tree.column(col_id, width=int(width_val))
                            except (ValueError, tk.TclError) as e_col: print(f"❗ HATA: Geçmiş '{col_id}' sütun genişliği ({width_val}) uygulanamadı: {e_col}")
            except json.JSONDecodeError as e: print(f"❗ HATA: Kayıtlı geçmiş sütun genişlikleri okunamadı (JSON): {e}")

        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.grid(row=1, column=0, sticky='ew')

        # Tarih güncelleme bağlantısını artık filtre fonksiyonu tanımlandıktan sonra yapıyoruz
        option_var.trace_add("write", update_date_range)
        # Başlangıçta tarihi güncelle
        update_date_range()

        # History satırlarının, statüsüne göre font renkleri
        tree.tag_configure("history_compress", foreground="red")
        tree.tag_configure("history_search_initiated", foreground="green")
        tree.tag_configure("history_run_search", foreground="black")
        tree.tag_configure("history_run_normal", foreground="blue")
        tree.tag_configure("history_rename", foreground="purple") 
        tree.tag_configure("history_search", foreground="green") 
        tree.tag_configure("history_zip_extract", foreground="black") 
        tree.tag_configure("history_open_default", foreground="brown") 
        tree.tag_configure("history_play_mp3", foreground="orange") 
        tree.tag_configure("history_method_analysis", foreground="darkgreen") # analiz işlemleri rengi
        tree.tag_configure("history_python_editor", foreground="navy")  # Python editörü rengi
        tree.tag_configure("history_unknown", foreground="gray") 

        update_history_filter()

        close_button = ttk.Button(main_frame, text="Kapat", command=close_history)
        close_button.pack(pady=(10, 0)) 
        history_window.bind("<Escape>", lambda e: close_history())
        self.app.wait_window(history_window)

    def _on_stats_closing(self, window_obj, window_key, tree_widget=None, tree_col_setting_key=None):
        """İstatistik penceresi kapatılırken geometri ve sütun genişliklerini kaydeder."""
        geom = window_obj.winfo_geometry()
        self.app.db.save_window_geometry(window_key, geom)
        if tree_widget and tree_col_setting_key:
            try:
                col_widths = {
                    "program": tree_widget.column("program", "width"),
                    "count": tree_widget.column("count", "width")
                }
                self.app.db.set_setting(tree_col_setting_key, json.dumps(col_widths))
            except Exception as e:
                print(f"❗ HATA: İstatistik penceresi '{tree_col_setting_key}' sütun genişlikleri kaydedilemedi: {e}")
        window_obj.destroy()
        self.stats_window_open = False

    def _show_history_statistics(self, history_data, show_run, show_compress, show_zip_extraction, show_search, show_rename, show_open_default, show_play_mp3, show_analysis, show_python_editor):  
        """Geçmiş işlem istatistiklerini gösteren bir pencere açar."""
        if self.stats_window_open:
            # TODO: Mevcut istatistik penceresini öne getirebilir veya kullanıcıyı bilgilendirebiliriz.
            # Şimdilik, zaten açıksa yenisini açmayı engelliyoruz.
            # print("İstatistik penceresi zaten açık.")
            return
    
        print("🔎 Geçmiş istatistikleri gösteriliyor...")
        self.stats_window_open = True
        stats_window_key = "history_stats"
        stats_window = tk.Toplevel(self.app)
        stats_window.title("Geçmiş İstatistikleri")
        self.app.load_or_center_window(stats_window_key, stats_window, 550, 450)
        stats_window.transient(self.app) # Ana pencereye bağlı
        stats_window.grab_set()
        stats_window.focus_set()

        main_stats_frame = ttk.Frame(stats_window, padding="10")
        main_stats_frame.pack(expand=True, fill=tk.BOTH)

        # Veri İşleme
        group_counts = {"run": 0, "compress": 0, "zip_extraction": 0, "search": 0, "rename": 0, "open_default": 0, "play_mp3": 0, "analysis":0, "python_editor": 0}  # Add python_editor
        program_execution_paths = []

        for _timestamp, path, event_type in history_data:
            if event_type in ("run_normal", "run_search"):
                if show_run: # Sadece checkbox işaretliyse say
                    group_counts["run"] += 1
                program_execution_paths.append(path) # Program listesi için her zaman ekle
            elif event_type == "compress" and show_compress:
                group_counts["compress"] += 1
            elif event_type == "zip_extraction" and show_zip_extraction:
                group_counts["zip_extraction"] += 1
            elif event_type in ("search_initiated", "word_search_initiated") and show_search:
                group_counts["search"] += 1
            elif event_type == "rename" and show_rename:
                group_counts["rename"] += 1
            elif event_type == "open_default" and show_open_default: # open_default sayımı
                group_counts["open_default"] += 1
            elif event_type == "play_mp3" and show_play_mp3:
                group_counts["play_mp3"] += 1
            elif event_type == "method_analysis" and show_analysis:
                group_counts["analysis"] += 1
            elif event_type == "python_editor" and show_python_editor:  # Add this condition
                group_counts["python_editor"] += 1

        program_execution_counts = Counter(program_execution_paths)
        sorted_program_executions = program_execution_counts.most_common()

        # Grup Sayılarını Gösterme
        group_counts_frame = ttk.LabelFrame(main_stats_frame, text="Seçili İşlem Grubu Sayıları", padding="10")
        group_counts_frame.pack(pady=10, fill="x")

        if show_run:
            ttk.Label(group_counts_frame, text=f"Çalıştırma İşlemleri: {group_counts['run']}").pack(anchor='w')
        if show_compress:
            ttk.Label(group_counts_frame, text=f"Sıkıştırma İşlemleri: {group_counts['compress']}").pack(anchor='w')
        if show_zip_extraction:
            ttk.Label(group_counts_frame, text=f"ZIP Çıkartma İşlemleri: {group_counts['zip_extraction']}").pack(anchor='w')        
        if show_search:
            ttk.Label(group_counts_frame, text=f"Arama İşlemleri: {group_counts['search']}").pack(anchor='w')
        if show_rename:
            ttk.Label(group_counts_frame, text=f"Yeniden Adlandırma İşlemleri: {group_counts['rename']}").pack(anchor='w')
        if show_open_default: 
            ttk.Label(group_counts_frame, text=f"Varsayılanla Açma İşlemleri: {group_counts['open_default']}").pack(anchor='w')
        if show_play_mp3:
            ttk.Label(group_counts_frame, text=f"MP3 Çalma İşlemleri: {group_counts['play_mp3']}").pack(anchor='w')
        if show_analysis:
            ttk.Label(group_counts_frame, text=f"Analiz İşlemleri: {group_counts['analysis']}").pack(anchor='w')
        if show_python_editor:  
            ttk.Label(group_counts_frame, text=f"Python Editör İşlemleri: {group_counts['python_editor']}").pack(anchor='w')
        
        if not (show_run or show_compress or show_search or show_rename or show_open_default or show_play_mp3):
            ttk.Label(group_counts_frame, text="İstatistik göstermek için en az bir işlem grubu seçin.").pack(anchor='w')

        # Program Çalıştırma Sayılarını Gösterme
        program_exec_frame = ttk.LabelFrame(main_stats_frame, text="Program Çalıştırma Sayıları (Çoktan Aza)", padding="10")
        program_exec_frame.pack(pady=10, fill="both", expand=True)
        program_exec_frame.rowconfigure(0, weight=1)
        program_exec_frame.columnconfigure(0, weight=1)

        program_tree_cols = ("program", "count")
        program_tree = ttk.Treeview(program_exec_frame, columns=program_tree_cols, show="headings")
        program_tree.heading("program", text="Program Yolu")
        program_tree.heading("count", text="Çalıştırma Sayısı")

        tree_col_widths_key = "history_stats_program_tree_cols"
        saved_col_widths_json = self.app.db.get_setting(tree_col_widths_key)
        if saved_col_widths_json:
            try:
                saved_widths = json.loads(saved_col_widths_json)
                if isinstance(saved_widths, dict):
                    program_tree.column("program", width=int(saved_widths.get("program", 350)))
                    program_tree.column("count", width=int(saved_widths.get("count", 100)), anchor='center')
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❗ HATA: İstatistik program ağacı sütun genişlikleri yüklenemedi: {e}")
                program_tree.column("program", width=350)
                program_tree.column("count", width=100, anchor='center')
        else:
            program_tree.column("program", width=350)
            program_tree.column("count", width=100, anchor='center')

        for prog_path, count in sorted_program_executions:
            program_tree.insert("", tk.END, values=(prog_path, count))

        program_tree.grid(row=0, column=0, sticky="nsew")
        pt_scrollbar_y = ttk.Scrollbar(program_exec_frame, orient=tk.VERTICAL, command=program_tree.yview)
        program_tree.configure(yscrollcommand=pt_scrollbar_y.set)
        pt_scrollbar_y.grid(row=0, column=1, sticky="ns")

        stats_window.protocol("WM_DELETE_WINDOW", lambda: self._on_stats_closing(stats_window, stats_window_key, program_tree, tree_col_widths_key))
        stats_window.bind("<Escape>", lambda e: self._on_stats_closing(stats_window, stats_window_key, program_tree, tree_col_widths_key))

        close_button = ttk.Button(main_stats_frame, text="Kapat", command=lambda: self._on_stats_closing(stats_window, stats_window_key, program_tree, tree_col_widths_key))
        close_button.pack(pady=10)

        self.app.wait_window(stats_window)