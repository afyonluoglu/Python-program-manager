"""
Exclusion Utils - Merkezi Hariç Tutma Yardımcı Modülü

Bu modül, program genelinde kullanılan exclusion (hariç tutma) pattern 
işlemlerini merkezi bir yerden yönetir.

Kullanım:
    from exclusion_utils import ExclusionManager
    
    manager = ExclusionManager("*.csv, dist\\*.*, __pycache__")
    
    # Klasör kontrolü
    if manager.should_exclude_dir("dist"):
        print("dist klasörü hariç tutulacak")
    
    # Dosya kontrolü
    if manager.is_file_excluded("data.csv", "C:\\project\\data.csv", "C:\\project"):
        print("data.csv hariç tutulacak")
    
    # Hariç tutulan klasördeki dosya sayısını al
    count = manager.count_files_in_excluded_dir("C:\\project\\dist")
"""

import os
import fnmatch


class ExclusionManager:
    """Hariç tutma pattern'lerini yöneten merkezi sınıf."""
    
    def __init__(self, exclusion_string=""):
        """
        ExclusionManager başlatıcı.
        
        Args:
            exclusion_string: Virgülle ayrılmış exclusion pattern'leri
                             Örnek: "*.csv, dist\\*.*, __pycache__, *env\\*.*"
        """
        self.raw_patterns = []
        self.dir_patterns = []
        self.file_patterns = []
        
        if exclusion_string:
            self.raw_patterns = [p.strip() for p in exclusion_string.split(',') if p.strip()]
            self._parse_patterns()
    
    def _parse_patterns(self):
        """Exclusion pattern'lerini klasör ve dosya pattern'lerine ayırır.
        
        Örnek dönüşümler:
        - 'dist\\*.*' veya 'dist\\*' → klasör pattern'i: 'dist'
        - '*env\\*.*' → klasör pattern'i: '*env'
        - '*.pyc' → dosya pattern'i: '*.pyc'
        - '__pycache__' → klasör pattern'i: '__pycache__'
        """
        self.dir_patterns = []
        self.file_patterns = []
        
        for pattern in self.raw_patterns:
            # Normalize separators
            normalized = pattern.replace('/', os.sep).replace('\\', os.sep)
            
            # Pattern'ı parçalara ayır
            parts = normalized.split(os.sep)
            
            if len(parts) >= 2:
                # 'klasör\\*.*' veya 'klasör\\*' formatı
                # İlk kısım klasör pattern'i
                dir_part = parts[0]
                file_part = parts[-1]
                
                # Klasör pattern'i ekle
                if dir_part and dir_part not in self.dir_patterns:
                    self.dir_patterns.append(dir_part)
                
                # Eğer dosya kısmı sadece * veya *.* değilse, onu da dosya pattern'i olarak ekle
                if file_part and file_part not in ('*', '*.*'):
                    if file_part not in self.file_patterns:
                        self.file_patterns.append(file_part)
            else:
                # Tek parça - dosya pattern'i mi klasör pattern'i mi?
                single_pattern = parts[0]
                if '*' in single_pattern and '.' in single_pattern:
                    # *.pyc gibi - dosya pattern'i
                    if single_pattern not in self.file_patterns:
                        self.file_patterns.append(single_pattern)
                else:
                    # __pycache__ gibi - hem klasör hem dosya olabilir
                    if single_pattern not in self.dir_patterns:
                        self.dir_patterns.append(single_pattern)
                    if single_pattern not in self.file_patterns:
                        self.file_patterns.append(single_pattern)
    
    def should_exclude_dir(self, dir_name):
        """Klasörün hariç tutulup tutulmayacağını kontrol eder.
        
        Args:
            dir_name: Klasör adı (sadece isim, yol değil)
        
        Returns:
            bool: Klasör hariç tutulacaksa True
        """
        if not self.dir_patterns:
            return False
        
        for pattern in self.dir_patterns:
            if fnmatch.fnmatch(dir_name.lower(), pattern.lower()):
                return True
        return False
    
    def should_exclude_file(self, file_name):
        """Dosyanın sadece dosya adına göre hariç tutulup tutulmayacağını kontrol eder.
        
        Args:
            file_name: Dosya adı (sadece isim, yol değil)
        
        Returns:
            bool: Dosya hariç tutulacaksa True
        """
        if not self.file_patterns:
            return False
        
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(file_name.lower(), pattern.lower()):
                return True
        return False
    
    def is_file_excluded(self, file_name, file_path, root_folder):
        """Dosyanın hariç tutulup tutulmayacağını tam olarak kontrol eder.
        
        Bu metod hem dosya adı pattern'lerini hem de yol içindeki
        klasör isimlerini kontrol eder.
        
        Args:
            file_name: Dosya adı
            file_path: Dosyanın tam yolu
            root_folder: Ana klasör yolu (göreceli yol hesabı için)
        
        Returns:
            bool: Dosya hariç tutulacaksa True
        """
        # Önce dosya adı pattern'i kontrol et
        if self.should_exclude_file(file_name):
            return True
        
        # Sonra yol içindeki klasörleri kontrol et
        try:
            rel_path = os.path.relpath(file_path, root_folder)
            path_parts = rel_path.replace('/', os.sep).replace('\\', os.sep).split(os.sep)
            
            # Son kısım dosya adı, onu atla ve klasörleri kontrol et
            for part in path_parts[:-1]:
                if self.should_exclude_dir(part):
                    return True
        except ValueError:
            # Farklı sürücülerdeki yollar için
            pass
        
        return False
    
    def count_files_in_dir(self, dir_path):
        """Belirtilen klasördeki toplam dosya sayısını döndürür.
        
        Bu metod alt klasörler dahil tüm dosyaları sayar.
        
        Args:
            dir_path: Klasör yolu
        
        Returns:
            int: Toplam dosya sayısı
        """
        count = 0
        try:
            for _, _, files in os.walk(dir_path):
                count += len(files)
        except (PermissionError, OSError):
            pass
        return count
    
    def get_debug_info(self):
        """Debug bilgilerini döndürür."""
        return {
            "raw_patterns": self.raw_patterns,
            "dir_patterns": self.dir_patterns,
            "file_patterns": self.file_patterns
        }
    
    def has_patterns(self):
        """Pattern tanımlanmış mı kontrol eder."""
        return bool(self.raw_patterns)
    
    def __repr__(self):
        return f"ExclusionManager(dirs={self.dir_patterns}, files={self.file_patterns})"
