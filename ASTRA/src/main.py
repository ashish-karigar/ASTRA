import sys
import tkinter as tk
from tkinter import font as tkfont, scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import shutil
from datetime import datetime


class TitleBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#A63131", height=60)
        self.master = master

        logo_image = Image.open("../assets/logo.png")
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
    def __init__(self, source_path, dest_path, logger):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path
        self.logger = logger

        self.logger("Name                                                                       | Status    | Kind   | Size     | Date Modified")
        self.logger("-" * 80)

    def on_created(self, event):
        if not event.is_directory:
            self._log_file_info(event.src_path, status="New")

    def on_modified(self, event):
        if not event.is_directory:
            self._log_file_info(event.src_path, status="Modified")

    def _log_file_info(self, file_path, status):
        try:
            name = os.path.basename(file_path)
            ext = os.path.splitext(name)[1] or "-"
            size_bytes = os.path.getsize(file_path)
            size_kb = f"{size_bytes / 1024:.1f} KB"
            mtime = os.path.getmtime(file_path)
            mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            log_line = f"{name:<30} | {status:<9} | {ext:<6} | {size_kb:<8} | {mod_time}"
            self.logger(log_line)

        except Exception as e:
            self.logger(f"Error accessing {file_path}: {e}")


class MainFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#1E1E1E")
        self.master = master
        self.backup_interval = 10
        self.remaining_seconds = self.backup_interval * 60
        self.observer = None
        self.timer_running = False
        self.timer_paused = False

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

        self.last_backup_label_title = tk.Label(self.sidebar, text="Last Backup on:", font=("Helvetica", 16),
                                                bg="#1e1e1e", fg="#d0d0d0", anchor="w", justify="left")
        self.last_backup_label_title.pack(pady=(30, 0), fill="x")

        self.last_backup_label = tk.Label(self.sidebar, text="No backup yet", font=("Helvetica", 14, "italic"),
                                          bg="#1e1e1e", fg="#a0a0a0", anchor="w", justify="left")
        self.last_backup_label.pack(fill="x")

        self.update_last_backup_label()

        # Create a frame at the bottom of the sidebar for disk health
        self.disk_health_frame = tk.Frame(self.sidebar, bg="#1E1E1E")
        self.disk_health_frame.pack(side="bottom", fill="x", pady=(10,20))

        # Disk Health Label inside bottom frame
        self.disk_health_label = tk.Label(self.disk_health_frame,
                                          text="Disk Health:\nSize Remaining - -- / -- GB",
                                          font=("Helvetica", 16),
                                          bg="#1e1e1e", fg="#d0d0d0",
                                          anchor="w", justify="left")
        self.disk_health_label.pack(fill="x", padx=10)

        # Disk Health Progress Bar inside bottom frame
        self.disk_health_bar = ttk.Progressbar(self.disk_health_frame,
                                               orient="horizontal", mode="determinate")
        self.disk_health_bar.pack(fill="x", padx=10, pady=(5, 0))

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
        self.path_var2 = tk.StringVar(value="Select Destination path")
        label2 = tk.Label(input_frame, textvariable=self.path_var2, width=80, bg="#2D2D2D", fg="white",
                          anchor="w", padx=6, pady=8, relief="sunken", font=("Segoe UI", 10))
        label2.grid(row=4, column=0, padx=(0, 10), pady=10, sticky="w")
        ttk.Button(input_frame, text="Browse", command=lambda: self.handle_destination_selection(), style="Rounded.TButton").grid(row=4, column=1, pady=10)

        start_stop_frame = tk.Frame(self.content_area, bg="#1E1E1E")
        start_stop_frame.pack(pady=10, padx=15, anchor="w")

        ttk.Button(start_stop_frame, text="Start", style="Rounded.TButton", command=self.start_monitoring).pack(pady=5, padx=5, side="left")
        ttk.Button(start_stop_frame, text="Stop", style="Rounded.TButton", command=self.stop_monitoring).pack(side="left", pady=5, padx=5)

        # Terminal Output Area with Custom Scrollbar Colors
        terminal_frame = tk.Frame(self.content_area, bg="#1E1E1E")
        terminal_frame.pack(padx=15, pady=(5, 15), fill="both", expand=True)

        self.terminal_output = tk.Text(
            terminal_frame,
            bg="#111111",
            fg="white",
            font=("Courier New", 10),
            wrap="word",
            relief="flat",
            borderwidth=5,
            height=10
        )
        self.terminal_output.pack(side="left", fill="both", expand=True)

        # scrollbar.config(command=self.terminal_output.yview)

        # Redirect stdout and stderr
        sys.stdout = self
        sys.stderr = self

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
        if not self.validate_paths():
            return

        print("Manual backup triggered.")
        self.perform_backup()
        self.remaining_seconds = self.backup_interval * 60
        self.update_backup_timer_label()

    def countdown(self):
        if self.timer_running and not self.timer_paused:
            if self.remaining_seconds > 0:
                mins, secs = divmod(self.remaining_seconds, 60)
                hours, mins = divmod(mins, 60)
                self.backup_timer_label.config(text=f"{hours:02}:{mins:02}:{secs:02}")
                self.remaining_seconds -= 1
                self.after(1000, self.countdown)
            else:
                self.timer_paused = True
                self.backup_timer_label.config(text="00:00:00")
                self.perform_backup()
                self.remaining_seconds = self.backup_interval * 60
                self.timer_paused = False
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
            return file_path
        return None

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
        if self.timer_running:
            print("Monitoring already started.")
            return

        if not self.validate_paths():
            return

        self.timer_running = True
        self.remaining_seconds = self.backup_interval * 60
        self.update_backup_timer_label()
        self.countdown()
        print("Monitoring started.")
        self.start_watchdog()

    def stop_monitoring(self):
        self.timer_running = False
        self.timer_paused = False
        self.backup_timer_label.config(text="00:00:00")
        print("Monitoring stopped.")
        self.stop_watchdog()

    def perform_backup(self):
        source_dir = self.path_var1.get()
        dest_dir = self.path_var2.get()

        print(f"Starting backup:\n  Source: {source_dir}\n  Destination: {dest_dir}")
        self.sync_directories(source_dir, dest_dir)
        print("Backup complete.")
        self.save_last_backup_time()
        self.update_last_backup_label()

    def validate_paths(self):
        source_dir = self.path_var1.get()
        dest_dir = self.path_var2.get()
        if not os.path.isdir(source_dir):
            print("Invalid source path")
            return False
        if not os.path.isdir(dest_dir):
            print("Invalid destination path")
            return False
        return True

    def write(self, message):
        self.terminal_output.config(state="normal")
        self.terminal_output.insert(tk.END, message)
        self.terminal_output.see(tk.END)
        self.terminal_output.config(state="disabled")

    def flush(self):
        pass  # Required for file-like behavior with stdout

    def start_watchdog(self):
        if not self.validate_paths():
            return

        if getattr(self, 'observer', None) and self.observer.is_alive():
            print("Watchdog is already running.")
            return

        source = self.path_var1.get()
        destination = self.path_var2.get()

        handler = WatchHandler(source, destination, self.print_terminal)
        self.observer = Observer()
        self.observer.schedule(handler, path=source, recursive=True)
        self.observer_thread = threading.Thread(target=self.observer.start, daemon=True)
        self.observer_thread.start()

        print("Watchdog monitoring started.")

    def stop_watchdog(self):
        if hasattr(self, 'observer') and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            print("Watchdog monitoring stopped.")

    def print_terminal(self, message):
        print(message)

    def save_last_backup_time(self):
        backup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("last_backup.txt", "w") as f:
            f.write(backup_time)

    def update_last_backup_label(self):
        try:
            with open("last_backup.txt", "r") as f:
                timestamp = f.read().strip()
                self.last_backup_label.config(text=timestamp)
        except FileNotFoundError:
            self.last_backup_label.config(text="No backup yet")

    def update_disk_health(self):
        if not self.dest_path:
            return

        total, used, free = shutil.disk_usage(self.dest_path)

        total_gb = total / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        percent_used = int((used / total) * 100)

        self.disk_health_label.config(
            text=f"Disk Health:\nSize Remaining - {free_gb:.1f} / {total_gb:.1f} GB"
        )
        self.disk_health_bar['value'] = percent_used

    def handle_destination_selection(self):
        selected_path = self.browse_file(self.path_var2)
        if selected_path:
            self.dest_path = selected_path  # Save for disk usage calculations
            self.update_disk_health()






