import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from PIL import Image, ImageTk
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import shutil


class TitleBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#A63131", height=60)
        self.master = master

        logo_image = Image.open("../../assets/logo.png")
        logo_image = logo_image.resize((40, 40))
        self.logo_photo = ImageTk.PhotoImage(logo_image)

        logo_label = tk.Label(self, image=self.logo_photo, bg="#A63131")
        logo_label.pack(side="left", padx=(10, 5), pady=5)

        title_label = tk.Label(
            self,
            text="A.S.T.R.A.",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#A63131"
        )
        title_label.pack(side="left", pady=10)


class WatchHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"Modified: {event.src_path}")

    def on_created(self, event):
        if not event.is_directory:
            print(f"New file: {event.src_path}")


class MainFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#1E1E1E")
        self.master = master
        self.backup_interval = 10
        self.remaining_seconds = self.backup_interval * 60
        self.observer = None

        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Rounded.TButton", foreground="black", background="white", padding=6,
                        relief="flat", font=("Helvetica", 10, "bold"))
        style.map("Rounded.TButton", background=[('active', '#e6e6e6')], foreground=[('disabled', 'gray')])

        self.title_bar = TitleBar(self)
        self.title_bar.pack(fill="x", side="top")

        sidebar_width = int(screen_width * 0.3)
        remaining_height = screen_height - self.title_bar.winfo_reqheight()

        self.sidebar = tk.Frame(self, bg="#1E1E1E", width=sidebar_width, height=remaining_height)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        next_backup_label = tk.Label(self.sidebar, text="Next backup in:", font=("Arial", 18), bg="#1E1E1E", anchor="w")
        next_backup_label.pack(pady=(30, 2), padx=10, anchor="w")

        self.backup_timer_label = tk.Label(self.sidebar, text="00:00:00", font=("Digital-7 Mono", 100), fg="white", bg="#1E1E1E")
        self.backup_timer_label.pack(pady=2, padx=10, anchor="w")

        self.update_backup_timer_label()
        self.countdown()

        backup_freq_frame = tk.Frame(self.sidebar, bg="#1E1E1E")
        backup_freq_frame.pack(pady=10, padx=10, anchor="w", fill="x")

        backup_freq_label = tk.Label(backup_freq_frame, text="Backup every", font=("Arial", 14), bg="#1E1E1E")
        backup_freq_label.pack(side="left")

        self.backup_interval_entry = tk.Entry(backup_freq_frame, width=5, font=("Arial", 14))
        self.backup_interval_entry.insert(0, "10")
        self.backup_interval_entry.pack(side="left", padx=5)

        minutes_label = tk.Label(backup_freq_frame, text="minutes", font=("Arial", 14), bg="#1E1E1E")
        minutes_label.pack(side="left")

        button_frame = tk.Frame(self.sidebar, bg="#1E1E1E")
        button_frame.pack(pady=10, padx=10, anchor="w")

        self.update_timer_button = ttk.Button(button_frame, text="Update Timer", style="Rounded.TButton", command=self.update_timer)
        self.update_timer_button.pack(pady=5, padx=5, side="left")

        self.backup_now_button = ttk.Button(button_frame, text="Backup Now", style="Rounded.TButton", command=self.backup_now)
        self.backup_now_button.pack(side="left", pady=5, padx=5)

        self.content_area = tk.Frame(self, bg="#1E1E1E")
        self.content_area.pack(expand=True, fill="both", side="left")

        input_frame = tk.Frame(self.content_area, bg="#1E1E1E")
        input_frame.pack(pady=20, padx=20, anchor="nw")

        tk.Label(input_frame, text="Source:", bg="#1E1E1E", fg="white", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 2), columnspan=2)
        self.path_var1 = tk.StringVar(value="Select Source path")
        label1 = tk.Label(input_frame, textvariable=self.path_var1, width=80, bg="#2D2D2D", fg="white",
                          anchor="w", padx=6, pady=8, relief="sunken", font=("Segoe UI", 10))
        label1.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="w")
        ttk.Button(input_frame, text="Browse", command=lambda: self.browse_file(self.path_var1), style="Rounded.TButton").grid(row=1, column=1, pady=10)

        tk.Label(input_frame, text="Destination:", bg="#1E1E1E", fg="white", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 2), columnspan=2)
        self.path_var2 = tk.StringVar(value="Select Destination path.")
        label2 = tk.Label(input_frame, textvariable=self.path_var2, width=80, bg="#2D2D2D", fg="white",
                          anchor="w", padx=6, pady=8, relief="sunken", font=("Segoe UI", 10))
        label2.grid(row=4, column=0, padx=(0, 10), pady=10, sticky="w")
        ttk.Button(input_frame, text="Browse", command=lambda: self.browse_file(self.path_var2), style="Rounded.TButton").grid(row=4, column=1, pady=10)

        start_stop_frame = tk.Frame(self.content_area, bg="#1E1E1E")
        start_stop_frame.pack(pady=10, padx=15, anchor="w")

        ttk.Button(start_stop_frame, text="Start", style="Rounded.TButton", command=self.start_monitoring).pack(pady=5, padx=5, side="left")
        ttk.Button(start_stop_frame, text="Stop", style="Rounded.TButton", command=self.stop_monitoring).pack(side="left", pady=5, padx=5)

    def update_timer(self):
        try:
            new_interval = int(self.backup_interval_entry.get())
            if new_interval <= 0:
                raise ValueError("Time must be positive.")
            self.backup_interval = new_interval
            self.remaining_seconds = self.backup_interval * 60
            self.update_backup_timer_label()
        except ValueError:
            print("Invalid input. Please enter a valid number of minutes.")

    def backup_now(self):
        print("Backing up now...")
        self.remaining_seconds = self.backup_interval * 60
        self.update_backup_timer_label()

    def countdown(self):
        if self.remaining_seconds > 0:
            mins, secs = divmod(self.remaining_seconds, 60)
            hours, mins = divmod(mins, 60)
            self.backup_timer_label.config(text=f"{hours:02}:{mins:02}:{secs:02}")
            self.remaining_seconds -= 1
            self.after(1000, self.countdown)
        else:
            print("Timer done. You can trigger backup logic here.")
            self.remaining_seconds = self.backup_interval * 60
            self.countdown()

    def update_backup_timer_label(self):
        mins, secs = divmod(self.remaining_seconds, 60)
        hours, mins = divmod(mins, 60)
        self.backup_timer_label.config(text=f"{hours:02}:{mins:02}:{secs:02}")

    def browse_file(self, var):
        from tkinter import filedialog
        file_path = filedialog.askdirectory()
        if file_path:
            var.set(file_path)

    # def start_monitoring(self):
    #     path = self.path_var1.get()
    #     if not os.path.isdir(path):
    #         print("Invalid source path")
    #         return
    #
    #     if self.observer and self.observer.is_alive():
    #         print("Already monitoring.")
    #         return
    #
    #     self.event_handler = WatchHandler()
    #     self.observer = Observer()
    #     self.observer.schedule(self.event_handler, path=path, recursive=True)
    #     self.monitor_thread = threading.Thread(target=self.observer.start, daemon=True)
    #     self.monitor_thread.start()
    #     print(f"Started monitoring: {path}")
    #
    # def stop_monitoring(self):
    #     if self.observer:
    #         self.observer.stop()
    #         self.observer.join()
    #         print("Stopped monitoring.")

    def sync_directories(self, source, destination):
        for root, dirs, files in os.walk(source):
            relative_path = os.path.relpath(root, source)
            dest_root = os.path.join(destination, relative_path)

            if not os.path.exists(dest_root):
                os.makedirs(dest_root)

            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)

                if not os.path.exists(dest_file):
                    shutil.copy2(src_file, dest_file)
                    print(f"Copied new file: {src_file} → {dest_file}")
                else:
                    src_mtime = os.path.getmtime(src_file)
                    dest_mtime = os.path.getmtime(dest_file)

                    if src_mtime > dest_mtime:
                        shutil.copy2(src_file, dest_file)
                        print(f"Updated file: {src_file} → {dest_file}")

    def start_monitoring(self):
        source_dir = self.path_var1.get()
        dest_dir = self.path_var2.get()

        if not os.path.isdir(source_dir):
            print("Invalid source path")
            return

        if not os.path.isdir(dest_dir):
            print("Invalid destination path")
            return

        print(f"Starting backup from:\n  Source: {source_dir}\n  Destination: {dest_dir}")
        self.sync_directories(source_dir, dest_dir)
        print("Backup complete.")

    def stop_monitoring(self):
        print("Stopped monitoring (no watchdog in use).")
