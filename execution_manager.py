# -*- coding: utf-8 -*-

import tkinter as tk # Sadece messagebox için
from tkinter import messagebox
import os
import subprocess
import sys
import platform
import pygame # For playing MP3 files

class ExecutionManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self._pygame_mixer_initialized = False
        self._pygame_display_initialized = False
        self.current_mp3_path = None
        self.is_mp3_playing = False
        self.is_mp3_paused = False
        self.mp3_duration_sec = 0
        self.mp3_start_time_for_get_pos = 0.0 # Son play() komutundaki 'start' parametresinin saniye cinsinden değeri

    def _initialize_pygame_audio(self):
        """Initializes Pygame and its mixer if not already initialized."""
        if not self._pygame_display_initialized:
            pygame.init() # Initializes all pygame modules
            # A display is often needed for pygame events/sound to work reliably
            # We can create a minimal, non-visible (or quickly hidden) display
            pygame.display.set_mode((1, 1), pygame.NOFRAME) # Minimal display
            self._pygame_display_initialized = True
        if not self._pygame_mixer_initialized:
            pygame.mixer.init() # Initialize mixer with default settings
            self._pygame_mixer_initialized = True

    def run_python_file(self, file_path, source=None):
        """Belirtilen Python dosyasını çalıştırır ve hataları yakalar."""
        if not os.path.exists(file_path):
             messagebox.showerror("Hata", f"Dosya bulunamadı:\n{file_path}", parent=self.app)
             return
        try:
            event_type = "run_search" if source == "search" else "run_normal"
            if source == "favorites":
                event_type = "run_favorite"
            mesaj = "Python dosyası çalıştırıldı:" if source != "editor" else "Python dosyası 'editörden' çalıştırıldı:"
            self.app.db.add_history(f"{mesaj} {file_path}", event_type=event_type)

            print(f"🚩 Çalıştırılıyor: {sys.executable} {file_path}")
            # subprocess.run yerine subprocess.Popen kullanarak programın eş zamanlı çalışmasını sağla
            # Popen ile capture_output kullanmak daha karmaşıktır ve ayrı bir thread veya non-blocking okuma gerektirir.
            # Basitlik adına, Popen ile çıktıyı yakalamadan sadece programı başlatıyoruz.
            # Eğer çıktı veya hata yakalama istenirse, bu kısım daha detaylı ele alınmalıdır.
            process = subprocess.Popen(
                [sys.executable, file_path],
                cwd=os.path.dirname(file_path),
                # stderr=subprocess.PIPE, # Hata çıktısını yakalamak isterseniz
                # stdout=subprocess.PIPE, # Standart çıktıyı yakalamak isterseniz
                # text=True, # Çıktıyı metin olarak almak isterseniz (Popen ile farklı kullanılır)
                # encoding='utf-8' # Çıktı yakalanıyorsa encoding belirtmek iyi olur
                # creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0 # Yeni pencere açılmasını engellemek için (isteğe bağlı)
            )

            # Popen kullanıldığında, programın bitmesini beklemiyoruz.
            # Bu nedenle returncode kontrolü ve çıktı/hata yakalama kısmı kaldırılmalıdır
            # veya ayrı bir iş parçacığında (thread) veya non-blocking yöntemlerle yapılmalıdır.
            # Şimdilik sadece programın başlatıldığı bilgisini veriyoruz.
            print(f"✅ Program başlatıldı (eş zamanlı): {file_path}")
            # İsteğe bağlı: Başlatılan process objesini saklayıp daha sonra kontrol edebilirsiniz.
            # self.app.running_processes.append(process) # App sınıfında bir liste tutulabilir

        except FileNotFoundError:
             messagebox.showerror("Hata", f"Python yorumlayıcısı bulunamadı:\n{sys.executable}\nLütfen Python kurulumunuzu kontrol edin.", parent=self.app)
        except Exception as e:
            messagebox.showerror("Hata", f"Program çalıştırılamadı:\n{e}", parent=self.app)

    def run_executable_file(self, file_path, source=None):
        """Belirtilen çalıştırılabilir dosyayı (.exe) çalıştırır."""
        if not os.path.exists(file_path):
            messagebox.showerror("Hata", f"Dosya bulunamadı:\n{file_path}", parent=self.app)
            return
        try:
            event_type = "run_search" if source == "search" else "run_normal"
            self.app.db.add_history(f"Çalıştırıldı: {file_path}", event_type=event_type)

            if platform.system() == "Windows":
                os.startfile(file_path)
            else:
                subprocess.Popen([file_path], cwd=os.path.dirname(file_path))
            print(f"☑️ Başarıyla çalıştırıldı (veya başlatıldı): {file_path}")
        except FileNotFoundError:
            messagebox.showerror("Hata", f"Dosya bulunamadı veya başlatılamadı:\n{file_path}", parent=self.app)
        except Exception as e:
            messagebox.showerror("Hata", f"'{os.path.basename(file_path)}' çalıştırılırken bir hata oluştu:\n{e}", parent=self.app)

    def open_file_with_default_app(self, file_path):
        """Belirtilen dosyayı işletim sisteminin varsayılan uygulamasıyla açar."""
        if not os.path.exists(file_path):
            messagebox.showerror("Hata", f"Dosya bulunamadı:\n{file_path}", parent=self.app)
            return
        try:
            self.app.db.add_history(f"Varsayılanla Açıldı: {file_path}", event_type="open_default")
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin": # macOS
                subprocess.call(['open', file_path])
            elif system == "Linux":
                subprocess.call(['xdg-open', file_path])
            else:
                messagebox.showinfo("Desteklenmiyor",
                                    f"'{system}' işletim sistemi için varsayılan uygulama ile açma özelliği şu anda desteklenmiyor.",
                                    parent=self.app)
                return # Başarı mesajı gösterme
            print(f"☑️ '{os.path.basename(file_path)}' varsayılan uygulama ile açıldı/açılmaya çalışıldı.")
        except FileNotFoundError:
            # Bu genellikle 'open' veya 'xdg-open' komutları bulunamadığında olur.
            messagebox.showerror("Hata", f"Dosyayı açmak için gerekli komut bulunamadı. Sistem yapılandırmanızı kontrol edin.", parent=self.app)
        except Exception as e:
            messagebox.showerror("Hata", f"'{os.path.basename(file_path)}' açılırken bir hata oluştu:\n{e}", parent=self.app)

    def _get_mp3_duration(self, file_path):
        """Helper to get MP3 duration. Returns 0 if error."""
        try:
            # Load as a Sound object to get length, then free it
            temp_sound = pygame.mixer.Sound(file_path)
            duration = temp_sound.get_length()
            del temp_sound
            return duration
        except pygame.error as e:
            print(f"❗ MP3 süresi alınırken Pygame hatası ({file_path}): {e}")
            # messagebox.showwarning("MP3 Bilgisi", f"'{os.path.basename(file_path)}' dosyasının süresi alınamadı.\nSebep: {e}", parent=self.app)
            return 0 # Duration unknown
        except Exception as e:
            print(f"❗ MP3 süresi alınırken genel hata ({file_path}): {e}")
            return 0

    def play_mp3_file(self, file_path):
        """Plays the specified MP3 file."""
        if not os.path.exists(file_path):
            messagebox.showerror("Hata", f"MP3 dosyası bulunamadı:\n{file_path}", parent=self.app)
            return
        try:
            if self.is_mp3_playing: # Başka bir MP3 çalıyorsa durdur
                self.stop_mp3()

            self._initialize_pygame_audio()
            
            self.mp3_duration_sec = self._get_mp3_duration(file_path)
            if self.mp3_duration_sec == 0 and pygame.mixer.get_init(): # If duration couldn't be fetched but mixer is fine
                messagebox.showwarning("MP3 Bilgisi",
                                       f"'{os.path.basename(file_path)}' dosyasının toplam süresi alınamadı.\n"
                                       "Kaydırma çubuğu düzgün çalışmayabilir.", parent=self.app)

            pygame.mixer.music.load(file_path)
            # Müziği en baştan başlat
            pygame.mixer.music.play(start=0.0) # loops=0 varsayılan değerdir
            self.mp3_start_time_for_get_pos = 0.0
            
            self.current_mp3_path = file_path
            self.is_mp3_playing = True
            self.is_mp3_paused = False
            
            self.app.show_mp3_controls(self.mp3_duration_sec, os.path.basename(file_path))
            self.app.db.add_history(f"MP3 çalındı: {file_path}, event_type='play_mp3'")
        except pygame.error as e:
            messagebox.showerror("MP3 Çalma Hatası", f"'{os.path.basename(file_path)}' çalınırken bir hata oluştu:\n{e}", parent=self.app)
            self.app.hide_mp3_controls()
        except Exception as e:
            messagebox.showerror("Hata", f"MP3 dosyası işlenirken beklenmedik bir hata oluştu:\n{e}", parent=self.app)
            self.app.hide_mp3_controls()

    def toggle_mp3_play_pause(self):
        if not self.is_mp3_playing:
            return
        if self.is_mp3_paused:
            pygame.mixer.music.unpause()
            self.is_mp3_paused = False
            self.app.update_mp3_play_pause_button_state(paused=False)
            # Duraklatmayı kaldırdığımızda, mp3_start_time_for_get_pos değişmez,
            # get_pos() kaldığı yerden (son play() komutuna göre) devam eder.
        else:
            pygame.mixer.music.pause()
            self.is_mp3_paused = True
            self.app.update_mp3_play_pause_button_state(paused=True)

    def stop_mp3(self):
        if self.is_mp3_playing or pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload() # Unload the music to free resources
        self.is_mp3_playing = False
        self.is_mp3_paused = False
        self.current_mp3_path = None
        self.mp3_duration_sec = 0
        self.mp3_start_time_for_get_pos = 0.0 # Durdurulduğunda sıfırla
        self.app.hide_mp3_controls()

    def seek_mp3(self, position_seconds):
        if self.is_mp3_playing and self.mp3_duration_sec > 0: # is_mp3_playing, bir parçanın yüklü ve aktif olduğu anlamına gelir (çalıyor veya duraklatılmış olabilir)
            try:
                # Ensure position is within bounds
                # Sürenin çok az öncesine ayarlamak, bazı MP3'lerde son saniyede bitmeme sorunlarını engelleyebilir.
                pos_sec = max(0.0, min(float(position_seconds), self.mp3_duration_sec - 0.001 if self.mp3_duration_sec > 0.001 else 0.0))
                
                # play(start=...) mevcut çalmayı durdurur ve yenisini belirtilen saniyeden başlatır.
                pygame.mixer.music.play(start=pos_sec)
                self.mp3_start_time_for_get_pos = pos_sec
                
                # play() komutundan sonra müzik çalmaya başlar. Eğer kullanıcı müziği duraklatmışsa,
                # yeni konumda tekrar duraklatmamız gerekir.
                # self.is_mp3_paused bayrağı, kullanıcının istediği durumu yansıtır.
                if self.is_mp3_paused: # Eğer kullanıcı müziği duraklatmışsa, yeni konumda duraklatılmış kalsın.
                    pygame.mixer.music.pause()
                    # self.is_mp3_paused zaten True olduğu için tekrar ayarlamaya gerek yok.
                else: # Eğer kullanıcı müziği çalıyorsa, şimdi yeni konumdan çalıyor.
                    self.is_mp3_paused = False # Bayrağımızın duraklatılmamış olduğunu teyit edelim.

            except pygame.error as e:
                print(f"❗ MP3 atlama hatası: {e}")
            except Exception as e_gen: # float dönüşümü gibi diğer olası hataları yakala
                print(f"❗ MP3 atlama sırasında genel hata: {e_gen}")

    def get_mp3_current_time_sec(self):
        if self.is_mp3_playing: # Bu, hem çalıyor hem de duraklatılmış durumları kapsar
            # pygame.mixer.music.get_pos(), müziğin çalmaya başladığı andan itibaren geçen milisaniyeyi döndürür.
            # Duraklatılmışsa, duraklatıldığı zamandaki değeri döndürür.
            # Bu her zaman son pygame.mixer.music.play() komutunun 'start' parametresine göredir.
            elapsed_ms = pygame.mixer.music.get_pos()
            if elapsed_ms == -1: # Hata veya çalma durumu yoksa
                print("❗ UYARI: pygame.mixer.music.get_pos() -1 döndürdü (is_mp3_playing True iken).")
                # Eğer duraklatılmamışsa ve -1 ise, muhtemelen çalma bitti veya durdu.
                return self.mp3_duration_sec if self.mp3_duration_sec > 0 and not self.is_mp3_paused else self.mp3_start_time_for_get_pos

            current_absolute_time = self.mp3_start_time_for_get_pos + (elapsed_ms / 1000.0)
            
            # Mevcut zamanın süreyi aşmamasını sağla (küçük zamanlama sorunları veya get_pos'un sonda davranışı nedeniyle olabilir)
            if self.mp3_duration_sec > 0:
                return min(current_absolute_time, self.mp3_duration_sec)
            return current_absolute_time
            
        return 0.0 # Varsayılan olarak, "çalmıyor" kabul edilirse 0.0 döndür

    def is_mp3_still_busy(self):
        return pygame.mixer.music.get_busy()