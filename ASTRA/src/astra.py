# astra.py
import os
import sys
import tkinter as tk
from intro import IntroFrame
from main import MainFrame
from PIL import ImageTk, Image


def resource_path(self, relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller stores files in a temp folder called _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        try:
            icon_image = Image.open(resource_path('logo.ico'))
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.iconphoto(False, icon_photo)
        except Exception as e:
            print(f"Failed to set window icon: {e}")

        self.title("ASTRA – Advanced Sync & Tracking for Replication Automation")
        self.attributes('-fullscreen', True)

        self.intro = IntroFrame(self, self.show_main)
        self.main_ui = MainFrame(self)

        self.intro.pack(fill='both', expand=True)
        self.bind("<Escape>", lambda e: self.destroy())

    def show_main(self):
        self.intro.pack_forget()
        self.main_ui.pack(fill='both', expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
