# intro.py
import tkinter as tk


class IntroFrame(tk.Frame):
    def __init__(self, master, switch_callback):
        super().__init__(master, bg="black")
        self.master = master
        self.switch_callback = switch_callback

        self.fade_step = 0
        self.max_step = 100
        self.bg_step = 0
        self.bg_target_rgb = (53, 53, 53)

        self.center_frame = tk.Frame(self, bg="black")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = tk.Label(
            self.center_frame,
            text="Welcome to A.S.T.R.A.",
            font=("Arial", 40, "bold"),
            fg="#000000",
            bg="black"
        )
        self.label.pack(pady=(0, 10))

        self.subtitle = tk.Label(
            self.center_frame,
            text="Advanced Synchronization, Tracking & Replication Assistant",
            font=("Arial", 18),
            fg="#000000",
            bg="black"
        )
        self.subtitle.pack()

        self.fade_in_text()

    def fade_in_text(self):
        if self.fade_step <= self.max_step:
            gray = int(255 * (self.fade_step / self.max_step))
            color = f'#{gray:02x}{gray:02x}{gray:02x}'
            self.label.config(fg=color)
            self.subtitle.config(fg=color)
            self.fade_step += 1
            self.after(20, self.fade_in_text)
        else:
            self.after(1500, self.fade_out_text)

    def fade_out_text(self):
        if self.fade_step >= 0:
            gray = int(255 * (self.fade_step / self.max_step))
            color = f'#{gray:02x}{gray:02x}{gray:02x}'
            self.label.config(fg=color)
            self.subtitle.config(fg=color)
            self.fade_step -= 1
            self.after(20, self.fade_out_text)
        else:
            self.label.destroy()
            self.subtitle.destroy()
            self.center_frame.destroy()
            self.fade_in_background()

    def fade_in_background(self):
        if self.bg_step <= self.max_step:
            r = int((self.bg_target_rgb[0] * self.bg_step) / self.max_step)
            g = int((self.bg_target_rgb[1] * self.bg_step) / self.max_step)
            b = int((self.bg_target_rgb[2] * self.bg_step) / self.max_step)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.configure(bg=color)
            self.bg_step += 1
            self.after(20, self.fade_in_background)
        else:
            self.switch_callback()
