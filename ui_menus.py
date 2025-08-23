# -*- coding: utf-8 -*-

from tkinter import ttk, Menu
import os

class DirectoryContextMenu(Menu):
    def __init__(self, app_instance, root=None):
        """Initialize the directory context menu."""
        super().__init__(root or app_instance, tearoff=0)
        self.app = app_instance

    def show(self, event, item_id, folder_path, folder_name):
        """Show the context menu for the folder."""
        if not os.path.isdir(folder_path):
            return

        # Add menu items
        self.delete(0, 'end')  # Clear existing items
        
        self.add_command(
            label="Özellikler",
            command=lambda: self.app.file_browser.show_folder_properties(folder_path, folder_name)
        )
        self.add_separator()
        self.add_command(
            label="🗜️ Sıkıştır (ZIP)...",
            command=lambda: self.app.action_manager.prompt_compression_options(folder_path)
        )

        # Show the menu at cursor position
        self.tk_popup(event.x_root, event.y_root)
