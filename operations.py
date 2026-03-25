# -*- coding: utf-8 -*-

import os
import zipfile
import datetime
import threading # Bu modülde doğrudan kullanılmayacak, app_gui.py çağıracak
import shutil
import tempfile
import fnmatch
import subprocess
import platform

from exclusion_utils import ExclusionManager # Merkezi exclusion yönetimi

# --- Sıkıştırma İşlemleri ---
def perform_compression_in_thread(app_instance, abs_source_folder_path, include_subfolders,
                                  abs_zip_file_path, normcase_abs_zip_file_path,
                                  abs_backup_dir_path, normcase_abs_backup_dir_path, folder_name,
                                  backup_dir_name, file_pattern="*.*", exclusion_pattern=""):
    """Sıkıştırma işlemini ayrı bir iş parçacığında gerçekleştirir."""
    
    # ExclusionManager oluştur
    exclusion_manager = ExclusionManager(exclusion_pattern)
    
    debug_info = exclusion_manager.get_debug_info()
    print(f"🔧 DEBUG: Sıkıştırma thread başladı")
    print(f"🔧 DEBUG: Klasör pattern'leri: {debug_info['dir_patterns']}")
    print(f"🔧 DEBUG: Dosya pattern'leri: {debug_info['file_patterns']}")
    
    try:
        with zipfile.ZipFile(abs_zip_file_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            if include_subfolders:
                for root, dirs, files in os.walk(abs_source_folder_path, topdown=True):
                    abs_current_root = os.path.abspath(root)
                    if backup_dir_name in dirs:
                        potential_backup_path_in_dirs = os.path.abspath(os.path.join(abs_current_root, backup_dir_name))
                        if os.path.normcase(potential_backup_path_in_dirs) == normcase_abs_backup_dir_path:
                            dirs.remove(backup_dir_name)
                    
                    # Hariç tutulan klasörleri dirs listesinden çıkar
                    dirs_to_remove = []
                    for dir_name in dirs:
                        if exclusion_manager.should_exclude_dir(dir_name):
                            dirs_to_remove.append(dir_name)
                            rel_dir_path = os.path.relpath(os.path.join(abs_current_root, dir_name), abs_source_folder_path)
                            print(f"🔧 DEBUG: Klasör hariç tutuluyor: {rel_dir_path}")
                    
                    for d in dirs_to_remove:
                        dirs.remove(d)
                    
                    for file_name in files:
                        if fnmatch.fnmatch(file_name, file_pattern): # Dosya deseni kontrolü
                            file_path_to_add = os.path.abspath(os.path.join(abs_current_root, file_name))
                            if os.path.normcase(file_path_to_add) == normcase_abs_zip_file_path:
                                continue
                            # Exclusion kontrolü
                            if exclusion_manager.should_exclude_file(file_name):
                                continue
                            arcname = os.path.relpath(file_path_to_add, abs_source_folder_path)
                            zf.write(file_path_to_add, arcname)
            else:
                for item_name in os.listdir(abs_source_folder_path):
                    item_path_to_check = os.path.join(abs_source_folder_path, item_name)
                    abs_item_path_to_check = os.path.abspath(item_path_to_check)
                    if os.path.normcase(abs_item_path_to_check) == normcase_abs_backup_dir_path:
                        continue
                    if os.path.normcase(abs_item_path_to_check) == normcase_abs_zip_file_path:
                        continue
                    if os.path.isfile(abs_item_path_to_check):
                        if fnmatch.fnmatch(item_name, file_pattern): # Dosya deseni kontrolü
                            # Exclusion kontrolü
                            if exclusion_manager.should_exclude_file(item_name):
                                continue
                            zf.write(abs_item_path_to_check, item_name)
        
        print(f"🔧 DEBUG: Sıkıştırma tamamlandı: {abs_zip_file_path}")
        app_instance.after(0, app_instance._handle_compression_success, folder_name, abs_zip_file_path, abs_backup_dir_path)

    except Exception as e:
        print(f"🔧 DEBUG: Sıkıştırma hatası: {e}")
        app_instance.after(0, app_instance._handle_compression_error, folder_name, e, abs_zip_file_path)

# --- EXE'ye Çevirme İşlemleri ---
def perform_exe_conversion_in_thread(app_instance, py_file_path, pyinstaller_executable):
    """PyInstaller kullanarak .py dosyasını .exe'ye çevirir."""
    py_file_dir = os.path.dirname(py_file_path)
    py_file_basename = os.path.basename(py_file_path)
    py_file_name_no_ext = os.path.splitext(py_file_basename)[0]
    
    temp_build_dir = None
    try:
        temp_build_dir = tempfile.mkdtemp(prefix="py_manager_exe_build_")
        cmd = [
            pyinstaller_executable, '--onefile', '--noconfirm', '--clean',
            '--distpath', py_file_dir,
            '--workpath', temp_build_dir,
            '--specpath', temp_build_dir,
            '--name', py_file_name_no_ext,
            '--log-level', 'WARN',
            py_file_path
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True, check=False, encoding='utf-8', 
                                 creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)

        if process.returncode == 0:
            exe_name = f"{py_file_name_no_ext}.exe"
            final_exe_path = os.path.join(py_file_dir, exe_name)
            if os.path.exists(final_exe_path):
                app_instance.after(0, app_instance._handle_exe_conversion_success, py_file_basename, final_exe_path)
            else:
                error_msg = f"PyInstaller başarıyla tamamlandı ancak beklenen EXE dosyası ({final_exe_path}) bulunamadı.\n\nPyInstaller Çıktısı:\n{process.stdout}\n{process.stderr}"
                app_instance.after(0, app_instance._handle_exe_conversion_error, py_file_basename, error_msg)
        else:
            error_msg = f"PyInstaller hatası (Kod: {process.returncode}):\n{process.stderr}\n\nStdout:\n{process.stdout}"
            app_instance.after(0, app_instance._handle_exe_conversion_error, py_file_basename, error_msg)

    except Exception as e:
        app_instance.after(0, app_instance._handle_exe_conversion_error, py_file_basename, f"EXE çevirme sırasında beklenmedik hata: {e}")
    finally:
        if temp_build_dir and os.path.isdir(temp_build_dir):
            shutil.rmtree(temp_build_dir, ignore_errors=True)
        app_instance.after(0, app_instance._finalize_exe_conversion_ui)

# --- Dosya Arama İşlemleri ---
def perform_search_in_thread_OLD(app_instance, pattern, root_folder):
    """Belirtilen desene göre dosyaları arar."""
    found_files_details = []
    pattern_lower = pattern.lower() # Kullanıcının girdiği desen küçük harfe çevriliyor

    try:
        for dirpath, _, filenames in os.walk(root_folder):
            for filename in filenames:
                # fnmatch deseni zaten küçük harfli (pattern_lower)
                # Dosya adını da küçük harfe çevirerek tutarlı eşleşme sağla
                if fnmatch.fnmatch(filename.lower(), pattern_lower): 
                    file_path = os.path.join(dirpath, filename)
                    filename_actual_lower = filename.lower() # Uzantı kontrolü için dosya adının küçük harfli hali
                    file_type_tag = "other_file" # Varsayılan etiket, eşleşen tüm dosyalar için

                    if filename_actual_lower.endswith(".py"):
                        file_type_tag = "python_file"
                    elif filename_actual_lower.endswith(".exe"):
                        file_type_tag = "exe_file"
                    elif filename_actual_lower.endswith(".zip"):
                        file_type_tag = "zip_file"
                    elif filename_actual_lower.endswith(".db"):
                        file_type_tag = "db_file"
                    # Diğer durumlar için file_type_tag "other_file" olarak kalır.

                    found_files_details.append((file_path, file_type_tag))
    except Exception as e:
        print(f"Arama sırasında hata: {e}")
        app_instance.after(0, app_instance._handle_search_error, e)
        return

    app_instance.after(0, app_instance._show_search_results, found_files_details, pattern, root_folder)

def perform_search_in_thread(app, search_pattern, search_root_folder, file_size=None, size_operator=None, search_in_excluded=False):
    """Dosya aramayı thread içinde gerçekleştirir ve dosya boyutu filtresi uygular.
    
    Args:
        search_in_excluded: True ise hariç tutulan klasör ve dosyalarda da arar
    """
    try:
        found_files_details = []
        
        # ExclusionManager oluştur
        global_exclusion = app.db.get_global_exclusion_list() or ""
        exclusion_manager = ExclusionManager(global_exclusion)
        
        print(f"🔧 DEBUG: Dosya arama başladı - search_in_excluded: {search_in_excluded}")
        
        # Dosyaları tarar
        for root, dirs, files in os.walk(search_root_folder, topdown=True):
            # Hariç tutulan klasörleri atla (eğer search_in_excluded False ise)
            if not search_in_excluded:
                dirs[:] = [d for d in dirs if not exclusion_manager.should_exclude_dir(d)]
            
            for file in files:
                # Dosya adı desenini kontrol et
                if fnmatch.fnmatch(file.lower(), search_pattern.lower()):
                    file_path = os.path.join(root, file)
                    
                    # Hariç tutulan dosyaları atla (eğer search_in_excluded False ise)
                    if not search_in_excluded and exclusion_manager.is_file_excluded(file, file_path, search_root_folder):
                        continue
                    
                    # Dosya boyutu kontrolü (eğer belirtilmişse)
                    if file_size is not None:
                        try:
                            file_size_kb = os.path.getsize(file_path) / 1024  # KB cinsine çevir
                            
                            if size_operator == "büyük" and file_size_kb <= file_size:
                                continue
                            elif size_operator == "eşit" and abs(file_size_kb - file_size) > 0.1:  # 0.1 KB tolerans
                                continue
                            elif size_operator == "küçük" and file_size_kb >= file_size:
                                continue
                        except OSError:
                            continue  # Dosya boyutu alınamıyorsa atla
                    
                    try:
                        # Dosya detaylarını topla
                        stat = os.stat(file_path)
                        file_size_bytes = stat.st_size
                        file_size_kb = round(file_size_bytes / 1024, 2)
                        modification_time = datetime.datetime.fromtimestamp(stat.st_mtime)
                        
                        found_files_details.append({
                            'path': file_path,
                            'size_kb': file_size_kb,
                            'modified': modification_time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except OSError:
                        continue  # Dosya bilgileri alınamıyorsa atla
        
        print(f"🔧 DEBUG: Dosya arama tamamlandı - {len(found_files_details)} dosya bulundu")
        
        # Ana thread'e sonucu gönder
        def show_results():
            app.search_manager._show_search_results(found_files_details, search_pattern, search_root_folder)
        
        app.after(0, show_results)
        
    except Exception as e:
        # Hata mesajını yakalayıp güvenli şekilde gönder
        error_message = str(e)
        def handle_error():
            app.search_manager._handle_search_error(error_message)
        
        app.after(0, handle_error)

# --- Kelime Arama İşlemleri ---
def perform_word_search_in_thread(app, search_word, search_root_folder, file_size=None, size_operator=None, search_in_excluded=False):
    """Kelime aramayı thread içinde gerçekleştirir ve dosya boyutu filtresi uygular.
    
    Args:
        search_in_excluded: True ise hariç tutulan klasör ve dosyalarda da arar
    """
    try:
        found_items = []
        
        # ExclusionManager oluştur
        global_exclusion = app.db.get_global_exclusion_list() or ""
        exclusion_manager = ExclusionManager(global_exclusion)
        
        print(f"🔧 DEBUG: Kelime arama başladı - search_in_excluded: {search_in_excluded}")
        
        # Python dosyalarını tarar
        for root, dirs, files in os.walk(search_root_folder, topdown=True):
            # Hariç tutulan klasörleri atla (eğer search_in_excluded False ise)
            if not search_in_excluded:
                dirs[:] = [d for d in dirs if not exclusion_manager.should_exclude_dir(d)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Hariç tutulan dosyaları atla (eğer search_in_excluded False ise)
                    if not search_in_excluded and exclusion_manager.is_file_excluded(file, file_path, search_root_folder):
                        continue
                    
                    # Dosya boyutu kontrolü (eğer belirtilmişse)
                    if file_size is not None:
                        try:
                            file_size_kb = os.path.getsize(file_path) / 1024  # KB cinsine çevir
                            
                            if size_operator == "büyük" and file_size_kb <= file_size:
                                continue
                            elif size_operator == "eşit" and abs(file_size_kb - file_size) > 0.1:  # 0.1 KB tolerans
                                continue
                            elif size_operator == "küçük" and file_size_kb >= file_size:
                                continue
                        except OSError:
                            continue  # Dosya boyutu alınamıyorsa atla
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            if search_word.lower() in line.lower():
                                # UI_dialogs.py'nin beklediği tuple formatında ekle
                                found_items.append((file_path, line_num, line.strip()))
                    except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                        continue  # Dosya okunamıyorsa atla
        
        print(f"🔧 DEBUG: Kelime arama tamamlandı - {len(found_items)} eşleşme bulundu")
        
        # Ana thread'e sonucu gönder
        def show_word_results():
            app.search_manager._show_word_search_results(found_items, search_word, search_root_folder)
        
        app.after(0, show_word_results)
        
    except Exception as e:
        # Hata mesajını yakalayıp güvenli şekilde gönder
        error_message = str(e)
        def handle_word_error():
            app.search_manager._handle_word_search_error(error_message)
        
        app.after(0, handle_word_error)