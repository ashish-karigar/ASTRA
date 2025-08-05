# astra.py
import tkinter as tk
from intro import IntroFrame
from main import MainFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()
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
