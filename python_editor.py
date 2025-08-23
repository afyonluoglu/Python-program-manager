# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import jedi
import keyword
import builtins
import re
import os

class PythonEditor:
    """Python kod editörü penceresi."""
    
    def __init__(self, app_instance, file_path=None, read_only=False):
        self.app = app_instance
        self.file_path = file_path
        self.current_file_path = file_path
        self.is_modified = False
        self.read_only = read_only
        self.found_lines = []  # Bulunan satırların konumlarını takip etmek için liste        

        # Editör penceresi oluştur
        self.window = tk.Toplevel(self.app)
        self.window.title("Python Editörü")
        
        # Pencere geometrisi
        self.app.load_or_center_window("python_editor", self.window, 1000, 700)
        
        self.window.transient(self.app)
        self.window.focus_set()
        
        # Kapatma işleyicisi
        def on_closing():
            if self._check_unsaved_changes():
                geom = self.window.winfo_geometry()
                self.app.db.save_window_geometry("python_editor", geom)
                self.window.destroy()
        
        self.window.protocol("WM_DELETE_WINDOW", on_closing)
        self.window.bind("<Escape>", lambda e: on_closing())
        
        # Autocomplete listesi için
        self.autocomplete_window = None
        self.suggestions = []
        self.current_word = ""
        
        # Autocomplete için handler ID'leri
        self._autocomplete_key_handler_id = None
        self._autocomplete_click_handler_id = None
        
        self._setup_ui()
        self._setup_syntax_highlighting()
        self.setup_autocomplete()
        
        # Dosya varsa yükle
        if file_path and os.path.exists(file_path):
            self._load_file(file_path)
        
        # Klavye kısayolları
        self._bind_shortcuts()
    
    def _setup_ui(self):
        """Kullanıcı arayüzünü oluşturur."""
        # Ana frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çubuğu
        self._create_menu()
        
        # Araç çubuğu
        self._create_toolbar(main_frame)
        
        # Editör alanı
        self._create_editor_area(main_frame)
        
        # Durum çubuğu
        self._create_status_bar(main_frame)
    
    def _create_menu(self):
        """Menü çubuğunu oluşturur."""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # Dosya menüsü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Yeni", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Aç...", command=self._open_file, accelerator="Ctrl+O")
        if self.read_only != True:
            file_menu.add_command(label="Kaydet", command=self._save_file, accelerator="Ctrl+S")
            file_menu.add_command(label="Farklı Kaydet...", command=self._save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Çık", command=self.window.destroy)
        
        # Düzen menüsü
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Düzen", menu=edit_menu)
        edit_menu.add_command(label="Geri Al", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Yinele", command=self._redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Kes", command=self._cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Kopyala", command=self._copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Yapıştır", command=self._paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Tümünü Seç", command=self._select_all, accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="Bul...", command=self._find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Bul ve Değiştir...", command=self._find_replace, accelerator="Ctrl+H")
        edit_menu.add_separator()
        edit_menu.add_command(label="Bulunan satıra konumlan", command=self._goto_next_highlighted_line(), accelerator="F3")
        edit_menu.add_command(label="Bulunan satır renklerini kaldır", command=self._clear_all_highlighted_lines, accelerator="F4")


        # Çalıştır menüsü
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Çalıştır", menu=run_menu)
        run_menu.add_command(label="Çalıştır", command=self._run_python, accelerator="F5")
        
        # Görünüm menüsü
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        view_menu.add_command(label="Satır Numaralarını Göster/Gizle", command=self._toggle_line_numbers)
        view_menu.add_command(label="Yazı Tipi...", command=self._change_font)
    
    def _create_toolbar(self, parent):
        """Araç çubuğunu oluşturur."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # Dosya işlemleri
        ttk.Button(toolbar, text="📄 Yeni", command=self._new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Aç", command=self._open_file).pack(side=tk.LEFT, padx=2)
        if self.read_only != True:
            ttk.Button(toolbar, text="💾 Kaydet", command=self._save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Düzenleme işlemleri
        ttk.Button(toolbar, text="⏪ Geri", command=self._undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏩ İleri", command=self._redo).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Arama
        ttk.Button(toolbar, text="🔍 Bul", command=self._find).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Çalıştır
        ttk.Button(toolbar, text="▶️ Çalıştır", command=self._run_python).pack(side=tk.LEFT, padx=2)
    
    def _create_editor_area(self, parent):
        """Editör alanını oluşturur."""
        # Editor frame
        editor_frame = ttk.Frame(parent)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Frame for line numbers and text
        text_frame = tk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Satır numaraları için Text widget
        self.line_numbers = tk.Text(text_frame, width=4, padx=3, takefocus=0,
                                   border=0, state='disabled', wrap='none',
                                   font=('Consolas', 10))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Ana metin alanı
        self.text_area = tk.Text(text_frame, wrap=tk.NONE, undo=True, maxundo=50,
                                font=('Consolas', 10), insertbackground='black',
                                selectbackground='lightblue')

        # Scrollbar'lar
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._sync_scroll)
        self.text_area.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.text_area.xview)
        self.text_area.configure(xscrollcommand=h_scrollbar.set)

        # Read-only modunu ayarla
        if self.read_only:
            self.text_area.config(state='disabled')

        # Pack işlemleri
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Event bindings
        self.text_area.bind('<Key>', self._on_key_press)
        self.text_area.bind('<Button-1>', self._on_click)
        self.text_area.bind('<KeyRelease>', self._on_key_release)
        self.text_area.bind('<MouseWheel>', self._on_mousewheel)
        
        # Klavye navigasyon tuşları için event binding ekleyin
        self.text_area.bind('<Up>', self._on_navigate)
        self.text_area.bind('<Down>', self._on_navigate)
        self.text_area.bind('<Left>', self._on_navigate)
        self.text_area.bind('<Right>', self._on_navigate)
        self.text_area.bind('<Prior>', self._on_navigate)  # Page Up
        self.text_area.bind('<Next>', self._on_navigate)   # Page Down
        self.text_area.bind('<Home>', self._on_navigate)
        self.text_area.bind('<End>', self._on_navigate)
        self.text_area.bind('<Control-Home>', self._on_navigate)
        self.text_area.bind('<Control-End>', self._on_navigate)
                
        # İlk satır numaralarını göster
        self._update_line_numbers()
    
    def setup_autocomplete(self):
        """Otomatik tamamlama olaylarını ayarla"""
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<Button-1>', self.hide_autocomplete)
        self.text_area.bind('<FocusOut>', self.hide_autocomplete)
    
    def on_key_release(self, event):
        """Tuş bırakıldığında otomatik tamamlama kontrol et ve satır numaralarını güncelle"""
        # Önce satır numaralarını güncelle
        self._update_line_numbers()
        
        # Autocomplete kontrolü
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Tab']:
            self.hide_autocomplete()
            return
        
        # Ctrl+Space ile manuel tetikleme
        if event.state & 0x4 and event.keysym == 'space':
            self.show_autocomplete()
            return
        
        # Otomatik tetikleme
        current_pos = self.text_area.index(tk.INSERT)
        line_start = current_pos.split('.')[0] + '.0'
        current_line = self.text_area.get(line_start, current_pos)

        # Son kelimeyi bul
        words = re.findall(r'\b\w+$', current_line)
        if words and len(words[0]) >= 2:  # En az 2 karakter yazıldığında
            self.current_word = words[0]
            self.show_autocomplete()
        else:
            self.hide_autocomplete()
    
    def show_autocomplete(self):
        """Otomatik tamamlama penceresini göster"""
        try:
            # Mevcut metni al
            content = self.text_area.get('1.0', tk.END)
            cursor_pos = self.text_area.index(tk.INSERT)
            line_col = cursor_pos.split('.')
            line = int(line_col[0])
            col = int(line_col[1])
            
            # Jedi versiyonuna göre farklı yaklaşımlar
            try:
                # Yeni Jedi versiyonu (0.18+)
                script = jedi.Script(code=content, path="temp.py")
                completions = script.complete(line=line, column=col)
            except TypeError:
                try:
                    # Eski Jedi versiyonu
                    script = jedi.Script(source=content, line=line, column=col, path="temp.py")
                    completions = script.completions()
                except:
                    # En basit yaklaşım
                    completions = []
            
            # Python anahtar kelimeleri ekle
            keywords = [kw for kw in keyword.kwlist if kw.startswith(self.current_word)]
            
            # Built-in fonksiyonlar
            builtins = [name for name in dir(__builtins__) 
                       if not name.startswith('_') and name.startswith(self.current_word)]
            
            # Önerileri birleştir
            self.suggestions = []
            
            # Jedi önerileri
            for completion in completions[:8]:
                try:
                    self.suggestions.append({
                        'name': completion.name,
                        'type': getattr(completion, 'type', 'unknown'),
                        'description': getattr(completion, 'description', '')
                    })
                except:
                    self.suggestions.append({
                        'name': str(completion),
                        'type': 'completion',
                        'description': ''
                    })
            
            # Anahtar kelimeler
            for kw in keywords[:4]:
                self.suggestions.append({
                    'name': kw,
                    'type': 'keyword',
                    'description': 'Python keyword'
                })
            
            # Built-in fonksiyonlar
            for builtin in builtins[:4]:
                self.suggestions.append({
                    'name': builtin,
                    'type': 'builtin',
                    'description': 'Built-in function'
                })
            
            if self.suggestions:
                self.create_autocomplete_window()
            else:
                self.hide_autocomplete()
                
        except Exception as e:
            print(f"Autocomplete error: {e}")
            # Hata durumunda basit anahtar kelime önerileri
            self.fallback_suggestions()
    
    def fallback_suggestions(self):
        """Jedi hata verirse basit öneriler"""
        try:
            current_pos = self.text_area.index(tk.INSERT)
            line_start = current_pos.split('.')[0] + '.0'
            current_line = self.text_area.get(line_start, current_pos)
            
            words = re.findall(r'\b\w+$', current_line)
            if words:
                self.current_word = words[0]
                
                # Python anahtar kelimeleri
                keywords = [kw for kw in keyword.kwlist if kw.startswith(self.current_word)]
                
                # Built-in fonksiyonlar
                builtins = [name for name in dir(__builtins__) 
                           if not name.startswith('_') and name.startswith(self.current_word)]
                
                self.suggestions = []
                
                for kw in keywords[:6]:
                    self.suggestions.append({
                        'name': kw,
                        'type': 'keyword',
                        'description': 'Python keyword'
                    })
                
                for builtin in builtins[:6]:
                    self.suggestions.append({
                        'name': builtin,
                        'type': 'builtin',
                        'description': 'Built-in function'
                    })
                
                if self.suggestions:
                    self.create_autocomplete_window()
        except:
            pass
    
    def create_autocomplete_window_OLD(self):
        """Otomatik tamamlama penceresini oluştur"""
        self.hide_autocomplete()
        
        try:
            # Cursor pozisyonunu al
            cursor_pos = self.text_area.index(tk.INSERT)
            bbox = self.text_area.bbox(cursor_pos)

            if bbox:
                x, y, _, _ = bbox
                x += self.text_area.winfo_rootx()
                y += self.text_area.winfo_rooty() + 20
            else:
                # Fallback pozisyon
                x = self.text_area.winfo_rootx() + 50
                y = self.text_area.winfo_rooty() + 50

            # Pencere oluştur
            self.autocomplete_window = tk.Toplevel(self.app)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_window.geometry(f"+{x}+{y}")
            
            # Listbox oluştur
            listbox = tk.Listbox(
                self.autocomplete_window,
                height=min(8, len(self.suggestions)),
                width=35,
                font=('Consolas', 10),
                bg='white',
                selectbackground='darkblue',
                activestyle='dotbox'
            )
            listbox.pack()
            
            # Önerileri ekle
            for suggestion in self.suggestions:
                display_text = f"{suggestion['name']} ({suggestion['type']})"
                listbox.insert(tk.END, display_text)
            
            # İlk öğeyi seç
            if self.suggestions:
                listbox.selection_set(0)
                listbox.activate(0)
            
            # Olayları bağla
            listbox.bind('<Double-Button-1>', lambda e: self.insert_completion(listbox))
            listbox.bind('<Return>', lambda e: self.insert_completion(listbox))
            listbox.bind('<Escape>', lambda e: self.hide_autocomplete())
            
            # Ana pencereye focus geri ver
            self.text_area.focus_set()
            
        except Exception as e:
            print(f"Create autocomplete window error: {e}")
            self.hide_autocomplete()
    
    def create_autocomplete_window(self):
        """Otomatik tamamlama penceresini oluşturur ve olayları yönetir."""
        print("   # Create autocomplete window called")
        self.hide_autocomplete()
        
        try:
            cursor_pos = self.text_area.index(tk.INSERT)
            bbox = self.text_area.bbox(cursor_pos)
            if not bbox: return

            x, y, _, _ = bbox
            x += self.text_area.winfo_rootx()
            y += self.text_area.winfo_rooty() + 25

            self.autocomplete_window = tk.Toplevel(self.window)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_window.geometry(f"+{x}+{y}")

            # Pencereyi en üstte tut
            self.autocomplete_window.wm_attributes("-topmost", True)
        
            listbox = tk.Listbox(
                self.autocomplete_window,
                height=min(8, len(self.suggestions)),
                width=40,
                font=('Consolas', 10),
                bg='#F0F0F0',
                fg='black',
                selectbackground='#0078D7',
                selectforeground='white',
                exportselection=False,
                activestyle='none'
            )
            listbox.pack()

            for suggestion in self.suggestions:
                display_text = f"{suggestion['name']} ({suggestion['type']})"
                listbox.insert(tk.END, display_text)
            
            if self.suggestions:
                listbox.selection_set(0)
                listbox.activate(0)
            print(f"   # Autocomplete suggestions: {len(self.suggestions)}")

            # --- Olay Yöneticileri ---
            def on_selection(event):
                self.insert_completion(listbox)
                return "break"

            def on_escape(event):
                print("   # Escape pressed")
                self.hide_autocomplete()
                return "break"

            # Listbox'a özel olaylar
            listbox.bind('<Double-Button-1>', on_selection)
            listbox.bind('<Return>', on_selection)
            listbox.bind('<Escape>', on_escape)

            # Text_area'ya geçici olaylar (popup açıkken)
            def handle_global_keys(event):
                if event.keysym == 'Up':
                    current = listbox.curselection()
                    if current and current[0] > 0:
                        listbox.selection_clear(0, tk.END)
                        listbox.selection_set(current[0] - 1)
                        listbox.activate(current[0] - 1)
                        listbox.see(current[0] - 1)
                    return "break"
                elif event.keysym == 'Down':
                    current = listbox.curselection()
                    if current and current[0] < listbox.size() - 1:
                        listbox.selection_clear(0, tk.END)
                        listbox.selection_set(current[0] + 1)
                        listbox.activate(current[0] + 1)
                        listbox.see(current[0] + 1)
                    return "break"
                elif event.keysym in ['Return', 'Tab']:
                    on_selection(event)
                    return "break"
                elif event.keysym == 'Escape':
                    on_escape(event)
                    return "break"
            
            # Handler ID'lerini sakla
            self._autocomplete_key_handler_id = self.text_area.bind('<Key>', handle_global_keys, add='+')
            self._autocomplete_click_handler_id = self.text_area.bind('<Button-1>', self.hide_autocomplete, add='+')

            # Focus'u gecikmeli olarak ver
            # self.window.after(50, listbox.focus_set)

        except Exception as e:
            print(f"Create autocomplete window error: {e}")
            self.hide_autocomplete()

    def insert_completion(self, listbox):
        """Seçilen tamamlamayı ekle"""
        print("   # Insert completion called")
        try:
            selection = listbox.curselection()
            print(f"   # Selection: {selection}")
            if selection:
                print(f"   # Selected suggestion: {self.suggestions[selection[0]]}")
                selected = self.suggestions[selection[0]]
                
                # Mevcut kelimeyi bul ve değiştir
                current_pos = self.text_area.index(tk.INSERT)
                line_start = current_pos.split('.')[0] + '.0'
                current_line = self.text_area.get(line_start, current_pos)

                # Son kelimeyi bul
                match = re.search(r'\b\w+$', current_line)
                if match:
                    start_pos = f"{current_pos.split('.')[0]}.{match.start()}"
                    self.text_area.delete(start_pos, current_pos)
                
                # Yeni metni ekle
                self.text_area.insert(tk.INSERT, selected['name'])

        except Exception as e:
            print(f"Insert completion error: {e}")
        finally:
            self.hide_autocomplete()
    
    def hide_autocomplete_OLD(self, event=None):
        """Otomatik tamamlama penceresini gizle"""
        if self.autocomplete_window:
            try:
                self.autocomplete_window.destroy()
            except:
                pass
            self.autocomplete_window = None

    def hide_autocomplete(self, event=None):
        """Otomatik tamamlama penceresini gizle ve geçici binding'leri temizle."""
        # Geçici global binding'leri kaldır
        self.text_area.unbind('<Key>', self._autocomplete_key_handler_id)
        self.text_area.unbind('<Button-1>', self._autocomplete_click_handler_id)
        self._autocomplete_key_handler_id = None
        self._autocomplete_click_handler_id = None

        if self.autocomplete_window:
            try:
                self.autocomplete_window.destroy()
            except tk.TclError:
                pass  # Pencere zaten yoksa hata verme
            finally:
                self.autocomplete_window = None

    def _on_navigate(self, event):
        """Klavye navigasyon tuşlarıyla hareket edildiğinde görünümü günceller."""
        # İşlemi normal devam ettir
        self.window.after(10, self._sync_line_numbers)
        return None  # Event'i normal işlemeye devam et
        
    def _sync_line_numbers(self):
        """Satır numaraları görünümünü metin alanıyla senkronize eder."""
        # Görünümü senkronize et
        first_visible = self.text_area.yview()[0]

        self.line_numbers.config(state='normal')
        self.line_numbers.yview_moveto(first_visible)        
        self.line_numbers.config(state='disabled')


    def _create_status_bar(self, parent):
        """Durum çubuğunu oluşturur."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.status_label = ttk.Label(status_frame, text="Hazır")
        self.status_label.pack(side=tk.LEFT)
        
        # Satır:Sütun bilgisi
        self.position_label = ttk.Label(status_frame, text="Satır: 1, Sütun: 1")
        self.position_label.pack(side=tk.RIGHT)
    
    def _setup_syntax_highlighting(self):
        """Syntax highlighting ayarlarını yapar."""
        # arama için renklendirme tag'leri
        self.text_area.tag_configure('find_highlight_line', background="#27522b", foreground="#b7ffa5")

        # Renk tanımlamaları
        self.syntax_colors = {
            'keyword': '#0000FF',      # Mavi
            'builtin': '#800080',      # Mor
            'string': '#008000',       # Yeşil
            'comment': '#808080',      # Gri
            'number': '#FF8000',       # Turuncu
            'operator': '#000000',     # Siyah
            'function': '#0080FF',     # Açık mavi
            'class': '#8000FF'         # Açık mor
        }
        
        # Tag'leri yapılandır
        for tag, color in self.syntax_colors.items():
            self.text_area.tag_configure(tag, foreground=color)
        
        # Keyword listeleri
        self.keywords = set(keyword.kwlist)
        self.builtins = set(dir(builtins))
    
    def _sync_scroll(self, *args):
        """Satır numaraları ve ana metin alanının scrolling'ini senkronize eder."""
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)
        # print(f"   ☑️☑️ Syncing scroll: {args}")
    
    def _on_mousewheel(self, event):
        """Mouse wheel ile scrolling."""
        self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")
        self.text_area.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"
    
    def _on_key_press(self, event):
        """Tuş basma olayını işler."""
        self.is_modified = True
        self._update_title()
        
        # Otomatik girinti
        if event.keysym == 'Return':
            self._auto_indent()
        
        # Tab desteği (4 boşluk)
        elif event.keysym == 'Tab':
            self.text_area.insert(tk.INSERT, "    ")
            return "break"
    
    def _on_key_release(self, event):
        """Tuş bırakma olayını işler."""
        # self._update_line_numbers()
        self._update_cursor_position()
        self._syntax_highlight()
    
    def _on_click(self, event):
        """Mouse tıklama olayını işler."""
        self._update_cursor_position()
    
    def _auto_indent(self):
        """Otomatik girinti yapar."""
        current_line = self.text_area.get("insert linestart", "insert lineend")
        indent = ""
        for char in current_line:
            if char in " \t":
                indent += char
            else:
                break
        
        # Eğer satır : ile bitiyorsa ekstra girinti ekle
        if current_line.strip().endswith(":"):
            indent += "    "
        
        self.text_area.insert(tk.INSERT, "\n" + indent)
        return "break"
    
    def _update_line_numbers(self):
        """Satır numaralarını günceller."""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        # Toplam satır sayısını al
        line_count = int(self.text_area.index('end-1c').split('.')[0])
        
        # Satır numaralarını oluştur
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert('1.0', line_numbers_text)
        
        self.line_numbers.config(state='disabled')
    
    def _update_cursor_position(self):
        """İmleç konumunu günceller."""
        try:
            line, col = self.text_area.index(tk.INSERT).split('.')
            self.position_label.config(text=f"Satır: {line}, Sütun: {int(col) + 1}")
        except:
            pass
    
    def _syntax_highlight(self):
        """Syntax highlighting uygular."""
        # Mevcut tag'leri temizle
        for tag in self.syntax_colors.keys():
            self.text_area.tag_remove(tag, '1.0', tk.END)
        self.text_area.tag_remove('comment_bg', '1.0', tk.END)  

        content = self.text_area.get('1.0', tk.END)
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            start_pos = f"{line_num}.0"

            # Satır başı comment ise arkaplanı boya
            if line.lstrip().startswith('#'):
                self.text_area.tag_add('comment_bg', f"{line_num}.0", f"{line_num}.end")

            # String highlighting
            self._highlight_strings(line, line_num)
            
            # Comment highlighting
            comment_pos = line.find('#')
            if comment_pos != -1:
                start = f"{line_num}.{comment_pos}"
                end = f"{line_num}.{len(line)}"
                self.text_area.tag_add('comment', start, end)
            
            # Keyword ve builtin highlighting
            words = re.findall(r'\b\w+\b', line)
            for word in words:
                if word in self.keywords:
                    self._highlight_word(word, line, line_num, 'keyword')
                elif word in self.builtins:
                    self._highlight_word(word, line, line_num, 'builtin')
            
            # Number highlighting
            numbers = re.finditer(r'\b\d+\.?\d*\b', line)
            for match in numbers:
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                self.text_area.tag_add('number', start, end)
        
        # Tag'ın arkaplan rengini ayarla - Yorum satırı arkaplan rengi 
        self.text_area.tag_configure('comment_bg', background="#DDDDDD")  # Açık gri
    
    def _highlight_strings(self, line, line_num):
        """String'leri vurgular."""
        # Triple quotes
        triple_single = re.finditer(r"'''.*?'''", line, re.DOTALL)
        triple_double = re.finditer(r'""".*?"""', line, re.DOTALL)
        
        for match in triple_single:
            start = f"{line_num}.{match.start()}"
            end = f"{line_num}.{match.end()}"
            self.text_area.tag_add('string', start, end)
        
        for match in triple_double:
            start = f"{line_num}.{match.start()}"
            end = f"{line_num}.{match.end()}"
            self.text_area.tag_add('string', start, end)
        
        # Single quotes
        single_quotes = re.finditer(r"'([^'\\]|\\.)*'", line)
        double_quotes = re.finditer(r'"([^"\\]|\\.)*"', line)
        
        for match in single_quotes:
            start = f"{line_num}.{match.start()}"
            end = f"{line_num}.{match.end()}"
            self.text_area.tag_add('string', start, end)
        
        for match in double_quotes:
            start = f"{line_num}.{match.start()}"
            end = f"{line_num}.{match.end()}"
            self.text_area.tag_add('string', start, end)
    
    def _highlight_word(self, word, line, line_num, tag):
        """Belirli bir kelimeyi vurgular."""
        start = 0
        while True:
            pos = line.find(word, start)
            if pos == -1:
                break
            
            # Kelime sınırlarını kontrol et
            if (pos == 0 or not line[pos-1].isalnum()) and \
               (pos + len(word) == len(line) or not line[pos + len(word)].isalnum()):
                start_pos = f"{line_num}.{pos}"
                end_pos = f"{line_num}.{pos + len(word)}"
                self.text_area.tag_add(tag, start_pos, end_pos)
            
            start = pos + 1
    
    def _bind_shortcuts(self):
        """Klavye kısayollarını bağlar."""
        self.window.bind('<Control-n>', lambda e: self._new_file())
        self.window.bind('<Control-o>', lambda e: self._open_file())
        self.window.bind('<Control-s>', lambda e: self._save_file())
        self.window.bind('<Control-S>', lambda e: self._save_as_file())
        self.window.bind('<Control-z>', lambda e: self._undo())
        self.window.bind('<Control-y>', lambda e: self._redo())
        self.window.bind('<Control-x>', lambda e: self._cut())
        self.window.bind('<Control-c>', lambda e: self._copy())
        self.window.bind('<Control-v>', lambda e: self._paste())
        self.window.bind('<Control-a>', lambda e: self._select_all())
        self.window.bind('<Control-f>', lambda e: self._find())
        self.window.bind('<Control-h>', lambda e: self._find_replace())
        self.window.bind('<F5>', lambda e: self._run_python())
        self.window.bind('<F3>', lambda e: self._goto_next_highlighted_line())
        self.window.bind('<F4>', lambda e: self._clear_all_highlighted_lines())
        
    def _clear_all_highlighted_lines(self):
        """F4 ile tüm 'hepsini bul' renklendirmelerini kaldır."""
        self.text_area.tag_remove("find_highlight_line", "1.0", tk.END)
        self.found_lines.clear()
        self.highlighted_line_index = -1
        
    def _goto_next_highlighted_line(self):
        """F3 ile renklendirilmiş satırlar arasında gez."""
        # Eğer hiç satır yoksa veya arama yapılmadıysa bir şey yapma
        if not hasattr(self, 'highlighted_line_index'):
            self.highlighted_line_index = -1

        # found_lines güncel mi? (FindDialog tarafından dolduruluyor)
        if hasattr(self, 'found_lines') and self.found_lines:
            self.highlighted_line_index = (self.highlighted_line_index + 1) % len(self.found_lines)
            line_num = self.found_lines[self.highlighted_line_index]
            self.text_area.mark_set(tk.INSERT, f"{line_num}.0")
            self.text_area.see(f"{line_num}.0")
            # Satırı kısa süreliğine vurgula
            self.text_area.tag_remove("highlight_line", "1.0", tk.END)
            self.text_area.tag_add("highlight_line", f"{line_num}.0", f"{line_num}.end")
            self.text_area.tag_configure("highlight_line", background="darkblue", foreground="white")
            self.window.after(1000, lambda: self.text_area.tag_remove("highlight_line", "1.0", tk.END))
        else:
            # Hiçbir şey bulunamadıysa index sıfırla
            self.highlighted_line_index = -1

    def _new_file(self):
        """Yeni dosya oluşturur."""
        if self._check_unsaved_changes():
            self.text_area.delete('1.0', tk.END)
            self.current_file_path = None
            self.is_modified = False
            self._update_title()
            self._update_line_numbers()
    
    def _open_file(self):
        """Dosya açar."""
        if self._check_unsaved_changes():
            file_path = filedialog.askopenfilename(
                title="Python Dosyası Aç",
                filetypes=[("Python Dosyaları", "*.py"), ("Tüm Dosyalar", "*.*")],
                parent=self.window
            )
            if file_path:
                self._load_file(file_path)
    
    def _load_file(self, file_path):
        """Belirtilen dosyayı yükler."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Read-only modda ise geçici olarak normal moda al
            if self.read_only:
                self.text_area.config(state='normal')

            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', content)
            
            # Read-only modda ise tekrar disabled yap
            if self.read_only:
                self.text_area.config(state='disabled')
                            
            self.current_file_path = file_path
            self.is_modified = False
            self._update_title()
            self._update_line_numbers()
            self._syntax_highlight()
            
            self.status_label.config(text=f"Dosya yüklendi: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılırken hata oluştu:\n{e}", parent=self.window)
    
    def _save_file(self):
        """Dosyayı kaydeder."""
        if self.current_file_path:
            self._save_to_file(self.current_file_path)
        else:
            self._save_as_file()
    
    def _save_as_file(self):
        """Dosyayı farklı kaydet."""
        file_path = filedialog.asksaveasfilename(
            title="Dosyayı Kaydet",
            defaultextension=".py",
            filetypes=[("Python Dosyaları", "*.py"), ("Tüm Dosyalar", "*.*")],
            parent=self.window
        )
        if file_path:
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path):
        """Belirtilen yola dosyayı kaydeder."""
        try:
            content = self.text_area.get('1.0', 'end-1c')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            self.current_file_path = file_path
            self.is_modified = False
            self._update_title()
            
            self.status_label.config(text=f"Kaydedildi: {os.path.basename(file_path)}")
            
            # Ana uygulamadaki dosya listesini yenile
            # if hasattr(self.app, 'file_browser'):
            #     self.app.file_browser.refresh_file_list()
                
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilirken hata oluştu:\n{e}", parent=self.window)
    
    def _undo(self):
        """Geri al."""
        try:
            self.text_area.edit_undo()
            self._update_line_numbers()
            self._syntax_highlight()
        except tk.TclError:
            pass
    
    def _redo(self):
        """Yinele."""
        try:
            self.text_area.edit_redo()
            self._update_line_numbers()
            self._syntax_highlight()
        except tk.TclError:
            pass
    
    def _cut(self):
        """Kes."""
        try:
            self.text_area.event_generate("<<Cut>>")
            self._update_line_numbers()
            self._syntax_highlight()
        except tk.TclError:
            pass
    
    def _copy(self):
        """Kopyala."""
        try:
            self.text_area.event_generate("<<Copy>>")
        except tk.TclError:
            pass
    
    def _paste(self):
        """Yapıştır."""
        try:
            self.text_area.event_generate("<<Paste>>")
            self._update_line_numbers()
            self._syntax_highlight()
        except tk.TclError:
            pass
    
    def _select_all(self):
        """Tümünü seç."""
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
    
    def _find(self):
        """Metin arama penceresi açar."""
        FindDialog(self)
    
    def _find_replace(self):
        """Bul ve değiştir penceresi açar."""
        FindReplaceDialog(self)
    
    def open_file_at_line(self, file_path, line_number):
        """Dosyayı belirtilen satırda açar."""
        self._load_file(file_path)
        
        # Belirtilen satıra git
        self.text_area.mark_set(tk.INSERT, f"{line_number}.0")
        self.text_area.see(f"{line_number}.0")
        
        # Görünümü senkronize et
        first_visible = self.text_area.yview()[0]
        # self.line_numbers.yview_moveto(first_visible)
        self.line_numbers.config(state='normal')
        self.line_numbers.yview_moveto(first_visible)        
        self.line_numbers.config(state='disabled')

                
        # Satırı vurgula
        self.text_area.tag_remove("highlight_line", "1.0", tk.END)
        self.text_area.tag_add("highlight_line", f"{line_number}.0", f"{line_number}.end")
        self.text_area.tag_configure("highlight_line", background="yellow", foreground="black")
        print(f"   🚩 Line Number {line_number} highlighted in {file_path}")
           
        self.text_area.mark_set(tk.INSERT, f"{line_number}.0")  # İmleci satır başına alır
        self.text_area.see(f"{line_number}.0")                  # O satırı görünür yapar        
               
        # Vurgulamayı 60 saniye sonra kaldır
        self.window.after(60000, lambda: self.text_area.tag_remove("highlight_line", "1.0", tk.END))
        
        # Pencereyi öne getir
        self.window.lift()
        self.window.focus_force()

    def _run_python(self):
        """Python kodunu çalıştırır."""
        if self.is_modified and self.current_file_path and self.read_only != True:
            result = messagebox.askyesnocancel(
                "Kaydedilmemiş Değişiklikler",
                "Dosyada kaydedilmemiş değişiklikler var. Çalıştırmadan önce kaydetmek ister misiniz?",
                parent=self.window
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes
                self._save_file()
        
        if self.current_file_path:
            # Ana uygulamadaki çalıştırma fonksiyonunu kullan
            self.app.execution_manager.run_python_file(self.current_file_path, source="editor")
        else:
            messagebox.showwarning("Uyarı", "Dosyayı çalıştırmak için önce kaydetmeniz gerekir.", parent=self.window)
    
    def _toggle_line_numbers(self):
        """Satır numaralarını göster/gizle."""
        if self.line_numbers.winfo_viewable():
            self.line_numbers.pack_forget()
        else:
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y, before=self.text_area)
    
    def _change_font(self):
        """Yazı tipi değiştirme penceresi açar."""
        FontDialog(self)
    
    def _check_unsaved_changes(self):
        """Kaydedilmemiş değişiklikleri kontrol eder."""
        if self.is_modified  and self.read_only != True:
            result = messagebox.askyesnocancel(
                "Kaydedilmemiş Değişiklikler",
                "Dosyada kaydedilmemiş değişiklikler var. Kaydetmek ister misiniz?",
                parent=self.window
            )
            if result is None:  # Cancel
                return False
            elif result:  # Yes
                self._save_file()
                return not self.is_modified  # Kaydetme başarılıysa True
        return True
    
    def _update_title(self):
        """Pencere başlığını günceller."""
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            title = f"Python Editörü - {filename}"
        else:
            title = "Python Editörü - Yeni Dosya"
        
        if self.is_modified:
            title += " *"
        
        self.window.title(title)
    
    def find_text(self, search_term, case_sensitive=False, whole_word=False):
        """Metin arama fonksiyonu."""
        if not search_term:
            return None
        
        # Arama ayarları
        if not case_sensitive:
            search_term = search_term.lower()
        
        content = self.text_area.get('1.0', tk.END)
        if not case_sensitive:
            content = content.lower()
        
        # Mevcut cursor pozisyonundan başla
        start_pos = self.text_area.index(tk.INSERT)
        start_line, start_col = map(int, start_pos.split('.'))
        
        # Cursor'dan sonraki metni al
        search_content = content[self.text_area.count('1.0', start_pos, 'chars')[0]:]
        
        pos = search_content.find(search_term)
        if pos != -1:
            # Bulunan pozisyonu hesapla
            char_pos = self.text_area.count('1.0', start_pos, 'chars')[0] + pos
            line_pos = content[:char_pos].count('\n') + 1
            col_pos = char_pos - content[:char_pos].rfind('\n') - 1 if '\n' in content[:char_pos] else char_pos
            
            found_start = f"{line_pos}.{col_pos}"
            found_end = f"{line_pos}.{col_pos + len(search_term)}"
            
            # Metni seç ve göster
            self.text_area.tag_remove(tk.SEL, '1.0', tk.END)
            self.text_area.tag_add(tk.SEL, found_start, found_end)
            self.text_area.mark_set(tk.INSERT, found_end)
            self.text_area.see(found_start)
            
            # Highlight the entire line
            # self.text_area.tag_remove("find_highlight_line", "1.0", tk.END)
            self.text_area.tag_add("find_highlight_line", f"{line_pos}.0", f"{line_pos}.end")
            self._sync_line_numbers()

            return found_start
        else:
            # Baştan ara
            pos = content.find(search_term)
            if pos != -1:
                line_pos = content[:pos].count('\n') + 1
                col_pos = pos - content[:pos].rfind('\n') - 1 if '\n' in content[:pos] else pos
                
                found_start = f"{line_pos}.{col_pos}"
                found_end = f"{line_pos}.{col_pos + len(search_term)}"
                
                self.text_area.tag_remove(tk.SEL, '1.0', tk.END)
                self.text_area.tag_add(tk.SEL, found_start, found_end)
                self.text_area.mark_set(tk.INSERT, found_end)
                self.text_area.see(found_start)

                # Highlight the entire line
                # self.text_area.tag_remove("find_highlight_line", "1.0", tk.END)
                self.text_area.tag_add("find_highlight_line", f"{line_pos}.0", f"{line_pos}.end")
                self._sync_line_numbers()

                return found_start
        
        return None


class FindDialog:
    """Metin arama penceresi."""
    
    def __init__(self, editor):
        self.editor = editor
             
        self.window = tk.Toplevel(editor.window)
        self.window.title("Bul")
        self.window.geometry("600x400")
        self.window.transient(editor.window)
        self.window.grab_set()
        
        self._setup_ui()
        
        # ESC ile kapat
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.bind('<Return>', lambda e: self._find_next())

        # Pencere kapatma olayını yakala
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Pencere kapatıldığında renklendirmeyi kaldır."""
        for line in self.editor.found_lines:
            self.editor.text_area.tag_remove("find_highlight_line", f"{line}.0", f"{line}.end")
        self.editor.text_area.tag_remove("find_highlight_line", "1.0", tk.END)        
        self.window.destroy()        
    
    def _setup_ui(self):
        """Arayüzü oluştur."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Arama metni
        ttk.Label(main_frame, text="Aranacak Kelime:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.search_entry.focus()
        
        # Seçenekler
        self.case_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Büyük/küçük harf duyarlı", 
                       variable=self.case_var).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        self.find_all_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Hepsini Bul",
                        variable=self.find_all_var, command=self._find_all_highlight).grid(row=1, column=2, sticky=tk.W, pady=2)

        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky=tk.EW)
        
        ttk.Button(button_frame, text="Sonrakini Bul", command=self._find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)

        # Bulunan satırları listelemek için Listbox
        self.result_listbox = tk.Listbox(self.window)
        self.result_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Çift tıklama olayını bağla
        self.result_listbox.bind("<Double-1>", self._on_result_double_click)

    def _find_next_OLD(self):
        """Sonraki eşleşmeyi bul."""
        search_term = self.search_var.get()
        if search_term:
            found_start = self.editor.find_text(search_term, self.case_var.get())
            if found_start:
                line_num = int(found_start.split('.')[0])
                if line_num not in self.editor.found_lines:
                    line_content = self.editor.text_area.get(f"{line_num}.0", f"{line_num}.end")
                    
                    # Listeye ekle
                    self.result_listbox.insert(tk.END, f"Satır {line_num}: {line_content}")
                    self.editor.found_lines.append(line_num)
                    print(f"   FIND_NEXT Append: {line_num} - {line_content.strip()}")
            else:
                messagebox.showinfo("Sonuç", "Aranan metin bulunamadı.", parent=self.window)

    def _find_next(self):
        """Sonraki eşleşmeyi bul."""
        search_term = self.search_var.get()
        if search_term:
            # Hepsini Bul işaretli ise, tüm satırları renklendir
            if self.find_all_var.get():
                self._find_all_highlight()
                return
            found_start = self.editor.find_text(search_term, self.case_var.get())
            if found_start:
                line_num = int(found_start.split('.')[0])
                if line_num not in self.editor.found_lines:
                    line_content = self.editor.text_area.get(f"{line_num}.0", f"{line_num}.end")

                    # Listeye ekle
                    self.result_listbox.insert(tk.END, f"Satır {line_num}: {line_content}")
                    self.editor.found_lines.append(line_num)
                    print(f"   FIND_NEXT Append: {line_num} - {line_content.strip()}")
            else:
                messagebox.showinfo("Sonuç", "Aranan metin bulunamadı.", parent=self.window)

    def _find_all_highlight(self):
        """Tüm eşleşen satırları renklendir."""
        # Önce eski renklendirmeleri kaldır
        self.editor.text_area.tag_remove("find_highlight_line", "1.0", tk.END)
        self.result_listbox.delete(0, tk.END)
        self.editor.found_lines.clear()

        search_term = self.search_var.get()
        if not search_term:
            return

        content = self.editor.text_area.get('1.0', tk.END)
        lines = content.split('\n')
        case_sensitive = self.case_var.get()

        for i, line in enumerate(lines, 1):
            haystack = line if case_sensitive else line.lower()
            needle = search_term if case_sensitive else search_term.lower()
            if needle in haystack:
                self.editor.text_area.tag_add("find_highlight_line", f"{i}.0", f"{i}.end")
                self.result_listbox.insert(tk.END, f"Satır {i}: {line}")
                self.editor.found_lines.append(i)

        if not self.editor.found_lines:
            messagebox.showinfo("Sonuç", "Aranan metin bulunamadı.", parent=self.window)

    def _on_result_double_click(self, event):
        """Liste öğesine çift tıklanınca ilgili satıra git."""
        selection = self.result_listbox.curselection()
        if selection:
            index = selection[0]
            line_num = self.editor.found_lines[index]
            self.editor.text_area.mark_set(tk.INSERT, f"{line_num}.0")
            self.editor.text_area.see(f"{line_num}.0")

    def _on_result_double_click(self, event):
        """Liste öğesine çift tıklanınca ilgili satıra git."""
        selection = self.result_listbox.curselection()
        if selection:
            index = selection[0]
            line_num = self.editor.found_lines[index]
            # print(f" >>> {self.editor.found_lines}")
            # print(f"   🚩 List Selection: {selection} index: {index} Line number: {line_num}")
            
            # Editörde ilgili satıra git
            self.editor.text_area.mark_set(tk.INSERT, f"{line_num}.0")
            self.editor.text_area.see(f"{line_num}.0")

class FindReplaceDialog:
    """Bul ve değiştir penceresi."""
    
    def __init__(self, editor):
        self.editor = editor
        
        self.window = tk.Toplevel(editor.window)
        self.window.title("Bul ve Değiştir")
        self.window.geometry("450x200")
        self.window.transient(editor.window)
        self.window.grab_set()
        
        self._setup_ui()
        
        # ESC ile kapat
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def _setup_ui(self):
        """Arayüzü oluştur."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Arama metni
        ttk.Label(main_frame, text="Aranan:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.search_entry.focus()
        
        # Değiştirme metni
        ttk.Label(main_frame, text="Değiştirilecek:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.replace_var = tk.StringVar()
        self.replace_entry = ttk.Entry(main_frame, textvariable=self.replace_var, width=30)
        self.replace_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Seçenekler
        self.case_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Büyük/küçük harf duyarlı", 
                       variable=self.case_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=tk.EW)
        
        ttk.Button(button_frame, text="Bul", command=self._find_next).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Değiştir", command=self._replace).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Tümünü Değiştir", command=self._replace_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Kapat", command=self.window.destroy).pack(side=tk.RIGHT, padx=2)
        
        main_frame.columnconfigure(1, weight=1)
    
    def _find_next(self):
        """Sonraki eşleşmeyi bul."""
        search_term = self.search_var.get()
        if search_term:
            result = self.editor.find_text(search_term, self.case_var.get())
            if result is None:
                messagebox.showinfo("Sonuç", "Aranan metin bulunamadı.", parent=self.window)
    
    def _replace(self):
        """Seçili metni değiştir."""
        if self.editor.text_area.tag_ranges(tk.SEL):
            replace_text = self.replace_var.get()
            self.editor.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.editor.text_area.insert(tk.INSERT, replace_text)
            self.editor.is_modified = True
            self.editor._update_title()
            self.editor._syntax_highlight()
    
    def _replace_all(self):
        """Tüm eşleşmeleri değiştir."""
        search_term = self.search_var.get()
        replace_text = self.replace_var.get()
        
        if not search_term:
            return
        
        content = self.editor.text_area.get('1.0', tk.END)
        if not self.case_var.get():
            # Case insensitive replacement için regex kullan
            import re
            new_content = re.sub(re.escape(search_term), replace_text, content, flags=re.IGNORECASE)
        else:
            new_content = content.replace(search_term, replace_text)
        
        if new_content != content:
            self.editor.text_area.delete('1.0', tk.END)
            self.editor.text_area.insert('1.0', new_content)
            self.editor.is_modified = True
            self.editor._update_title()
            self.editor._update_line_numbers()
            self.editor._syntax_highlight()
            
            count = content.count(search_term) if self.case_var.get() else len(re.findall(re.escape(search_term), content, re.IGNORECASE))
            messagebox.showinfo("Sonuç", f"{count} eşleşme değiştirildi.", parent=self.window)
        else:
            messagebox.showinfo("Sonuç", "Değiştirilecek metin bulunamadı.", parent=self.window)


class FontDialog:
    """Yazı tipi seçim penceresi."""
    
    def __init__(self, editor):
        self.editor = editor
        
        self.window = tk.Toplevel(editor.window)
        self.window.title("Yazı Tipi")
        self.window.geometry("400x300")
        self.window.transient(editor.window)
        self.window.grab_set()
        
        self._setup_ui()
        
        # ESC ile kapat
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def _setup_ui(self):
        """Arayüzü oluştur."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Font ailesi
        ttk.Label(main_frame, text="Font:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.font_var = tk.StringVar()
        font_combo = ttk.Combobox(main_frame, textvariable=self.font_var, width=25)
        font_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Sistem fontlarını al
        font_families = list(font.families())
        font_families.sort()
        font_combo['values'] = font_families
        
        # Mevcut fontu seç
        current_font = self.editor.text_area.cget('font')
        if isinstance(current_font, tuple):
            self.font_var.set(current_font[0])
        else:
            self.font_var.set('Consolas')
        
        # Font boyutu
        ttk.Label(main_frame, text="Boyut:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.size_var = tk.StringVar()
        size_combo = ttk.Combobox(main_frame, textvariable=self.size_var, width=10)
        size_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        size_combo['values'] = sizes
        
        # Mevcut boyutu seç
        if isinstance(current_font, tuple) and len(current_font) > 1:
            self.size_var.set(str(current_font[1]))
        else:
            self.size_var.set('10')
        
        # Önizleme
        preview_frame = ttk.LabelFrame(main_frame, text="Önizleme", padding=10)
        preview_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.EW+tk.N)
        
        self.preview_label = ttk.Label(preview_frame, text="Python kod editörü örnek metin 123")
        self.preview_label.pack()
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=tk.EW)
        
        ttk.Button(button_frame, text="Önizleme", command=self._preview_font).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tamam", command=self._apply_font).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="İptal", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # İlk önizleme
        self._preview_font()
    
    def _preview_font(self):
        """Font önizlemesi göster."""
        try:
            font_name = self.font_var.get()
            font_size = int(self.size_var.get())
            
            preview_font = (font_name, font_size)
            self.preview_label.config(font=preview_font)
        except:
            pass
    
    def _apply_font(self):
        """Seçilen fontu uygula."""
        try:
            font_name = self.font_var.get()
            font_size = int(self.size_var.get())
            
            new_font = (font_name, font_size)
            self.editor.text_area.config(font=new_font)
            self.editor.line_numbers.config(font=new_font)
            
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Font ayarlanırken hata oluştu:\n{e}", parent=self.window)

