import tkinter as tk
from tkinter import ttk

class ColoredContextMenu:
    """Renkli simgeler ve modern görünümlü context menu."""
    
    def __init__(self, parent):
        self.parent = parent
        self.menu_window = None
        self.items = []
    
    def add_command(self, label, command, color="#000000", bg_color="#FFFFFF", hover_color="#E3F2FD"):
        """Renkli komut ekler."""
        self.items.append({
            'type': 'command',
            'label': label,
            'command': command,
            'color': color,
            'bg_color': bg_color,
            'hover_color': hover_color
        })
    
    def add_separator(self):
        """Ayırıcı ekler."""
        self.items.append({'type': 'separator'})
    
    def popup(self, x, y):
        """Menüyü belirtilen koordinatlarda gösterir."""
        if self.menu_window:
            self.menu_window.destroy()
        
        self.menu_window = tk.Toplevel(self.parent)
        self.menu_window.wm_overrideredirect(True)
        self.menu_window.configure(bg="#F0F0F0", relief="raised", bd=1)
        
        # Pencereyi konumlandır
        self.menu_window.geometry(f"+{x}+{y}")
        
        for i, item in enumerate(self.items):
            if item['type'] == 'command':
                frame = tk.Frame(self.menu_window, bg=item['bg_color'])
                frame.pack(fill=tk.X, padx=1, pady=1)
                
                label = tk.Label(frame, 
                               text=item['label'],
                               font=("Segoe UI Emoji", 9),
                               fg=item['color'],
                               bg=item['bg_color'],
                               anchor='w',
                               padx=10, pady=5)
                label.pack(fill=tk.X)
                
                # Hover efekti
                def on_enter(e, frame=frame, label=label, hover_bg=item['hover_color']):
                    frame.configure(bg=hover_bg)
                    label.configure(bg=hover_bg)
                
                def on_leave(e, frame=frame, label=label, orig_bg=item['bg_color']):
                    frame.configure(bg=orig_bg)
                    label.configure(bg=orig_bg)
                
                def on_click(e, cmd=item['command']):
                    self.menu_window.destroy()
                    cmd()
                
                label.bind("<Enter>", on_enter)
                label.bind("<Leave>", on_leave)
                label.bind("<Button-1>", on_click)
                
            elif item['type'] == 'separator':
                sep = tk.Frame(self.menu_window, height=1, bg="#CCCCCC")
                sep.pack(fill=tk.X, padx=5, pady=2)
        
        # Menü dışına tıklandığında kapat
        def close_menu(event=None):
            if self.menu_window:
                self.menu_window.destroy()
                self.menu_window = None
        
        # Biraz gecikme ile bind et
        self.parent.after(100, lambda: self.parent.bind("<Button-1>", close_menu, add="+"))
        self.menu_window.bind("<FocusOut>", close_menu)
        
        # Focus'u menu'ye ver
        self.menu_window.focus_set()
    
    def clear(self):
        """Menü öğelerini temizler."""
        self.items.clear()