# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime
import os
from tkinter import messagebox # Hata durumlarında kullanıcıyı bilgilendirmek için

# --- Veritabanı Yönetimi Sınıfı ---
class DatabaseManager:
    """SQLite veritabanı işlemlerini yönetir.
    
    Bu sınıf, uygulama verilerini SQLite veritabanında saklamak ve
    yönetmek için gerekli tüm CRUD işlemlerini sağlar.
    
    Attributes:
        db_path: Veritabanı dosyasının yolu.
        conn: SQLite bağlantı nesnesi.
    """
    def __init__(self, db_path):
        """DatabaseManager'ı başlatır.
        
        Args:
            db_path: Veritabanı dosyasının yolu.
        """
        self.db_path = db_path
        self.conn = None  # Tutarlı olarak conn kullanılıyor
        self._connect()
        self._create_tables()
        self._migrate_favorites_order_index() # Favoriler için sıralama indeksi göçünü yap

    def _connect(self):
        """Veritabanına bağlanır."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Veritabanı bağlantı hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Veritabanına bağlanılamadı:\n{e}\nProgram düzgün çalışmayabilir.")
            self.conn = None

    def _close(self):
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """SQL sorgularını güvenli bir şekilde çalıştırır."""
        if not self.conn:
            print("Veritabanı bağlı değil.")
            return None

        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            if commit:
                self.conn.commit()
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            return cursor
        except sqlite3.Error as e:
            print(f"Veritabanı hatası: {e}\nSorgu: {query}\nParametreler: {params}")
            return None

    def _create_tables(self):
        """Gerekli tabloları oluşturur (eğer yoksa)."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS file_descriptions (
                path TEXT PRIMARY KEY,
                description TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT DEFAULT 'run_normal' NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS themes (
                name TEXT PRIMARY KEY,
                config TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS window_geometry (
                window_name TEXT PRIMARY KEY,
                geometry TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS favorites (
                path TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                alias TEXT,
                order_index INTEGER
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS compression_exclusions (
                folder_path TEXT PRIMARY KEY,
                exclusion_pattern TEXT NOT NULL
            );
            """
        ]
        for query in queries:
            self._execute(query, commit=True)

    def get_setting(self, key, default=None):
        row = self._execute("SELECT value FROM settings WHERE key = ?", (key,), fetchone=True)
        return row['value'] if row else default

    def set_setting(self, key, value):
        self._execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value), commit=True)

    def get_description(self, path):
        """Tek bir dosya için açıklamayı döndürür.
        
        Args:
            path: Dosya yolu.
            
        Returns:
            str veya None: Dosya açıklaması veya None.
        """
        row = self._execute("SELECT description FROM file_descriptions WHERE path = ?", (path,), fetchone=True)
        return row['description'] if row else None

    def get_descriptions_batch(self, paths):
        """Birden fazla dosya için açıklamaları toplu olarak döndürür.
        
        Bu metod, her dosya için ayrı sorgu yapmak yerine tek bir sorgu ile
        tüm açıklamaları alarak performansı artırır.
        
        Args:
            paths: Dosya yollarının listesi.
            
        Returns:
            dict: {dosya_yolu: açıklama} şeklinde sözlük.
        """
        if not paths:
            return {}
        
        # SQL IN clause için placeholder'lar oluştur
        placeholders = ','.join(['?' for _ in paths])
        query = f"SELECT path, description FROM file_descriptions WHERE path IN ({placeholders})"
        rows = self._execute(query, tuple(paths), fetchall=True)
        
        if rows:
            return {row['path']: row['description'] for row in rows}
        return {}

    def set_description(self, path, description):
        """Dosya için açıklama kaydeder veya günceller.
        
        Args:
            path: Dosya yolu.
            description: Kaydedilecek açıklama. None veya boş ise açıklama silinir.
        """
        if description:
             self._execute("INSERT OR REPLACE INTO file_descriptions (path, description) VALUES (?, ?)", (path, description), commit=True)
        else:
             self.delete_description(path)

    def delete_description(self, path):
        """Dosya açıklamasını siler.
        
        Args:
            path: Dosya yolu.
        """
        self._execute("DELETE FROM file_descriptions WHERE path = ?", (path,), commit=True)

    def add_history(self, path, event_type="run_normal"):
        """Çalıştırma geçmişine yeni kayıt ekler.
        
        Args:
            path: Çalıştırılan dosyanın yolu veya işlem açıklaması.
            event_type: Olay türü (varsayılan: "run_normal").
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._execute("INSERT INTO execution_history (path, timestamp, event_type) VALUES (?, ?, ?)",
                      (path, timestamp, event_type), commit=True)

    def get_history(self):
        """Tüm çalıştırma geçmişini döndürür.
        
        Returns:
            list: (zaman_damgası, yol, olay_türü) tuple'larının listesi.
        """
        rows = self._execute("SELECT timestamp, path, event_type FROM execution_history ORDER BY timestamp DESC", fetchall=True)
        return [(row['timestamp'], row['path'], row['event_type']) for row in rows] if rows else []

    def get_history_batch(self, start_date=None, end_date=None, event_types=None, limit=100):
        """Filtrelenmiş çalıştırma geçmişini toplu olarak döndürür.
        
        Args:
            start_date: Başlangıç tarihi (YYYY-MM-DD formatında).
            end_date: Bitiş tarihi (YYYY-MM-DD formatında).
            event_types: Filtrelenecek olay türlerinin listesi.
            limit: Maksimum sonuç sayısı.
            
        Returns:
            list: Filtrelenmiş (zaman_damgası, yol, olay_türü) tuple'ları.
        """
        query = "SELECT timestamp, path, event_type FROM execution_history WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date + " 23:59:59")
        
        if event_types:
            placeholders = ','.join(['?' for _ in event_types])
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self._execute(query, tuple(params), fetchall=True)
        return [(row['timestamp'], row['path'], row['event_type']) for row in rows] if rows else []

    def save_theme(self, name, config_dict):
        config_json = json.dumps(config_dict)
        self._execute("INSERT OR REPLACE INTO themes (name, config) VALUES (?, ?)", (name, config_json), commit=True)

    def get_theme(self, name):
        row = self._execute("SELECT config FROM themes WHERE name = ?", (name,), fetchone=True)
        return json.loads(row['config']) if row else None

    def get_all_theme_names(self):
        rows = self._execute("SELECT name FROM themes ORDER BY name", fetchall=True)
        return [row['name'] for row in rows] if rows else []

    def delete_theme(self, name):
        self._execute("DELETE FROM themes WHERE name = ?", (name,), commit=True)

    def get_active_theme_name(self):
        return self.get_setting("active_theme_name")

    def set_active_theme_name(self, name):
        self.set_setting("active_theme_name", name)

    def save_window_geometry(self, window_name, geometry_string):
        # print(f"🚩 Saving geometry for {window_name}: {geometry_string}")
        self._execute("INSERT OR REPLACE INTO window_geometry (window_name, geometry) VALUES (?, ?)",
                      (window_name, geometry_string), commit=True)
        # print(f"✅ Geometry for {window_name} saved successfully.")

    def get_window_geometry(self, window_name):
        row = self._execute("SELECT geometry FROM window_geometry WHERE window_name = ?", (window_name,), fetchone=True)
        return row['geometry'] if row else None

    def delete_window_geometry(self, window_name):
        self._execute("DELETE FROM window_geometry WHERE window_name = ?", (window_name,), commit=True)

    # --- Favorites ---
    def add_favorite(self, path, alias=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Yeni favoriler her zaman listenin sonuna eklenir.
        max_order_cursor = self._execute("SELECT MAX(order_index) FROM favorites", fetchone=True)
        max_order = -1
        if max_order_cursor and max_order_cursor[0] is not None:
            max_order = max_order_cursor[0]
        new_order_index = max_order + 1

        self._execute("INSERT OR REPLACE INTO favorites (path, timestamp, alias, order_index) VALUES (?, ?, ?, ?)",
                      (path, timestamp, alias, new_order_index), commit=True)

    def remove_favorite(self, path):
        self._execute("DELETE FROM favorites WHERE path = ?", (path,), commit=True)

    def get_favorites(self):
        # order_index'e göre sırala
        rows = self._execute("SELECT path, timestamp, alias, order_index FROM favorites ORDER BY order_index ASC", fetchall=True)
        return [(row['path'], row['timestamp'], row['alias'], row['order_index']) for row in rows] if rows else []

    def is_favorite(self, path):
        row = self._execute("SELECT path FROM favorites WHERE path = ?", (path,), fetchone=True)
        return row is not None

    def update_favorite_alias(self, path, alias):
        # order_index'i koruyarak sadece alias'ı güncelle
        self._execute("UPDATE favorites SET alias = ? WHERE path = ?", (alias, path), commit=True)

    def update_favorites_order(self, ordered_paths):
        """Verilen yolların listesine göre favorilerin order_index'ini günceller."""
        if not self.conn:
            print("Veritabanı bağlı değil.")
            return
        try:
            cursor = self.conn.cursor()
            for new_index, path in enumerate(ordered_paths):
                cursor.execute("UPDATE favorites SET order_index = ? WHERE path = ?", (new_index, path))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Favori sıralaması güncellenirken hata: {e}")
            if self.conn:
                self.conn.rollback()

    def _migrate_favorites_order_index(self):
        """Mevcut favorilere order_index atar (eğer NULL ise)."""
        null_check_cursor = self._execute("SELECT COUNT(*) FROM favorites WHERE order_index IS NULL", fetchone=True)
        if null_check_cursor and null_check_cursor[0] > 0:
            print("Favoriler için order_index göçü yapılıyor...")
            rows = self._execute("SELECT path FROM favorites ORDER BY alias ASC, path ASC", fetchall=True) # Eski sıralama kriteri
            if rows:
                paths_to_order = [row['path'] for row in rows]
                self.update_favorites_order(paths_to_order)
                print(f"{len(paths_to_order)} favori için order_index güncellendi.")

    # --- Compression Exclusions ---
    def get_compression_exclusion(self, folder_path):
        """Belirli bir klasör için kaydedilmiş exclusion pattern'ini döndürür."""
        row = self._execute("SELECT exclusion_pattern FROM compression_exclusions WHERE folder_path = ?", (folder_path,), fetchone=True)
        return row['exclusion_pattern'] if row else None

    def set_compression_exclusion(self, folder_path, exclusion_pattern):
        """Belirli bir klasör için exclusion pattern'ini kaydeder veya günceller."""
        if exclusion_pattern and exclusion_pattern.strip():
            self._execute("INSERT OR REPLACE INTO compression_exclusions (folder_path, exclusion_pattern) VALUES (?, ?)",
                          (folder_path, exclusion_pattern.strip()), commit=True)
        else:
            self._execute("DELETE FROM compression_exclusions WHERE folder_path = ?", (folder_path,), commit=True)

    # --- Global Exclusion List ---
    def get_global_exclusion_list(self):
        """Program genelinde uygulanacak hariç tutma listesini döndürür."""
        return self.get_setting("global_exclusion_list", "")

    def set_global_exclusion_list(self, exclusion_list):
        """Program genelinde uygulanacak hariç tutma listesini kaydeder."""
        self.set_setting("global_exclusion_list", exclusion_list.strip() if exclusion_list else "")

    def __del__(self):
        self._close()