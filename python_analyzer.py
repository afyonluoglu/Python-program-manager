# -*- coding: utf-8 -*-

import os
import ast
import sys
import re
import tkinter as tk
import subprocess
from tkinter import ttk, messagebox
from datetime import datetime
import importlib.util
from typing import Dict, List, Set, Tuple

# Modern alternatif: importlib.metadata (Python 3.8+)
try:
    from importlib.metadata import distributions
    METADATA_AVAILABLE = True
except ImportError:
    # Python 3.7 ve altı için fallback
    METADATA_AVAILABLE = False


class DependencyAnalyzer:
    def __init__(self):
        self.builtin_modules = set(sys.builtin_module_names)
        self.stdlib_modules = self._get_stdlib_modules()
        self.installed_packages = self._get_installed_packages()
        
        # Import name'den package name'e mapping
        self.import_to_package_mapping = {
            'PIL': 'Pillow',
            'fitz': 'PyMuPDF', 
            'tabula': 'tabula-py',
            'cv2': 'opencv-python',
            'skimage': 'scikit-image',
            'sklearn': 'scikit-learn',
            'yaml': 'PyYAML',
            'requests_oauthlib': 'requests-oauthlib',
            'bs4': 'beautifulsoup4',
            'dateutil': 'python-dateutil',
            'psutil': 'psutil',
            'magic': 'python-magic',
            'dotenv': 'python-dotenv',
            'jwt': 'PyJWT',
            'serial': 'pyserial',
            'win32api': 'pywin32',
            'win32con': 'pywin32',
            'win32gui': 'pywin32',
            'pywintypes': 'pywin32'
        }
    def analyze_project_dependencies(self, project_files: List[str]) -> Dict:
        """Proje dosyalarındaki tüm bağımlılıkları analiz et"""
        all_imports = set()
        missing_packages = set()
        installed_packages = set()
        builtin_used = set()
        stdlib_used = set()
        
        # Proje dizinlerini ve yerel modül isimlerini belirle
        project_dirs = set()
        local_modules = set()
        
        for file_path in project_files:
            project_dirs.add(os.path.dirname(file_path))
            # Dosya adını .py uzantısız al (yerel modül adı)
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            if module_name != '__init__':  # __init__.py dosyalarını hariç tut
                local_modules.add(module_name)
        
        # Her dosyadan import'ları çıkar
        for file_path in project_files:
            try:
                file_imports = self._extract_imports_from_file(file_path)
                all_imports.update(file_imports)
            except Exception as e:
                print(f"❗ Import analizi hatası {file_path}: {e}")
          # Import'ları kategorize et
        for import_name in all_imports:
            # Yerel modül kontrolü
            if import_name in local_modules:
                continue  # Yerel modülleri atla
            
            # Yerel dizin/klasör kontrolü 
            is_local_module = False
            for project_dir in project_dirs:
                # .py dosyası var mı kontrol et
                potential_file = os.path.join(project_dir, f"{import_name}.py")
                if os.path.exists(potential_file):
                    is_local_module = True
                    break
                
                # Klasör ve __init__.py dosyası var mı kontrol et
                potential_package = os.path.join(project_dir, import_name)
                if os.path.isdir(potential_package):
                    init_file = os.path.join(potential_package, "__init__.py")
                    if os.path.exists(init_file):
                        is_local_module = True
                        break
                    # __init__.py yoksa da klasör varsa yerel modül olarak kabul et
                    # Çünkü proje içindeki klasörler paket değil
                    is_local_module = True
                    break
            
            if is_local_module:
                continue  # Yerel modülleri/klasörleri atla
            
            # Kategorize et
            if self._is_builtin(import_name):
                builtin_used.add(import_name)
            elif self._is_stdlib(import_name):
                stdlib_used.add(import_name)
            elif self._is_installed(import_name):
                installed_packages.add(import_name)
            else:
                missing_packages.add(import_name)
        
        return {
            'all_imports': sorted(all_imports),
            'builtin_modules': sorted(builtin_used),
            'stdlib_modules': sorted(stdlib_used),
            'installed_packages': sorted(installed_packages),
            'missing_packages': sorted(missing_packages),
            'requirements': self._generate_requirements(installed_packages),
            'pip_install_command': self._generate_pip_command(missing_packages)
        }
    
    def _extract_imports_from_file(self, file_path: str) -> Set[str]:
        """Dosyadan import'ları çıkar"""
        imports = set()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            module_name = name.name.split('.')[0]
                            imports.add(module_name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.split('.')[0]
                            imports.add(module_name)
                            
            except SyntaxError:
                # AST parsing başarısızsa regex fallback
                f.seek(0)
                content = f.read()
                imports.update(self._regex_import_extraction(content))
        
        return imports
    
    def _regex_import_extraction(self, content: str) -> Set[str]:
        """Regex ile import çıkarma (fallback)"""
        import re
        imports = set()
          # import module_name
        import_pattern = r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        imports.update(re.findall(import_pattern, content, re.MULTILINE))
        
        # from module_name import ...
        from_pattern = r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
        imports.update(re.findall(from_pattern, content, re.MULTILINE))
        
        return imports
    
    def _get_stdlib_modules(self) -> Set[str]:
        """Standart kütüphane modüllerini al"""
        stdlib = set()
        
        # Dinamik stdlib modüllerini al
        try:
            import sys
            import pkgutil
            
            # Builtin modüller zaten self.builtin_modules'te var
            # Standart kütüphane yollarını bul
            stdlib_paths = []
            for path in sys.path:
                if path and 'site-packages' not in path and 'dist-packages' not in path:
                    if 'lib' in path or 'python' in path.lower():
                        stdlib_paths.append(path)
            
            # pkgutil ile standart modülleri tara
            for importer, modname, ispkg in pkgutil.iter_modules(stdlib_paths):
                if not modname.startswith('_'):  # Private modülleri atla
                    stdlib.add(modname)
                    
        except Exception as e:
            print(f"❗ Dinamik stdlib taraması başarısız: {e}")

        # Bilinen Python standart kütüphane modülleri (fallback)
        known_stdlib = {
            'os', 'sys', 'json', 'datetime', 'time', 'math', 'random',
            'collections', 'itertools', 'functools', 'operator', 're',
            'string', 'io', 'pathlib', 'glob', 'shutil', 'tempfile',
            'subprocess', 'threading', 'multiprocessing', 'queue',
            'socket', 'urllib', 'http', 'email', 'html', 'xml',
            'sqlite3', 'csv', 'configparser', 'logging', 'unittest',
            'argparse', 'getopt', 'warnings', 'contextlib', 'weakref',
            'copy', 'pickle', 'shelve', 'marshal', 'dbm', 'zlib',
            'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'hashlib',
            'hmac', 'secrets', 'ssl', 'base64', 'binascii', 'struct',
            'codecs', 'unicodedata', 'stringprep', 'readline', 'rlcompleter',
            'pprint', 'reprlib', 'enum', 'types', 'inspect', 'importlib',
            'pkgutil', 'modulefinder', 'runpy', 'gc', 'dis', 'atexit',
            'traceback', 'faulthandler', 'pdb', 'profile', 'cProfile',
            'timeit', 'trace', 'ast', 'symtable', 'symbol', 'token',
            'keyword', 'tokenize', 'tabnanny', 'pyclbr', 'py_compile',
            'compileall', 'zipapp', 'venv', 'tkinter', 'turtle', 'colorsys',
            'decimal', 'fractions', 'statistics', 'calendar', 'locale',
            'gettext', 'optparse', 'shlex', 'cmd', 'pydoc',
            # Ek standart kütüphane modülleri
            'ctypes', 'fnmatch', 'platform', 'typing', 'dataclasses',
            'asyncio', 'concurrent', 'selectors', 'signal', 'errno',
            'mmap', 'resource', 'sysconfig', 'distutils', 'site',
            'heapq', 'bisect', 'array', 'textwrap', 'difflib', 'pstats', 
            'linecache', 'fileinput', 'stat', 'filecmp', 'macpath', 
            'ntpath', 'posixpath', 'genericpath', 'getpass', 'curses', 
            'msvcrt', 'winreg', 'winsound', 'msilib', '_winapi', 'audioop', 
            'aifc', 'sunau', 'wave', 'chunk', 'sndhdr', 'imghdr',
            'mailcap', 'mailbox', 'mimetypes', 'quopri', 'uu', 'binhex',
            'xdrlib', 'netrc', 'robotparser', 'cgi', 'cgitb',
            'wsgiref', 'socketserver', 'webbrowser', 'formatter',
            # Yaygın ek modüller
            'antigravity', 'this', 'uuid', 'ipaddress', 'smtplib', 'ftplib',
            'telnetlib', 'imaplib', 'poplib', 'nntplib', 'socketserver',
            'http.server', 'http.client', 'http.cookies', 'http.cookiejar',
            'urllib.parse', 'urllib.request', 'urllib.response', 'urllib.error',
            'html.parser', 'html.entities', 'xml.etree', 'xml.dom', 'xml.sax',            'xml.parsers', 'email.mime', 'email.header', 'email.utils',
            'test', 'distutils', 'lib2to3', 'ensurepip'
        }
        
        stdlib.update(known_stdlib)
        return stdlib
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """Yüklü paketleri al"""
        installed = {}
        
        try:
            # pip list ile yüklü paketleri al
            result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
            lines = result.stdout.split('\n')[2:]  # Header'ları atla
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[0].lower()
                        version = parts[1]
                        installed[package_name] = version
        except:
            # Modern importlib.metadata ile fallback (Python 3.8+)
            if METADATA_AVAILABLE:
                try:
                    for dist in distributions():
                        installed[dist.metadata['name'].lower()] = dist.version
                except:
                    pass
            else:
                # Daha eski Python sürümleri için temel fallback
                pass
        
        return installed
    
    def _is_builtin(self, module_name: str) -> bool:
        """Builtin modül mü?"""
        return module_name in self.builtin_modules
    
    def _is_stdlib(self, module_name: str) -> bool:
        """Standart kütüphane modülü mü?"""
        return module_name in self.stdlib_modules
    
    def _is_installed(self, module_name: str) -> bool:
        """Yüklü paket mi?"""
        # Önce direkt import name'i kontrol et
        if module_name.lower() in self.installed_packages:
            return True
        
        # Eğer mapping'de varsa, asıl package name'i kontrol et
        if module_name in self.import_to_package_mapping:
            actual_package = self.import_to_package_mapping[module_name]
            return actual_package.lower() in self.installed_packages
        
        return False
    
    def _generate_requirements(self, packages: Set[str]) -> List[str]:
        """requirements.txt formatında liste oluştur"""
        requirements = []
        
        for package in sorted(packages):
            # Mapping'de varsa asıl package name'i al
            actual_package = self.import_to_package_mapping.get(package, package)
            actual_package_lower = actual_package.lower()
            
            if actual_package_lower in self.installed_packages:
                version = self.installed_packages[actual_package_lower]
                requirements.append(f"{actual_package}=={version}")
            else:
                requirements.append(actual_package)
        
        return requirements
    
    def _generate_pip_command(self, missing_packages: Set[str]) -> str:
        """Eksik paketler için pip install komutu"""
        if missing_packages:
            # Missing packages'ı mapping'e göre asıl package isimlerine çevir
            actual_packages = []
            for package in sorted(missing_packages):
                actual_package = self.import_to_package_mapping.get(package, package)
                actual_packages.append(actual_package)
            
            packages = ' '.join(actual_packages)
            return f"pip install {packages}"
        return ""
    
    def generate_requirements_file(self, project_path: str, requirements: List[str]):
        """requirements.txt dosyası oluştur"""
        req_file_path = os.path.join(project_path, 'requirements.txt')
        
        with open(req_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
        
        return req_file_path
    
class PythonAnalyzer:
    """Python dosyalarını analiz etmek için sınıf."""
    
    def __init__(self, app_instance):
        self.app = app_instance    
        
    def analyze_python_file(self, file_path):
        """Python dosyasını ve bağımlı kullanıcı dosyalarını analiz eder ve sonuçları bir pencerede gösterir."""
        try:
            if not os.path.exists(file_path):
                messagebox.showerror("Hata", f"Dosya bulunamadı: {file_path}", parent=self.app)
                return
            
            if not file_path.lower().endswith('.py'):
                messagebox.showerror("Hata", "Sadece Python dosyaları (.py) analiz edilebilir.", parent=self.app)
                return
            
            # Tüm bağımlı dosyaları bul
            all_project_files = self._discover_project_files(file_path)
            
            # Dosyaları analiz et
            analysis_results = self._perform_project_analysis(file_path, all_project_files)
            
            # Sonuçları göster
            self._show_analysis_results(file_path, analysis_results)

            # History'ye kaydet
            self.app.db.add_history(f"Python Dosya Analizi: {file_path}", "method_analysis")            

            
        except Exception as e:
            messagebox.showerror("Analiz Hatası", f"Dosya analizi sırasında bir hata oluştu:\n{e}", parent=self.app)    
    def _perform_single_file_analysis(self, file_path):
        """Tek dosyanın detaylı analizini yapar (eski _perform_analysis fonksiyonu)."""
        results = {
            'file_info': {},
            'imports': {
                'builtin': [],
                'third_party': [],
                'user_defined': []
            },
            'code_stats': {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'blank_lines': 0,
                'docstring_lines': 0
            },
            'functions': [],
            'classes': [],
            'errors': []
        }

        # Dosya bilgileri
        file_stat = os.stat(file_path)
        results['file_info'] = {
            'name': os.path.basename(file_path),
            'size': file_stat.st_size,
            'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'path': file_path
        }

        try:
            # Dosyayı oku
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Satır bazlı analiz
            lines = content.split('\n')
            results['code_stats']['total_lines'] = len(lines)
            
            in_multiline_string = False
            string_delimiter = None
            
            for line in lines:
                stripped = line.strip()
                
                # Boş satırlar
                if not stripped:
                    results['code_stats']['blank_lines'] += 1
                    continue
                
                # Çok satırlı string kontrolü
                if '"""' in line or "'''" in line:
                    if not in_multiline_string:
                        in_multiline_string = True
                        string_delimiter = '"""' if '"""' in line else "'''"
                    elif string_delimiter in line:
                        in_multiline_string = False
                        string_delimiter = None
                    results['code_stats']['docstring_lines'] += 1
                elif in_multiline_string:
                    results['code_stats']['docstring_lines'] += 1
                # Yorum satırları
                elif stripped.startswith('#'):
                    results['code_stats']['comment_lines'] += 1
                # Kod satırları
                else:
                    results['code_stats']['code_lines'] += 1

            # AST ile analiz
            try:
                tree = ast.parse(content, filename=file_path)
                self._analyze_ast(tree, results)
            except SyntaxError as e:
                results['errors'].append(f"Sözdizimi hatası: {e}")
            except Exception as e:
                results['errors'].append(f"AST analizi hatası: {e}")

        except UnicodeDecodeError:
            # UTF-8 ile okuyamadıysa farklı encoding'ler dene
            encodings = ['latin1', 'cp1252', 'iso-8859-1']
            content_read = False
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    content_read = True
                    break
                except:
                    continue
            
            if not content_read:
                results['errors'].append("Dosya okunamadı: Desteklenmeyen karakter kodlaması")
        except Exception as e:
            results['errors'].append(f"Dosya okuma hatası: {e}")

        return results

    def _analyze_ast(self, tree, results):
        """AST kullanarak kod yapısını analiz eder."""
        for node in ast.walk(tree):
            # Import analizleri
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._categorize_import(alias.name, results)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._categorize_import(node.module, results)
            
            # Fonksiyon tanımları
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args),
                    'is_method': False
                }
                # Eğer bir sınıf içindeyse method olarak işaretle
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        for child in ast.walk(parent):
                            if child is node:
                                func_info['is_method'] = True
                                break
                
                results['functions'].append(func_info)
            
            # Sınıf tanımları
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [],
                    'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                }
                
                # Sınıf içindeki methodları bul
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append({
                            'name': item.name,
                            'line': item.lineno,
                            'args': len(item.args.args)
                        })
                
                results['classes'].append(class_info)

    def _categorize_import(self, module_name, results):
        """Import'u kategorize eder (builtin, third-party, user-defined)."""
        # Python builtin modülleri
        builtin_modules = set(sys.builtin_module_names)
        
        # Standart kütüphane modülleri (sadece önemli olanlar)
        stdlib_modules = {
            'os', 'sys', 'datetime', 'json', 'csv', 'sqlite3', 'tkinter', 'threading',
            'subprocess', 'shutil', 'pathlib', 're', 'math', 'random', 'collections',
            'itertools', 'functools', 'operator', 'time', 'urllib', 'http', 'email',
            'html', 'xml', 'zipfile', 'tarfile', 'gzip', 'pickle', 'hashlib', 'hmac',
            'base64', 'uuid', 'logging', 'unittest', 'doctest', 'argparse', 'configparser',
            'io', 'tempfile', 'glob', 'fnmatch', 'platform', 'socket', 'ssl', 'ftplib',
            'smtplib', 'imaplib', 'poplib', 'telnetlib', 'webbrowser'
        }
        
        # Ana modül adını al (noktadan önceki kısım)
        main_module = module_name.split('.')[0]
        
        if main_module in builtin_modules or main_module in stdlib_modules:
            if module_name not in results['imports']['builtin']:
                results['imports']['builtin'].append(module_name)
        else:
            # Kullanıcı tanımlı mı yoksa third-party mı kontrol et
            try:
                # Eğer modül mevcut dizinde bir .py dosyası ise user-defined
                current_dir = os.path.dirname(results['file_info']['path'])
                potential_file = os.path.join(current_dir, main_module + '.py')
                
                if os.path.exists(potential_file):
                    if module_name not in results['imports']['user_defined']:
                        results['imports']['user_defined'].append(module_name)
                else:
                    # Third-party olarak kategorize et
                    if module_name not in results['imports']['third_party']:
                        results['imports']['third_party'].append(module_name)
            except:
                # Hata durumunda third-party olarak kategorize et
                if module_name not in results['imports']['third_party']:
                    results['imports']['third_party'].append(module_name)                      
    def _show_analysis_results(self, file_path, results):
        """Proje analiz sonuçlarını yeni bir pencerede gösterir."""
        # Yeni pencere oluştur
        analysis_window = tk.Toplevel(self.app)
        analysis_window.title(f"Proje Analizi - {os.path.basename(file_path)}")
        analysis_window.resizable(True, True)
        
        # Geometri yönetimini kullan
        self.app.load_or_center_window("python_analyzer", analysis_window, 900, 700)
          # Pencere kapatma işleyicisi
        def on_analysis_closing():
            geom = analysis_window.winfo_geometry()
            self.app.db.save_window_geometry("python_analyzer", geom)
            analysis_window.destroy()
        
        analysis_window.protocol("WM_DELETE_WINDOW", on_analysis_closing)
        # ESC tuşu ile pencereyi kapat
        analysis_window.bind("<Escape>", lambda e: on_analysis_closing())
        
        # Ana frame
        main_frame = ttk.Frame(analysis_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook widget (sekmeler)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Proje Özeti sekmesi
        self._create_project_summary_tab(notebook, results)
        
        # Dosyalar sekmesi
        self._create_files_tab(notebook, results)
        
        # İmport Analizi sekmesi
        self._create_project_imports_tab(notebook, results)
        
        # Proje İstatistikleri sekmesi
        self._create_project_stats_tab(notebook, results)
        
        # Yapısal Analiz sekmesi
        self._create_project_structure_tab(notebook, results)
        
        # Hatalar sekmesi (varsa)
        if results['errors']:
            self._create_project_errors_tab(notebook, results)

    def _create_general_info_tab(self, notebook, results):
        """Genel bilgiler sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Genel Bilgi")
        
        # Text widget ile bilgileri göster
        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bilgileri ekle
        info = results['file_info']
        content = f"""DOSYA BİLGİLERİ
{'='*50}

Dosya Adı: {info['name']}
Dosya Boyutu: {info['size']:,} byte ({info['size']/1024:.1f} KB)
Son Değiştirme: {info['modified']}
Tam Yol: {info['path']}

KOD İSTATİSTİKLERİ
{'='*50}

Toplam Satır: {results['code_stats']['total_lines']:,}
Kod Satırları: {results['code_stats']['code_lines']:,}
Yorum Satırları: {results['code_stats']['comment_lines']:,}
Docstring Satırları: {results['code_stats']['docstring_lines']:,}
Boş Satırlar: {results['code_stats']['blank_lines']:,}

YAPISAL BİLGİLER
{'='*50}

Toplam Fonksiyon: {len(results['functions'])}
Toplam Sınıf: {len(results['classes'])}
Toplam İmport: {len(results['imports']['builtin']) + len(results['imports']['third_party']) + len(results['imports']['user_defined'])}
"""
        
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

    def _create_imports_tab(self, notebook, results):
        """İmport analizi sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="İmportlar")
        
        # TreeView ile importları göster
        tree = ttk.Treeview(frame, columns=('module',), show='tree headings')
        tree.heading('#0', text='Kategori')
        tree.heading('module', text='Modül Adı')
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Builtin/Standart Kütüphane
        if results['imports']['builtin']:
            builtin_node = tree.insert('', tk.END, text=f"Standart Kütüphane ({len(results['imports']['builtin'])})", open=True)
            for module in sorted(results['imports']['builtin']):
                tree.insert(builtin_node, tk.END, text='', values=(module,))
        
        # Third-party
        if results['imports']['third_party']:
            third_party_node = tree.insert('', tk.END, text=f"Üçüncü Taraf Kütüphaneler ({len(results['imports']['third_party'])})", open=True)
            for module in sorted(results['imports']['third_party']):
                tree.insert(third_party_node, tk.END, text='', values=(module,))
        
        # User-defined
        if results['imports']['user_defined']:
            user_node = tree.insert('', tk.END, text=f"Kullanıcı Tanımlı Modüller ({len(results['imports']['user_defined'])})", open=True)
            for module in sorted(results['imports']['user_defined']):
                tree.insert(user_node, tk.END, text='', values=(module,))

    def _create_stats_tab(self, notebook, results):
        """Kod istatistikleri sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="İstatistikler")
        
        # Frame içinde istatistikleri göster
        stats_frame = ttk.LabelFrame(frame, text="Satır İstatistikleri")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats = results['code_stats']
        total = stats['total_lines']
        
        if total > 0:
            # İstatistik satırları
            ttk.Label(stats_frame, text=f"Toplam Satır: {total:,}").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Kod Satırları: {stats['code_lines']:,} ({stats['code_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Yorum Satırları: {stats['comment_lines']:,} ({stats['comment_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Docstring Satırları: {stats['docstring_lines']:,} ({stats['docstring_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Boş Satırlar: {stats['blank_lines']:,} ({stats['blank_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
        
        # Özet bilgiler
        summary_frame = ttk.LabelFrame(frame, text="Özet")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(summary_frame, text=f"Toplam Fonksiyon: {len(results['functions'])}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(summary_frame, text=f"Toplam Sınıf: {len(results['classes'])}").pack(anchor=tk.W, padx=10, pady=2)
        
        total_imports = len(results['imports']['builtin']) + len(results['imports']['third_party']) + len(results['imports']['user_defined'])
        ttk.Label(summary_frame, text=f"Toplam İmport: {total_imports}").pack(anchor=tk.W, padx=10, pady=2)

    def _create_structure_tab_DEPRECIATED(self, notebook, results):
        """Fonksiyonlar ve sınıflar sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Yapı")
        
        # TreeView ile yapısal elementleri göster
        tree = ttk.Treeview(frame, columns=('line', 'info'), show='tree headings')
        tree.heading('#0', text='Ad')
        tree.heading('line', text='Satır')
        tree.heading('info', text='Detay')
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Sınıfları ekle
        if results['classes']:
            classes_node = tree.insert('', tk.END, text=f"Sınıflar ({len(results['classes'])})", open=True)
            for cls in sorted(results['classes'], key=lambda x: x['line']):
                cls_info = f"{len(cls['methods'])} method"
                if cls['bases']:
                    cls_info += f", inherit: {', '.join(cls['bases'])}"
                cls_node = tree.insert(classes_node, tk.END, text=cls['name'], values=(cls['line'], cls_info))
                
                # Sınıfın methodlarını ekle
                for method in sorted(cls['methods'], key=lambda x: x['line']):
                    tree.insert(cls_node, tk.END, text=method['name'], values=(method['line'], f"{method['args']} parametre"))
        
        # Bağımsız fonksiyonları ekle
        standalone_functions = [f for f in results['functions'] if not f['is_method']]
        if standalone_functions:
            funcs_node = tree.insert('', tk.END, text=f"Fonksiyonlar ({len(standalone_functions)})", open=True)
            for func in sorted(standalone_functions, key=lambda x: x['line']):
                tree.insert(funcs_node, tk.END, text=func['name'], values=(func['line'], f"{func['args']} parametre"))

    def _create_errors_tab(self, notebook, results):
        """Hatalar sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Hatalar")
        
        # Text widget ile hataları göster
        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hataları ekle
        for i, error in enumerate(results['errors'], 1):
            text_widget.insert(tk.END, f"{i}. {error}\n\n")
        
        text_widget.config(state=tk.DISABLED)

    def _create_project_summary_tab(self, notebook, results):
        """Proje özeti sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Proje Özeti")
        
        # Text widget ile bilgileri göster
        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Proje bilgilerini ekle
        main_file = os.path.basename(results['main_file'])
        project_dir = os.path.dirname(results['main_file'])
        
        content = f"""PROJE ÖZETİ
{'='*60}

Ana Dosya: {main_file}
Proje Dizini: {project_dir}
Toplam Dosya Sayısı: {results['file_count']}

GENEL İSTATİSTİKLER
{'='*60}

Toplam Satır       : {results['project_stats']['total_lines']:,}
Kod Satırları      : {results['project_stats']['code_lines']:,}
Yorum Satırları    : {results['project_stats']['comment_lines']:,}
Docstring Satırları: {results['project_stats']['docstring_lines']:,}
Boş Satırlar       : {results['project_stats']['blank_lines']:,}

Toplam Boyut       : {results['project_stats']['total_size']:,} byte ({results['project_stats']['total_size']/1024:.1f} KB)

YAPISAL BİLGİLER
{'='*60}

Toplam Fonksiyon   : {results['project_structure']['total_functions']}
Toplam Sınıf       : {results['project_structure']['total_classes']}

İMPORT İSTATİSTİKLERİ
{'='*60}

Standart Kütüphane : {len(results['project_imports']['builtin'])}
Üçüncü Taraf       : {len(results['project_imports']['third_party'])}
Kullanıcı Tanımlı  : {len(results['project_imports']['user_defined'])}

DOSYA LİSTESİ
{'='*60}

"""
        
        for i, file_path in enumerate(results['project_files'], 1):
            file_name = os.path.basename(file_path)
            file_stats = results['file_details'][file_path]['code_stats']
            content += f"{i:2d}. {file_name} ({file_stats['total_lines']} satır)\n"
        
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

    def _create_files_tab(self, notebook, results):
        """Dosyalar sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Dosyalar")
        
        # TreeView ile dosyaları göster
        tree = ttk.Treeview(frame, columns=('lines', 'code', 'size'), show='tree headings')
        tree.heading('#0', text='Dosya Adı')
        tree.heading('lines', text='Toplam Satır')
        tree.heading('code', text='Kod Satırları')
        tree.heading('size', text='Boyut (KB)')
        
        # Kolon hizalama
        tree.column('lines', anchor='e')    # Toplam kolonunu sağa yasla
        tree.column('code', anchor='e')
        tree.column('size', anchor='e')

        # Sütun genişlikleri
        tree.column('#0', width=300)
        tree.column('lines', width=100)
        tree.column('code', width=100)
        tree.column('size', width=100)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Ana dosyayı özel olarak işaretle
        for file_path in results['project_files']:
            file_name = os.path.basename(file_path)
            file_stats = results['file_details'][file_path]['code_stats']
            file_size = results['file_details'][file_path]['file_info']['size']
            
            # Ana dosya ise işaretle
            if file_path == results['main_file']:
                file_name = f"★ {file_name} (ANA DOSYA)"
            
            tree.insert('', tk.END, 
                       text=file_name,
                       values=(
                           f"{file_stats['total_lines']:,}",
                           f"{file_stats['code_lines']:,}",
                           f"{file_size/1024:.1f}"
                       ))

    def _create_project_imports_tab(self, notebook, results):
        """Proje import analizi sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="İmportlar")
        
        # TreeView ile importları göster
        tree = ttk.Treeview(frame, columns=('module',), show='tree headings')
        tree.heading('#0', text='Kategori')
        tree.heading('module', text='Modül Adı')
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Builtin/Standart Kütüphane
        if results['project_imports']['builtin']:
            builtin_node = tree.insert('', tk.END, text=f"Standart Kütüphane ({len(results['project_imports']['builtin'])})", open=True)
            for module in results['project_imports']['builtin']:
                tree.insert(builtin_node, tk.END, text='', values=(module,))
        
        # Third-party
        if results['project_imports']['third_party']:
            third_party_node = tree.insert('', tk.END, text=f"Üçüncü Taraf Kütüphaneler ({len(results['project_imports']['third_party'])})", open=True)
            for module in results['project_imports']['third_party']:
                tree.insert(third_party_node, tk.END, text='', values=(module,))
        
        # User-defined
        if results['project_imports']['user_defined']:
            user_node = tree.insert('', tk.END, text=f"Kullanıcı Tanımlı Modüller ({len(results['project_imports']['user_defined'])})", open=True)
            for module in results['project_imports']['user_defined']:
                tree.insert(user_node, tk.END, text='', values=(module,))

    def _create_project_stats_tab(self, notebook, results):
        """Proje kod istatistikleri sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="İstatistikler")
        
        # Frame içinde istatistikleri göster
        stats_frame = ttk.LabelFrame(frame, text="Proje Satır İstatistikleri")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats = results['project_stats']
        total = stats['total_lines']
        
        if total > 0:
            # İstatistik satırları
            ttk.Label(stats_frame, text=f"Toplam Satır: {total:,}").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Kod Satırları: {stats['code_lines']:,} ({stats['code_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Yorum Satırları: {stats['comment_lines']:,} ({stats['comment_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Docstring Satırları: {stats['docstring_lines']:,} ({stats['docstring_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(stats_frame, text=f"Boş Satırlar: {stats['blank_lines']:,} ({stats['blank_lines']/total*100:.1f}%)").pack(anchor=tk.W, padx=10, pady=2)
        
        # Proje özet bilgiler
        summary_frame = ttk.LabelFrame(frame, text="Proje Özeti")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(summary_frame, text=f"Toplam Dosya: {results['file_count']}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(summary_frame, text=f"Toplam Boyut: {stats['total_size']:,} byte ({stats['total_size']/1024:.1f} KB)").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(summary_frame, text=f"Toplam Fonksiyon: {results['project_structure']['total_functions']}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(summary_frame, text=f"Toplam Sınıf: {results['project_structure']['total_classes']}").pack(anchor=tk.W, padx=10, pady=2)
        
        total_imports = len(results['project_imports']['builtin']) + len(results['project_imports']['third_party']) + len(results['project_imports']['user_defined'])
        ttk.Label(summary_frame, text=f"Toplam İmport: {total_imports}").pack(anchor=tk.W, padx=10, pady=2)

        # Dosya bazlı detaylar
        details_frame = ttk.LabelFrame(frame, text="Dosya Detayları")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # TreeView ile dosya detayları
        detail_tree = ttk.Treeview(details_frame, columns=('total', 'code', 'comment', 'blank'), show='tree headings')
        detail_tree.heading('#0', text='Dosya')
        detail_tree.heading('total', text='Toplam')
        detail_tree.heading('code', text='Kod')
        detail_tree.heading('comment', text='Yorum')
        detail_tree.heading('blank', text='Boş')
        
        # Kolon hizalama
        detail_tree.column('total', anchor='e')    # Toplam kolonunu sağa yasla
        detail_tree.column('code', anchor='e')
        detail_tree.column('comment', anchor='e')
        detail_tree.column('blank', anchor='e')

        detail_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=detail_tree.yview)
        detail_tree.configure(yscrollcommand=detail_scrollbar.set)
        
        detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for file_path in results['project_files']:
            file_name = os.path.basename(file_path)
            file_stats = results['file_details'][file_path]['code_stats']
            
            detail_tree.insert('', tk.END,
                             text=file_name,
                             values=(
                                f"{file_stats['total_lines']:,}",    # Bindelik ayıraçlı
                                f"{file_stats['code_lines']:,}",
                                f"{file_stats['comment_lines']:,}",
                                f"{file_stats['blank_lines']:,}"                                 
                             ))

    def _create_project_structure_tab(self, notebook, results):
        """Proje yapısal analiz sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Yapısal Analiz")
        
        # TreeView ile yapısal elementleri göster
        tree = ttk.Treeview(frame, columns=('file', 'line', 'info'), show='tree headings')
        tree.heading('#0', text='Ad')
        tree.heading('file', text='Dosya')
        tree.heading('line', text='Satır')
        tree.heading('info', text='Detay')
        
        # Sütun genişlikleri
        tree.column('#0', width=200)
        tree.column('file', width=150)
        tree.column('line', width=80)
        tree.column('info', width=200)
        
        # Kolon hizalama
        tree.column('line', anchor='e')    # Satır kolonunu sağa yasla

        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Sınıfları ekle
        if results['project_structure']['classes']:
            classes_node = tree.insert('', tk.END, text=f"Sınıflar ({len(results['project_structure']['classes'])})", open=True)
            for cls in sorted(results['project_structure']['classes'], key=lambda x: (x['file'], x['line'])):
                cls_info = f"{len(cls['methods'])} method"
                if cls['bases']:
                    cls_info += f", inherit: {', '.join(cls['bases'])}"
                cls_node = tree.insert(classes_node, tk.END, 
                                     text=cls['name'], 
                                     values=(cls['file'], cls['line'], "    " + cls_info))
                
                # Sınıfın methodlarını ekle
                for method in sorted(cls['methods'], key=lambda x: x['line']):
                    tree.insert(cls_node, tk.END, 
                              text=method['name'], 
                              values=('', method['line'], f"{method['args']} parametre"))
        
        # Bağımsız fonksiyonları ekle
        standalone_functions = [f for f in results['project_structure']['functions'] if not f.get('is_method', False)]
        if standalone_functions:
            funcs_node = tree.insert('', tk.END, text=f"Fonksiyonlar ({len(standalone_functions)})", open=True)
            for func in sorted(standalone_functions, key=lambda x: (x['file'], x['line'])):
                tree.insert(funcs_node, tk.END, 
                          text=func['name'], 
                          values=(func['file'], func['line'], f"{func['args']} parametre"))

    def _create_project_errors_tab(self, notebook, results):
        """Proje hataları sekmesini oluşturur."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Hatalar")
        
        # Text widget ile hataları göster
        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hataları ekle
        for i, error in enumerate(results['errors'], 1):
            text_widget.insert(tk.END, f"{i}. {error}\n\n")
        
        text_widget.config(state=tk.DISABLED)

    def _discover_project_files(self, main_file_path):
        """Ana dosyadan başlayarak tüm kullanıcı tanımlı import dosyalarını keşfeder."""
        discovered_files = set()
        to_process = [main_file_path]
        processed = set()
        
        base_dir = os.path.dirname(main_file_path)
        
        while to_process:
            current_file = to_process.pop(0)
            if current_file in processed:
                continue
                
            processed.add(current_file)
            discovered_files.add(current_file)
            
            # Dosyadaki importları analiz et
            user_imports = self._get_user_defined_imports(current_file, base_dir)
            
            for import_file in user_imports:
                if import_file not in processed and os.path.exists(import_file):
                    to_process.append(import_file)
        
        return sorted(discovered_files)

    def _get_user_defined_imports(self, file_path, base_dir):
        """Dosyadaki kullanıcı tanımlı importları bulur."""
        user_imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content, filename=file_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_file = self._resolve_import_path(alias.name, base_dir)
                            if import_file:
                                user_imports.append(import_file)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_file = self._resolve_import_path(node.module, base_dir)
                            if import_file:
                                user_imports.append(import_file)
                        
                        # from . import veya from .module import durumları
                        elif node.level > 0:  # Relative import
                            for alias in node.names:
                                if alias.name != '*':
                                    # Relative import çözümleme
                                    relative_path = '../' * (node.level - 1) + alias.name
                                    import_file = self._resolve_import_path(relative_path, base_dir)
                                    if import_file:
                                        user_imports.append(import_file)
                        
            except SyntaxError:
                pass  # Syntax hatası varsa bu dosyayı atla
            except Exception:
                pass  # Diğer hatalar için de atla
                
        except (UnicodeDecodeError, FileNotFoundError):
            # Dosya okunamıyorsa farklı encoding'ler dene
            encodings = ['latin1', 'cp1252', 'iso-8859-1']
            content_read = False
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    content_read = True
                    break
                except:
                    continue
        
        return user_imports

    def _resolve_import_path(self, module_name, base_dir):
        """Import adını dosya yoluna çevirir."""
        # Python builtin ve standart kütüphane kontrolü
        builtin_modules = set(sys.builtin_module_names)
        stdlib_modules = {
            'os', 'sys', 'datetime', 'json', 'csv', 'sqlite3', 'tkinter', 'threading',
            'subprocess', 'shutil', 'pathlib', 're', 'math', 'random', 'collections',
            'itertools', 'functools', 'operator', 'time', 'urllib', 'http', 'email',
            'html', 'xml', 'zipfile', 'tarfile', 'gzip', 'pickle', 'hashlib', 'hmac',
            'base64', 'uuid', 'logging', 'unittest', 'doctest', 'argparse', 'configparser',
            'io', 'tempfile', 'glob', 'fnmatch', 'platform', 'socket', 'ssl', 'ftplib',
            'smtplib', 'imaplib', 'poplib', 'telnetlib', 'webbrowser', 'ast', 'inspect'
        }
        
        main_module = module_name.split('.')[0]
        
        if main_module in builtin_modules or main_module in stdlib_modules:
            return None  # Standart kütüphane, bizi ilgilendirmiyor
        
        # Aynı dizinde .py dosyası ara
        possible_paths = [
            os.path.join(base_dir, module_name + '.py'),
            os.path.join(base_dir, module_name, '__init__.py'),
            os.path.join(base_dir, main_module + '.py'),
            os.path.join(base_dir, main_module, '__init__.py')
        ]
        
        # Alt dizinlerde de ara
        module_parts = module_name.split('.')
        if len(module_parts) > 1:
            subdir_path = os.path.join(base_dir, *module_parts[:-1], module_parts[-1] + '.py')
            possible_paths.append(subdir_path)
            
            subdir_init_path = os.path.join(base_dir, *module_parts, '__init__.py')
            possible_paths.append(subdir_init_path)
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        return None

    def _perform_project_analysis(self, main_file_path, all_files):
        """Proje dosyalarının toplu analizini yapar."""
        results = {
            'main_file': main_file_path,
            'project_files': all_files,
            'file_count': len(all_files),
            'file_details': {},
            'project_stats': {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'blank_lines': 0,
                'docstring_lines': 0,
                'total_size': 0
            },
            'project_imports': {
                'builtin': set(),
                'third_party': set(),
                'user_defined': set()
            },
            'project_structure': {
                'total_functions': 0,
                'total_classes': 0,
                'functions': [],
                'classes': []
            },
            'errors': []
        }
        
        # Her dosyayı ayrı ayrı analiz et
        for file_path in all_files:
            try:
                file_analysis = self._perform_single_file_analysis(file_path)
                
                # Dosya detaylarını kaydet
                results['file_details'][file_path] = file_analysis
                
                # Proje istatistiklerini güncelle
                stats = file_analysis['code_stats']
                results['project_stats']['total_lines'] += stats['total_lines']
                results['project_stats']['code_lines'] += stats['code_lines']
                results['project_stats']['comment_lines'] += stats['comment_lines']
                results['project_stats']['blank_lines'] += stats['blank_lines']
                results['project_stats']['docstring_lines'] += stats['docstring_lines']
                results['project_stats']['total_size'] += file_analysis['file_info']['size']
                
                # Import bilgilerini birleştir
                for category in ['builtin', 'third_party', 'user_defined']:
                    results['project_imports'][category].update(file_analysis['imports'][category])
                
                # Yapısal elementleri birleştir
                results['project_structure']['total_functions'] += len(file_analysis['functions'])
                results['project_structure']['total_classes'] += len(file_analysis['classes'])
                
                # Fonksiyon ve sınıf bilgilerini dosya adıyla birlikte kaydet
                for func in file_analysis['functions']:
                    func_copy = func.copy()
                    func_copy['file'] = os.path.basename(file_path)
                    func_copy['full_path'] = file_path
                    results['project_structure']['functions'].append(func_copy)
                
                for cls in file_analysis['classes']:
                    cls_copy = cls.copy()
                    cls_copy['file'] = os.path.basename(file_path)
                    cls_copy['full_path'] = file_path
                    results['project_structure']['classes'].append(cls_copy)
                
                # Hataları topla
                if file_analysis['errors']:
                    results['errors'].extend([f"{os.path.basename(file_path)}: {error}" for error in file_analysis['errors']])
                    
            except Exception as e:
                results['errors'].append(f"{os.path.basename(file_path)}: Analiz hatası - {e}")
        
        # Set'leri listeye çevir
        for category in ['builtin', 'third_party', 'user_defined']:
            results['project_imports'][category] = sorted(list(results['project_imports'][category]))
        
        return results

    def _perform_single_file_analysis(self, file_path):
        """Tek dosyanın detaylı analizini yapar (eski _perform_analysis fonksiyonu)."""
        results = {
            'file_info': {},
            'imports': {
                'builtin': [],
                'third_party': [],
                'user_defined': []
            },
            'code_stats': {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'blank_lines': 0,
                'docstring_lines': 0
            },
            'functions': [],
            'classes': [],
            'errors': []
        }

        # Dosya bilgileri
        file_stat = os.stat(file_path)
        results['file_info'] = {
            'name': os.path.basename(file_path),
            'size': file_stat.st_size,
            'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'path': file_path
        }

        try:
            # Dosyayı oku
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Satır bazlı analiz
            lines = content.split('\n')
            results['code_stats']['total_lines'] = len(lines)
            
            in_multiline_string = False
            string_delimiter = None
            
            for line in lines:
                stripped = line.strip()
                
                # Boş satırlar
                if not stripped:
                    results['code_stats']['blank_lines'] += 1
                    continue
                
                # Çok satırlı string kontrolü
                if '"""' in line or "'''" in line:
                    if not in_multiline_string:
                        in_multiline_string = True
                        string_delimiter = '"""' if '"""' in line else "'''"
                    elif string_delimiter in line:
                        in_multiline_string = False
                        string_delimiter = None
                    results['code_stats']['docstring_lines'] += 1
                elif in_multiline_string:
                    results['code_stats']['docstring_lines'] += 1
                # Yorum satırları
                elif stripped.startswith('#'):
                    results['code_stats']['comment_lines'] += 1
                # Kod satırları
                else:
                    results['code_stats']['code_lines'] += 1

            # AST ile analiz
            try:
                tree = ast.parse(content, filename=file_path)
                self._analyze_ast(tree, results)
            except SyntaxError as e:
                results['errors'].append(f"Sözdizimi hatası: {e}")
            except Exception as e:
                results['errors'].append(f"AST analizi hatası: {e}")

        except UnicodeDecodeError:
            # UTF-8 ile okuyamadıysa farklı encoding'ler dene
            encodings = ['latin1', 'cp1252', 'iso-8859-1']
            content_read = False
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    content_read = True
                    break
                except:
                    continue
            
            if not content_read:
                results['errors'].append("Dosya okunamadı: Desteklenmeyen karakter kodlaması")
        except Exception as e:
            results['errors'].append(f"Dosya okuma hatası: {e}")

        return results

if __name__ == "__main__":
    print("############################################################################################")
    print("   Bu dosya doğrudan çalıştırılamaz, Python Program Yöneticisi Python Analiz modülüdür.")
    print("############################################################################################")

