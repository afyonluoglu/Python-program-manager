import ast
import os
import tkinter as tk
from tkinter import ttk
import json
from collections import defaultdict
import glob
from python_editor import PythonEditor  

class MethodAnalyzer:
    def __init__(self, app_instance):
        self.app = app_instance
        self.methods_by_name = defaultdict(list)
        self.method_calls = set()
        self.all_methods = []
        self.unused_methods = []
        self.method_occurrences = defaultdict(set)
        self.project_files = []
        self.analyzed_files = set()
        
        # Analiz dışında bırakılacak metodlar
        self.excluded_methods = {
            # Python built-in magic methods
            '__init__', '__del__', '__new__', '__str__', '__repr__',
            '__len__', '__getitem__', '__setitem__', '__delitem__',
            '__iter__', '__next__', '__enter__', '__exit__',
            '__call__', '__bool__', '__eq__', '__ne__', '__lt__',
            '__le__', '__gt__', '__ge__', '__hash__', '__contains__',
            '__add__', '__sub__', '__mul__', '__div__', '__truediv__',
            '__floordiv__', '__mod__', '__pow__', '__and__', '__or__',
            '__xor__', '__lshift__', '__rshift__', '__neg__', '__pos__',
            '__abs__', '__invert__', '__getattr__', '__setattr__',
            '__delattr__', '__getattribute__', '__dict__', '__class__',
            
            # GUI event handlers (Tkinter)
            'on_closing', 'on_double_click', 'on_click', 'on_select',
            'on_focus', 'on_key_press', 'on_key_release', 'on_mouse_enter',
            'on_mouse_leave', 'on_resize', 'on_configure', 'on_destroy',
            'on_activate', 'on_deactivate', 'on_map', 'on_unmap',
            'on_visibility', 'on_expose', 'on_button_press',
            'on_button_release', 'on_motion', 'on_enter', 'on_leave',
            
            # Common callback patterns
            'callback', 'on_callback', 'handle_callback', 'event_handler',
            'button_callback', 'menu_callback', 'timer_callback',
            
            # GUI widget event methods
            'on_paint', 'on_draw', 'on_update', 'on_refresh',
            'on_show', 'on_hide', 'on_minimize', 'on_maximize',
            'on_restore', 'on_move', 'on_size_changed',
            
            # Common override methods
            'setup', 'teardown', 'cleanup', 'initialize', 'finalize',
            'validate', 'process', 'handle', 'execute', 'run',
            
            # Test methods
            'setUp', 'tearDown', 'test_', 'setUpClass', 'tearDownClass',
            
            # Django/Flask common methods
            'get', 'post', 'put', 'delete', 'patch', 'head', 'options',
            'dispatch', 'get_context_data', 'get_queryset', 'form_valid',
            'form_invalid', 'get_object', 'get_success_url',
            
            # Common property methods
            'getter', 'setter', 'deleter',
        }
    
    def _is_excluded_method(self, method_name, method_info=None):
        """Metodun analiz dışında bırakılıp bırakılmayacağını kontrol eder."""
        # Exact match kontrolü
        if method_name in self.excluded_methods:
            return True
        
        # Pattern-based exclusions
        patterns_to_exclude = [
            '__.*__',  # Magic methods
            'test_.*',  # Test methods
            'on_.*',   # Event handlers
            'handle_.*',  # Event handlers
            '_.*_callback',  # Callback methods
            'callback_.*',   # Callback methods
        ]
        
        import re
        for pattern in patterns_to_exclude:
            if re.match(pattern, method_name):
                return True
        
        # Class method'ları kontrol et (eğer method_info verilmişse)
        if method_info and method_info.get('class'):
            class_name = method_info['class']
            
            # GUI class'larında common method'lar
            gui_class_patterns = [
                '.*App.*', '.*Window.*', '.*Dialog.*', '.*Frame.*', 
                '.*Panel.*', '.*Widget.*', '.*Button.*', '.*Menu.*'
            ]
            
            for pattern in gui_class_patterns:
                if re.match(pattern, class_name, re.IGNORECASE):
                    # GUI class'larında yaygın olan method'ları exclude et
                    if method_name in ['close', 'show', 'hide', 'update', 'refresh', 
                                     'resize', 'move', 'focus', 'blur', 'enable', 
                                     'disable', 'bind', 'unbind', 'pack', 'grid',
                                     'place', 'destroy', 'quit', 'mainloop']:
                        return True
        
        return False
    
    def analyze_file(self, file_path):
        """Belirtilen Python dosyasını ve import zincirini analiz eder."""
        try:
            # Önce tüm verileri temizle
            self._reset_analysis_data()
            
            print(f"🔍 Analiz başlıyor: {os.path.basename(file_path)}")
            
            # Ana dosyayı analiz et
            self._analyze_single_file(file_path)
            self.analyzed_files.add(file_path)

            print(f"   DEBUG: analyzed files: {self.analyzed_files}")
            
            # Import zincirini recursive olarak bul
            print(f"📁 Import zinciri takip ediliyor...")
            imported_files = self._find_local_imports(file_path)
            
            print(f"🔍 Toplam {len(imported_files)} import dosyası bulundu:")
            for index, imported_file in enumerate(imported_files, start=1):
                print(f"     {index}. {os.path.relpath(imported_file, os.path.dirname(file_path))}")
            
            # Import edilen dosyaları analiz et
            for imported_file in imported_files:
                if imported_file not in self.analyzed_files and os.path.exists(imported_file):
                    self._analyze_single_file(imported_file)
                    self.analyzed_files.add(imported_file)
        
            # Analiz edilen dosyaları project_files listesine ekle
            self.project_files = list(self.analyzed_files)
            
            print(f"✅ Toplam {len(self.analyzed_files)} dosya analiz edildi")
            print(f"📊 Toplam {len(self.all_methods)} metod bulundu")
            
            # Kullanılmayan metodları tespit et
            self._find_unused_methods()
            
            # Analiz edilen dosyalarda metod geçişlerini ara
            self._search_method_occurrences_in_analyzed_files()
            
        except Exception as e:
            print(f"❗ HATA: Dosya analizi sırasında hata: {e}")
    
    def _reset_analysis_data(self):
        """Analiz verilerini sıfırla."""
        self.methods_by_name = defaultdict(list)
        self.method_calls = set()
        self.all_methods = []
        self.unused_methods = []
        self.method_occurrences = defaultdict(set)
        self.analyzed_files = set()
    
    def _find_project_python_files(self, project_dir):
        """Proje klasöründeki tüm Python dosyalarını bulur."""
        self.project_files = []
        
        # Recursive olarak tüm .py dosyalarını bul
        for root, dirs, files in os.walk(project_dir):
            # __pycache__ klasörlerini atla
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    self.project_files.append(full_path)
        
        print(f"🔍 Toplam {len(self.project_files)} Python dosyası bulundu")
    
    def _analyze_single_file(self, file_path):
        """Tek bir Python dosyasını analiz eder."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            visitor = MethodVisitor(file_path)
            visitor.visit(tree)
            
            # Metodları topla (excluded olanları filtrele)
            for method_info in visitor.methods:
                method_name = method_info['name']
                
                # Excluded method kontrolü
                if not self._is_excluded_method(method_name, method_info):
                    self.methods_by_name[method_name].append(method_info)
                    self.all_methods.append(method_info)
                    # print(f"   ✅ DEBUG - Metod bulundu: {method_name} ({'in ' + method_info['class'] if method_info['class'] else 'global'})")
                    # print(f"       Method Info: {method_info}")
                else:
                    print(f"   ⏭️  Excluded: {method_name} ({'in ' + method_info['class'] if method_info['class'] else 'global'})")
            
            # Metod çağrılarını topla (excluded olanları da dahil et - çünkü kullanım kontrolü için gerekli)
            self.method_calls.update(visitor.method_calls)
            
        except Exception as e:
            print(f"❗ UYARI: {file_path} dosyası analiz edilemedi: {e}")
    
    def _search_method_occurrences_in_project(self):
        """Projedeki tüm Python dosyalarında metod geçişlerini arar."""
        print("🔍 Metod geçişleri aranıyor...")
        
        # Her metod için tüm projedeki dosyalarda arama yap
        for method_info in self.all_methods:
            method_name = method_info['name']
            
            # Tüm proje dosyalarında ara
            for py_file in self.project_files:
                self._search_method_in_file(method_name, py_file)
    
    def _search_method_occurrences_in_analyzed_files(self):
        """Analiz edilen dosyalarda metod geçişlerini arar."""
        print("🔍 Metod geçişleri aranıyor...")
        
        # Her metod için analiz edilen dosyalarda arama yap
        for method_info in self.all_methods:
            method_name = method_info['name']
            
            # Sadece analiz edilen dosyalarda ara
            for py_file in self.analyzed_files:
                self._search_method_in_file(method_name, py_file)
    
    def _search_method_in_file(self, method_name, file_path):
        """Belirtilen dosyada metod ismini arar."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Metod isminin geçip geçmediğini kontrol et
                if method_name in line:
                    # Daha hassas kontroller
                    stripped_line = line.strip()
                    
                    # Yorum satırlarını ve string literalleri atla
                    # Mustafa: 25.07.2025 - Yorum satırlarında geçtiği yerleri de göstersin

                    # if (stripped_line.startswith('#') or 
                    #     stripped_line.startswith('"""') or 
                    #     stripped_line.startswith("'''")):
                    #     continue
                    
                    # Metod tanımı satırını atla (def method_name)
                    if f"def {method_name}(" in line:
                        continue
                    
                    # Gerçekten metodun kullanıldığından emin ol
                    if self._is_method_usage(line, method_name):
                        # Tuple kullanarak benzersizlik sağla
                        occurrence_tuple = (file_path, line_num, stripped_line)
                        self.method_occurrences[method_name].add(occurrence_tuple)
                        
        except Exception as e:
            print(f"❗ UYARI: {file_path} dosyasında arama yapılamadı: {e}")
    
    def _is_method_usage(self, line, method_name):
        """Satırda metodun gerçekten kullanılıp kullanılmadığını kontrol eder."""
        import re
        
        # Metod çağrısı kalıpları
        patterns = [
            rf'\b{method_name}\s*\(',  # method_name(
            rf'\.{method_name}\s*\(',  # .method_name(
            rf'{method_name}\s*=',     # method_name = (assignment)
            rf'={method_name}\b',      # = method_name
            rf'\b{method_name}\b',     # kelime sınırlarında method_name
        ]
        
        for pattern in patterns:
            if re.search(pattern, line):
                return True
        
        return False
    
    def _find_local_imports(self, file_path, visited_files=None, base_dir=None):
        """Dosyanın import ettiği yerel Python dosyalarını recursive olarak bulur - alt klasörler dahil."""
        if visited_files is None:
            visited_files = set()
        
        # Sonsuz döngüyü önlemek için zaten ziyaret edilen dosyaları kontrol et
        if file_path in visited_files:
            return []
        
        visited_files.add(file_path)
        imported_files = []
        file_dir = os.path.dirname(file_path)
        
        # İlk çağrıda base_dir'i ayarla
        if base_dir is None:
            base_dir = file_dir
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        # Yerel import dosyasını bul
                        potential_file = self._resolve_local_import(module_name, file_dir, base_dir)
                        if potential_file and potential_file not in visited_files:
                            imported_files.append(potential_file)
                            print(f"   📁 Import bulundu: {os.path.basename(potential_file)} <- {os.path.basename(file_path)}")
                            
                            # Bu dosyanın da import'larını recursive olarak bul
                            nested_imports = self._find_local_imports(potential_file, visited_files.copy(), base_dir)
                            imported_files.extend(nested_imports)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        
                        # Yerel import dosyasını bul
                        potential_file = self._resolve_local_import(module_name, file_dir, base_dir)
                        if potential_file and potential_file not in visited_files:
                            imported_files.append(potential_file)
                            print(f"   📁 From-Import bulundu: {os.path.basename(potential_file)} <- {os.path.basename(file_path)}")
                            
                            # Bu dosyanın da import'larını recursive olarak bul
                            nested_imports = self._find_local_imports(potential_file, visited_files.copy(), base_dir)
                            imported_files.extend(nested_imports)
    
        except Exception as e:
            print(f"❗ HATA: {file_path} import analizi sırasında hata: {e}")
        
        # Mükerrer dosyaları temizle
        unique_imports = []
        for imp in imported_files:
            if imp not in unique_imports:
                unique_imports.append(imp)
        
        return unique_imports
    
    def _resolve_local_import(self, module_name, file_dir, base_dir):
        """Import adını dosya yoluna çevirir - sadece proje dizini içindeki dosyaları bulur."""
        # Python builtin ve standart kütüphane kontrolü
        import sys
        builtin_modules = set(sys.builtin_module_names)
        stdlib_modules = {
            'os', 'sys', 'datetime', 'json', 'csv', 'sqlite3', 'tkinter', 'threading',
            'subprocess', 'shutil', 'pathlib', 're', 'math', 'random', 'collections',
            'itertools', 'functools', 'operator', 'time', 'urllib', 'http', 'email',
            'html', 'xml', 'zipfile', 'tarfile', 'gzip', 'pickle', 'hashlib', 'hmac',
            'base64', 'uuid', 'logging', 'unittest', 'doctest', 'argparse', 'configparser',
            'io', 'tempfile', 'glob', 'fnmatch', 'platform', 'socket', 'ssl', 'ftplib',
            'smtplib', 'imaplib', 'poplib', 'telnetlib', 'webbrowser', 'ast', 'inspect',
            'typing', 'dataclasses', 'abc', 'copy', 'enum', 'traceback', 'warnings',
            'contextlib', 'decimal', 'fractions', 'statistics', 'struct', 'codecs',
            'textwrap', 'difflib', 'pprint', 'reprlib', 'heapq', 'bisect', 'array',
            'weakref', 'types', 'gc', 'dis', 'atexit', 'queue', 'asyncio', 'concurrent',
            'multiprocessing', 'signal', 'mmap', 'ctypes', 'tkcalendar', 'customtkinter',
            'PIL', 'numpy', 'pandas', 'matplotlib', 'pygame', 'requests', 'bs4',
            'flask', 'django', 'scipy', 'cv2', 'sklearn', 'tensorflow', 'torch'
        }
        
        main_module = module_name.split('.')[0]
        
        if main_module in builtin_modules or main_module in stdlib_modules:
            return None  # Standart kütüphane veya yaygın üçüncü taraf kütüphane
        
        module_parts = module_name.split('.')
        
        # Projeyi sınırla - sadece base_dir altındaki dosyaları kabul et
        def is_within_project(path):
            """Dosyanın proje dizini içinde olup olmadığını kontrol eder."""
            try:
                abs_path = os.path.abspath(path)
                abs_base = os.path.abspath(base_dir)
                # site-packages kontrolü
                if 'site-packages' in abs_path.lower() or 'dist-packages' in abs_path.lower():
                    return False
                # Proje dizini dışındaki dosyaları reddet
                return abs_path.startswith(abs_base)
            except:
                return False
        
        # 1. Aynı dizinde .py dosyası ara
        possible_paths = [
            os.path.join(file_dir, f"{module_name}.py"),
            os.path.join(file_dir, module_name, '__init__.py'),
            os.path.join(file_dir, main_module + '.py'),
            os.path.join(file_dir, main_module, '__init__.py'),
            os.path.join(base_dir, f"{module_name}.py"),
            os.path.join(base_dir, module_name, '__init__.py'),
            os.path.join(base_dir, main_module + '.py'),
            os.path.join(base_dir, main_module, '__init__.py')
        ]
        
        # 2. Noktalı importlar için (örn: mixins.helper -> mixins/helper.py)
        if len(module_parts) > 1:
            # file_dir'de ara
            subdir_path = os.path.join(file_dir, *module_parts[:-1], f"{module_parts[-1]}.py")
            possible_paths.append(subdir_path)
            
            subdir_init = os.path.join(file_dir, *module_parts, '__init__.py')
            possible_paths.append(subdir_init)
            
            # base_dir'de ara  
            base_subdir_path = os.path.join(base_dir, *module_parts[:-1], f"{module_parts[-1]}.py")
            possible_paths.append(base_subdir_path)
            
            base_subdir_init = os.path.join(base_dir, *module_parts, '__init__.py')
            possible_paths.append(base_subdir_init)
            
            # Tam yol: mixins/helper.py
            full_path = os.path.join(file_dir, *module_parts) + '.py'
            possible_paths.append(full_path)
            
            full_path_base = os.path.join(base_dir, *module_parts) + '.py'
            possible_paths.append(full_path_base)
        
        # Önce direkt yolları kontrol et
        for path in possible_paths:
            if os.path.exists(path) and is_within_project(path):
                return os.path.abspath(path)
        
        # 3. Sadece base_dir altında recursive arama yap
        for root, dirs, files in os.walk(base_dir):
            # __pycache__, .git, venv gibi klasörleri atla
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.vscode', 'venv', '.venv', 'env', '__pypackages__']]
            
            # main_module.py dosyasını ara
            target_file = main_module + '.py'
            if target_file in files:
                found_path = os.path.join(root, target_file)
                if is_within_project(found_path):
                    return os.path.abspath(found_path)
            
            # main_module klasörünü ara (paket)
            if main_module in dirs:
                # Paket içindeki spesifik modülü ara
                if len(module_parts) > 1:
                    specific_module = module_parts[-1] + '.py'
                    specific_path = os.path.join(root, main_module, specific_module)
                    if os.path.exists(specific_path) and is_within_project(specific_path):
                        return os.path.abspath(specific_path)
                
                # __init__.py var mı kontrol et
                init_path = os.path.join(root, main_module, '__init__.py')
                if os.path.exists(init_path) and is_within_project(init_path):
                    return os.path.abspath(init_path)
        
        return None
    
    def _find_unused_methods(self):
        """Tanımlı olduğu halde kullanılmayan metodları bulur."""
        self.unused_methods = []
        
        for method_info in self.all_methods:
            method_name = method_info['name']
            
            # Zaten excluded metodlar burada yok, ama double-check
            if not self._is_excluded_method(method_name, method_info):
                if method_name not in self.method_calls:
                    self.unused_methods.append(method_info)
    
    def get_duplicate_methods(self):
        """Aynı isimli metodları döndürür."""
        duplicates = []
        for method_name, methods in self.methods_by_name.items():
            if len(methods) > 1:
                duplicates.extend(methods)
        return duplicates
    
    def show_method_occurrences(self, method_name, highlight_file=None):
        """Belirtilen metodun geçtiği tüm yerleri gösteren pencere açar."""
        print(f"🔍 '{method_name}' metodunun geçtiği yerler gösteriliyor...")
        
        occurrences_window = tk.Toplevel(self.app)
        occurrences_window.title(f"'{method_name}' Metodunun Geçtiği Yerler")
        
        # Pencere boyut ve pozisyon ayarları
        self.app.load_or_center_window("method_occurrences", occurrences_window, 1000, 600)
        
        occurrences_window.transient(self.app)
        occurrences_window.grab_set()
        occurrences_window.focus_set()
        
        # Ana frame
        main_frame = ttk.Frame(occurrences_window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Başlık
        title_label = ttk.Label(main_frame, 
                               text=f"'{method_name}' metodunun projedeki tüm geçişleri:",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Set'ten listeye çevir ve sırala
        occurrences_set = self.method_occurrences.get(method_name, set())
        occurrences = [{'file': occ[0], 'line': occ[1], 'context': occ[2]} 
                      for occ in occurrences_set]
        
        # İstatistik bilgisi
        unique_files = set(occ['file'] for occ in occurrences)
        stats_label = ttk.Label(main_frame, 
                               text=f"Toplam {len(occurrences)} benzersiz geçiş bulundu, {len(unique_files)} farklı dosyada",
                               font=("Arial", 10, "italic"))
        stats_label.pack(pady=(0, 10))
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(expand=True, fill=tk.BOTH)
        
        # Treeview oluştur
        columns = ("Dosya", "Satır", "İçerik")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        tree.heading("Dosya", text="Dosya")
        tree.heading("Satır", text="Satır No")
        tree.heading("İçerik", text="Kod İçeriği")
        
        tree.column("Dosya", width=250)
        tree.column("Satır", width=80)
        tree.column("İçerik", width=500)
        
        # Çift tık ile dosyayı açma özelliği
        def on_tree_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item, "values")
                if len(values) >= 2 and values[0] and values[1]:
                    relative_path = values[0]
                    line_number = values[1]
                    
                    # Tam dosya yolunu bul
                    for occ in occurrences:
                        if os.path.relpath(occ['file'], os.path.dirname(self.project_files[0])) == relative_path:
                            try:
                                # Metodun editörde açılması
                                # self.app.grab_release()
                                occurrences_window.grab_release()

                                # Python editörde dosyayı aç
                                editor = PythonEditor(self.app, occ['file'], read_only=False)
                                try:
                                    editor.open_file_at_line(occ['file'], line_number)                
                                except ValueError:
                                    print(f"    HATA: Satır numarası parse edilemedi: {line_number}")

                                # Editör penceresini en üste getir
                                editor.window.deiconify()  # Pencereyi göster
                                editor.window.attributes('-topmost', True)  # En üste getir
                                editor.window.focus_force()  # Focus ver
                                editor.window.after(100, lambda: editor.window.attributes('-topmost', False))  # Kısa süre sonra topmost'u kaldır
                                    
                                print(f"📂 {occ['file']} dosyası açıldı (Satır: {line_number})")
                                break
                                
                            except Exception as e:
                                print(f"❗ Dosya açılamadı: {e}")
        
        tree.bind("<Double-1>", on_tree_double_click)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Veri ekle
        if occurrences:
            # Dosya adına göre grupla ve sırala
            occurrences_sorted = sorted(occurrences, key=lambda x: (os.path.basename(x['file']), x['line']))
            
            print(f"🔍 '{method_name}' metodu {len(occurrences_sorted)} benzersiz yerde bulundu")
            for occurrence in occurrences_sorted:
                relative_path = os.path.relpath(occurrence['file'], os.path.dirname(self.project_files[0]))
                context = occurrence['context']
                if len(context) > 100:
                    context = context[:100] + "..."
                
                tree.insert("", tk.END, values=(
                    relative_path,
                    occurrence['line'],
                    context
                ))
        else:
            tree.insert("", tk.END, values=("", "", f"'{method_name}' metodu hiçbir yerde kullanılmamış"))
        
        # Butonlar frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=(10, 0), fill=tk.X)
        
        # Bilgi etiketi
        info_button_label = ttk.Label(buttons_frame, 
                                     text="💡 İpucu: Dosyayı açmak için satıra çift tıklayın",
                                     font=("Arial", 8, "italic"))
        info_button_label.pack(side=tk.LEFT)
        
        # Yenile butonu
        refresh_button = ttk.Button(buttons_frame, text="🔄 Yeniden Ara", 
                                   command=lambda: self._refresh_method_search(method_name, tree))
        refresh_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Kapat düğmesi - pencere kapatılırken pozisyonu kaydet
        def on_close():
            geom = occurrences_window.winfo_geometry()            
            self.app.db.save_window_geometry("method_occurrences", geom)
            occurrences_window.destroy()
        
        close_button = ttk.Button(buttons_frame, text="Kapat", command=on_close)
        close_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # ESC ve X butonu ile kapatma
        occurrences_window.protocol("WM_DELETE_WINDOW", on_close)
        occurrences_window.bind("<Escape>", lambda e: on_close())

    def _refresh_method_search(self, method_name, tree):
        """Metod aramasını yeniler."""
        # Eski sonuçları temizle
        self.method_occurrences[method_name] = set()
        
        # Yeniden ara
        for py_file in self.project_files:
            self._search_method_in_file(method_name, py_file)
        
        # Treeview'i güncelle
        tree.delete(*tree.get_children())
        
        # Set'ten listeye çevir
        occurrences_set = self.method_occurrences.get(method_name, set())
        occurrences = [{'file': occ[0], 'line': occ[1], 'context': occ[2]} 
                      for occ in occurrences_set]
        
        if occurrences:
            occurrences_sorted = sorted(occurrences, key=lambda x: (os.path.basename(x['file']), x['line']))
            for occurrence in occurrences_sorted:
                relative_path = os.path.relpath(occurrence['file'], os.path.dirname(self.project_files[0]))
                context = occurrence['context'][:100] + "..." if len(occurrence['context']) > 100 else occurrence['context']
                tree.insert("", tk.END, values=(relative_path, occurrence['line'], context))
        else:
            tree.insert("", tk.END, values=("", "", f"'{method_name}' metodu hiçbir yerde kullanılmamış"))

    def _is_main_file(self, file_path):
        """Dosyanın projenin ana dosyası olup olmadığını kontrol eder."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. __main__ kontrolü - En güvenilir yöntem
            if 'if __name__ == "__main__":' in content:
                return True, "Contains __main__ block"
            
            # 2. Ana dosya isim kalıpları
            filename = os.path.basename(file_path).lower()
            main_file_patterns = ['main.py', 'app.py', 'run.py', 'start.py', 'launcher.py', 'index.py']
            if filename in main_file_patterns:
                return True, f"Main file pattern: {filename}"
            
            # 3. Tkinter mainloop() çağrısı
            if '.mainloop()' in content:
                return True, "Contains mainloop() call"
            
            # 4. Flask/Django app.run() çağrısı
            if 'app.run(' in content or 'application.run(' in content:
                return True, "Contains app.run() call"
            
            # 5. Diğer framework başlatma kalıpları
            startup_patterns = [
                'sys.exit(',
                'QApplication(',
                'app.exec_(',
                'root.mainloop()',
                'pygame.init()',
                'server.serve_forever()',
                'uvicorn.run(',
                'gunicorn'
            ]
            
            for pattern in startup_patterns:
                if pattern in content:
                    return True, f"Contains startup pattern: {pattern}"
            
            # 6. Import analizi - Ana dosyalar genelde çok import yapar
            import_count = content.count('import ') + content.count('from ')
            total_lines = len(content.splitlines())
            
            if import_count > 5 and total_lines < 100:  # Çok import, az kod = ana dosya olabilir
                return True, f"High import ratio: {import_count} imports in {total_lines} lines"
            
            return False, "No main file indicators found"
            
        except Exception as e:
            return False, f"Error analyzing file: {e}"
    
    def _find_project_main_files(self, project_dir):
        """Projedeki potansiyel ana dosyaları bulur."""
        main_files = []
        
        for root, dirs, files in os.walk(project_dir):
            # __pycache__ ve .git klasörlerini atla
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.vscode', '__pycache__']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    is_main, reason = self._is_main_file(file_path)
                    
                    if is_main:
                        main_files.append({
                            'path': file_path,
                            'reason': reason,
                            'name': file
                        })
        
        return main_files
    
    def show_analysis_window(self, file_path):
        """Analiz sonuçlarını gösteren pencereyi açar."""
        # Ana dosya kontrolü
        is_main, main_reason = self._is_main_file(file_path)
        
        # Önce analizi yap
        self.analyze_file(file_path)
        
        # Pencereyi oluştur
        self.analysis_window = tk.Toplevel(self.app)
        self.analysis_window.title(f"Python Metod Kontrolü - {os.path.basename(file_path)}")
        
        # Pencere boyut ve pozisyon ayarları 
        self.app.load_or_center_window("method_analysis", self.analysis_window, 1200, 800)

        self.analysis_window.transient(self.app)
        self.analysis_window.grab_set()
        self.analysis_window.focus_set()
        
        # Ana frame
        main_frame = ttk.Frame(self.analysis_window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Dosya türü bilgisi
        file_type_frame = ttk.Frame(main_frame)
        file_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        if is_main:
            file_type_label = ttk.Label(file_type_frame, 
                                       text=f"🚀 Ana Dosya: {main_reason}",
                                       font=("Arial", 10, "bold"),
                                       foreground="darkgreen")
        else:
            file_type_label = ttk.Label(file_type_frame, 
                                       text=f"📄 Modül Dosyası: {main_reason}",
                                       font=("Arial", 10),
                                       foreground="darkblue")
        file_type_label.pack(side=tk.LEFT)
        
        # Ana dosyaları göster butonu
        show_main_files_button = ttk.Button(file_type_frame, 
                                           text="🔍 Projedeki Ana Dosyaları Göster",
                                           command=lambda: self._show_project_main_files(file_path))
        show_main_files_button.pack(side=tk.RIGHT)
        
        # Analiz bilgisi
        excluded_count = sum(1 for method in self.all_methods if self._is_excluded_method(method['name'], method))
        info_label = ttk.Label(main_frame, 
                              text=f"Analiz: {len(self.analyzed_files)} dosya, {len(self.all_methods)} metod " +
                                   f"({excluded_count} standart metod hariç tutuldu)",
                              font=("Arial", 10, "italic"))
        info_label.pack(pady=(0, 10))
        
        # Excluded metodları göster butonu
        show_excluded_button = ttk.Button(main_frame, text="🔍 Hariç Tutulan Metodları Göster",
                                         command=lambda: self._show_excluded_methods(file_path))
        show_excluded_button.pack(pady=(0, 10))
        
        # Notebook için sekmeler
        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill=tk.BOTH)
        
        # Sekmeler oluştur
        self._create_duplicate_methods_tab(notebook)
        self._create_unused_methods_tab(notebook)
        self._create_all_methods_tab(notebook)
        
        # Kapat düğmesi - pencere kapatılırken pozisyonu kaydet
        def on_close():
            geom = self.analysis_window.winfo_geometry()
            self.app.db.save_window_geometry("method_analysis", geom)
            self.analysis_window.destroy()
        
        close_button = ttk.Button(main_frame, text="Kapat", command=on_close)
        close_button.pack(pady=(10, 0))
        
        # ESC ve X butonu ile kapatma - pozisyonu kaydet
        self.analysis_window.protocol("WM_DELETE_WINDOW", on_close)
        self.analysis_window.bind("<Escape>", lambda e: on_close())

    def _show_project_main_files(self, current_file_path):
        """Projedeki tüm ana dosyaları gösteren pencere açar."""
        project_dir = os.path.dirname(current_file_path)
        main_files = self._find_project_main_files(project_dir)
        
        main_files_window = tk.Toplevel(self.app)
        main_files_window.title("Projedeki Ana Dosyalar")
        
        # Pencere boyut ve pozisyon ayarları
        self.app.load_or_center_window("project_main_files", main_files_window, 800, 500)

        main_files_window.transient(self.app)
        main_files_window.grab_set()
        main_files_window.focus_set()
        
        # Ana frame
        main_frame = ttk.Frame(main_files_window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Başlık
        title_label = ttk.Label(main_frame, 
                               text="Projedeki Potansiyel Ana Dosyalar:",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(expand=True, fill=tk.BOTH)

        # Treeview oluştur
        columns = ("Dosya Adı", "Yol", "Ana Dosya Olma Nedeni")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        tree.heading("Dosya Adı", text="Dosya Adı")
        tree.heading("Yol", text="Dosya Yolu")
        tree.heading("Ana Dosya Olma Nedeni", text="Tespit Nedeni")
        
        tree.column("Dosya Adı", width=150)
        tree.column("Yol", width=300)
        tree.column("Ana Dosya Olma Nedeni", width=250)
        
        # Çift tık ile analiz et
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                file_name = tree.item(item, "values")[0]
                
                # Dosya yolunu bul
                for main_file in main_files:
                    if os.path.basename(main_file['path']) == file_name:
                        main_files_window.destroy()
                        # Yeni analiz penceresi aç
                        new_analyzer = MethodAnalyzer(self.app)
                        new_analyzer.show_analysis_window(main_file['path'])
                        break
        
        tree.bind("<Double-1>", on_double_click)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Veri ekle
        if main_files:
            for main_file in main_files:
                # Mevcut dosyayı vurgula
                if main_file['path'] == current_file_path:
                    item_id = tree.insert("", tk.END, values=(
                        f"👑 {main_file['name']} (Mevcut)",
                        os.path.relpath(main_file['path'], project_dir),
                        main_file['reason']
                    ))
                    tree.selection_set(item_id)
                    tree.focus(item_id)
                else:
                    tree.insert("", tk.END, values=(
                        main_file['name'],
                        os.path.relpath(main_file['path'], project_dir),
                        main_file['reason']
                    ))
        else:
            tree.insert("", tk.END, values=("Ana dosya bulunamadı", "", "Hiçbir dosyada ana dosya kalıbı tespit edilmedi"))
        
        # Bilgi etiketi
        info_label = ttk.Label(main_frame, 
                              text="💡 İpucu: Başka bir ana dosyayı analiz etmek için çift tıklayın",
                              font=("Arial", 8, "italic"))
        info_label.pack(pady=(10, 0))
        
        # Kapat düğmesi - pencere kapatılırken pozisyonu kaydet
        def on_close():
            geom = main_files_window.winfo_geometry()
            self.app.db.save_window_geometry("project_main_files", geom)
            main_files_window.destroy()
        
        close_button = ttk.Button(main_frame, text="Kapat", command=on_close)
        close_button.pack(pady=(10, 0))
        
        # ESC ve X butonu ile kapatma
        main_files_window.protocol("WM_DELETE_WINDOW", on_close)
        main_files_window.bind("<Escape>", lambda e: on_close())

    def _show_excluded_methods(self, file_path):
        """Hariç tutulan metodları gösteren pencere açar."""
        excluded_window = tk.Toplevel(self.app)
        excluded_window.title("Hariç Tutulan Metodlar")
        
        # Pencere boyut ve pozisyon ayarları
        self.app.load_or_center_window("excluded_methods", excluded_window, 800, 600)

        excluded_window.transient(self.app)
        excluded_window.grab_set()
        excluded_window.focus_set()
        
        # Ana frame
        main_frame = ttk.Frame(excluded_window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Başlık
        title_label = ttk.Label(main_frame, 
                               text="Analizden Hariç Tutulan Standart Metodlar:",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(expand=True, fill=tk.BOTH)        

        # Treeview oluştur
        columns = ("Metod Adı", "Dosya", "Satır", "Sınıf", "Hariç Tutulma Nedeni")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hariç tutulan metodları bul ve göster
        excluded_methods_found = []
        for py_file in self.analyzed_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree_ast = ast.parse(content)
                visitor = MethodVisitor(py_file)
                visitor.visit(tree_ast)
                
                for method_info in visitor.methods:
                    if self._is_excluded_method(method_info['name'], method_info):
                        reason = self._get_exclusion_reason(method_info['name'], method_info)
                        tree.insert("", tk.END, values=(
                            method_info['name'],
                            os.path.basename(method_info['file']),
                            method_info['line'],
                            method_info['class'] or "Global",
                            reason
                        ))
            except Exception as e:
                continue
        
        # Kapat düğmesi - pencere kapatılırken pozisyonu kaydet
        def on_close():
            geom = excluded_window.winfo_geometry()
            self.app.db.save_window_geometry("excluded_methods", geom)
            excluded_window.destroy()
        
        close_button = ttk.Button(main_frame, text="Kapat", command=on_close)
        close_button.pack(pady=(10, 0))
        
        # ESC ve X butonu ile kapatma
        excluded_window.protocol("WM_DELETE_WINDOW", on_close)
        excluded_window.bind("<Escape>", lambda e: on_close())
    
    def _get_exclusion_reason(self, method_name, method_info=None):
        """Metodun neden hariç tutulduğunun açıklamasını döndürür."""
        if method_name.startswith('__') and method_name.endswith('__'):
            return "Python Magic Method"
        elif method_name.startswith('test_'):
            return "Test Method"
        elif method_name.startswith('on_'):
            return "Event Handler"
        elif method_name.startswith('handle_'):
            return "Event Handler"
        elif '_callback' in method_name or method_name.startswith('callback_'):
            return "Callback Method"
        elif method_name in self.excluded_methods:
            return "Common Framework Method"
        else:
            return "Pattern Match"

    def _create_duplicate_methods_tab(self, parent):
        """Aynı isimli metodlar sekmesi."""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Aynı İsimli Metodlar")
        
        # Açıklama
        info_label = ttk.Label(frame, 
                              text="Çift tıklayarak metodun projedeki tüm geçişlerini görebilirsiniz, sağ tıklayarak metodu açabilirsiniz. \n Aynı isimli metodun farklı sınıflarda geçiyor olmasını dikkate alınız",
                              font=("Arial", 9, "italic"))
        info_label.pack(pady=(5, 10))
        
        # Treeview oluştur
        columns = ("Metod Adı", "Dosya", "Satır", "Sınıf")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        
        # Çift tık olayını bağla
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                method_name = tree.item(item, "values")[0]
                if method_name and method_name != "Aynı isimli metod bulunamadı":
                    self.show_method_occurrences(method_name)
        
        tree.bind("<Double-1>", on_double_click)
        
        # Sağ tık menüsü
        def on_right_click(event):
            iid = tree.identify_row(event.y)
            if iid:
                tree.selection_set(iid)
                values = tree.item(iid, "values")
                method_name = values[0]
                file_name = values[1]
                line_number = values[2]
                # Dosya yolunu bul
                file_path = None
                for method in self.get_duplicate_methods():
                    if (method['name'] == method_name and
                        os.path.basename(method['file']) == file_name and
                        str(method['line']) == str(line_number)):
                        file_path = method['file']
                        break
                if not file_path:
                    return

                menu = tk.Menu(tree, tearoff=0)
                def open_file():
                    try:
                        self.analysis_window.grab_release()
                        editor = PythonEditor(self.app, file_path, read_only=False)
                        editor.open_file_at_line(file_path, line_number)
                        editor.window.deiconify()
                        editor.window.attributes('-topmost', True)
                        editor.window.focus_force()
                        editor.window.after(100, lambda: editor.window.attributes('-topmost', False))
                    except Exception as e:
                        print(f"❗ Dosya açılamadı: {e}")
                menu.add_command(label=f"Bu Metodu Aç: {file_name}", command=open_file)
                menu.tk_popup(event.x_root, event.y_root)
        
        tree.bind("<Button-3>", on_right_click)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Veri ekle
        duplicates = self.get_duplicate_methods()
        if duplicates:
            for method in duplicates:
                tree.insert("", tk.END, values=(
                    method['name'],
                    os.path.basename(method['file']),
                    method['line'],
                    method['class'] or "Global"
                ))
        else:
            tree.insert("", tk.END, values=("Aynı isimli metod bulunamadı", "", "", ""))

    def _create_unused_methods_tab(self, parent):
        """Kullanılmayan metodlar sekmesi."""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Kullanılmayan Metodlar")
        
        # Açıklama
        info_label = ttk.Label(frame, 
                              text="Çift tıklayarak metodun geçtiği tüm yerleri görebilirsiniz",
                              font=("Arial", 9, "italic"))
        info_label.pack(pady=(5, 10))
        
        # Treeview oluştur
        columns = ("Metod Adı", "Dosya", "Satır", "Sınıf")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        
        # Çift tık olayını bağla
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                method_name = tree.item(item, "values")[0]
                if method_name and method_name != "Kullanılmayan metod bulunamadı":
                    self.show_method_occurrences(method_name)
        
        tree.bind("<Double-1>", on_double_click)
        
        # Sağ tık menüsü
        def on_right_click(event):
            iid = tree.identify_row(event.y)
            if iid:
                tree.selection_set(iid)
                values = tree.item(iid, "values")
                method_name = values[0]
                file_name = values[1]
                line_number = values[2]
                # Dosya yolunu bul
                file_path = None
                for method in self.unused_methods:
                    if (method['name'] == method_name and
                        os.path.basename(method['file']) == file_name and
                        str(method['line']) == str(line_number)):
                        file_path = method['file']
                        break
                if not file_path:
                    return

                menu = tk.Menu(tree, tearoff=0)
                def open_file():
                    try:
                        self.analysis_window.grab_release()
                        editor = PythonEditor(self.app, file_path, read_only=False)
                        editor.open_file_at_line(file_path, line_number)
                        editor.window.deiconify()
                        editor.window.attributes('-topmost', True)
                        editor.window.focus_force()
                        editor.window.after(100, lambda: editor.window.attributes('-topmost', False))
                    except Exception as e:
                        print(f"❗ Dosya açılamadı: {e}")
                menu.add_command(label=f"Kullanılmayan Metodu Aç: {file_name}", command=open_file)
                menu.tk_popup(event.x_root, event.y_root)
        
        tree.bind("<Button-3>", on_right_click)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Veri ekle
        if self.unused_methods:
            for method in self.unused_methods:
                tree.insert("", tk.END, values=(
                    method['name'],
                    os.path.basename(method['file']),
                    method['line'],
                    method['class'] or "Global"
                ))
        else:
            tree.insert("", tk.END, values=("Kullanılmayan metod bulunamadı", "", "", ""))

    def _create_all_methods_tab(self, parent):
        """Tüm metodlar sekmesi."""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Tüm Metodlar")
        
        # Açıklama
        info_label = ttk.Label(frame, 
                              text="Çift tıklayarak metodun projedeki tüm geçişlerini görebilirsiniz",
                              font=("Arial", 9, "italic"))
        info_label.pack(pady=(5, 10))
        
        # Treeview oluştur
        columns = ("Metod Adı", "Dosya", "Satır", "Sınıf", "Durumu")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Çift tık olayını bağla
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                method_name = tree.item(item, "values")[0]
                if method_name and method_name != "Metod bulunamadı":
                    self.show_method_occurrences(method_name)
        
        tree.bind("<Double-1>", on_double_click)
        
        # Sağ tık menüsü
        def on_right_click(event):
            iid = tree.identify_row(event.y)
            if iid:
                tree.selection_set(iid)
                values = tree.item(iid, "values")
                method_name = values[0]
                file_name = values[1]
                line_number = values[2]
                # Dosya yolunu bul
                file_path = None
                for method in self.all_methods:
                    if (method['name'] == method_name and
                        os.path.basename(method['file']) == file_name and
                        str(method['line']) == str(line_number)):
                        file_path = method['file']
                        break
                if not file_path:
                    return

                menu = tk.Menu(tree, tearoff=0)
                def open_file():
                    try:
                        self.analysis_window.grab_release()
                        editor = PythonEditor(self.app, file_path, read_only=False)
                        editor.open_file_at_line(file_path, line_number)
                        editor.window.deiconify()
                        editor.window.attributes('-topmost', True)
                        editor.window.focus_force()
                        editor.window.after(100, lambda: editor.window.attributes('-topmost', False))
                    except Exception as e:
                        print(f"❗ Dosya açılamadı: {e}")
                menu.add_command(label=f"Metodu Aç: {file_name}", command=open_file)
                menu.tk_popup(event.x_root, event.y_root)
        
        tree.bind("<Button-3>", on_right_click)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Veri ekle
        unused_method_names = {m['name'] for m in self.unused_methods}
        duplicate_method_names = {name for name, methods in self.methods_by_name.items() if len(methods) > 1}
        
        if self.all_methods:
            for method in self.all_methods:
                status = []
                if method['name'] in unused_method_names:
                    status.append("Kullanılmıyor")
                if method['name'] in duplicate_method_names:
                    status.append("Duplikasyon")
                
                tree.insert("", tk.END, values=(
                    method['name'],
                    os.path.basename(method['file']),
                    method['line'],
                    method['class'] or "Global",
                    ", ".join(status) if status else "Normal"
                ))
        else:
            tree.insert("", tk.END, values=("Metod bulunamadı", "", "", "", ""))


class MethodVisitor(ast.NodeVisitor):
    """AST visitor to find method definitions and calls."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.methods = []
        self.method_calls = set()
        self.current_class = None
        self.method_references = []  # Metod referansları için
    
    def visit_ClassDef(self, node):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        self.methods.append({
            'name': node.name,
            'file': self.file_path,
            'line': node.lineno,
            'class': self.current_class
        })
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self.methods.append({
            'name': node.name,
            'file': self.file_path,
            'line': node.lineno,
            'class': self.current_class
        })
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            self.method_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.method_calls.add(node.func.attr)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Visit attribute access (method references)."""
        if isinstance(node.ctx, ast.Load):
            self.method_calls.add(node.attr)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit name references."""
        if isinstance(node.ctx, ast.Load):
            self.method_calls.add(node.id)

if __name__ == "__main__":
    print("############################################################################################")
    print("   Bu dosya doğrudan çalıştırılamaz, Python Program Yöneticisi Metod Analiz  modülüdür.")
    print("############################################################################################")


