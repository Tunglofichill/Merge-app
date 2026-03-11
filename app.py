import os
import math
import json
import datetime
import threading
import platform
import webbrowser
from PIL import Image
import tkinter as tk
from tkinter import filedialog

# ================= APP INFO =================
APP_NAME = "Merge App"
VERSION = "1.3.1"
AUTHOR = "SekiGremory"
DISCORD_URL = "https://discord.gg/ueqtuREEGw"

CONFIG_FILE = "config.json"

cancel_flag = False
current_theme = "dark"
progress_value = 0

# ================= CONFIG =================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"theme": "dark", "cols": 8, "quality": 92}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= THEME =================
def apply_theme(theme):
    global current_theme
    current_theme = theme

    if theme == "dark":
        bg = "#1e1e1e"
        fg = "white"
        entry_bg = "#2a2a2a"
    else:
        bg = "#f0f0f0"
        fg = "black"
        entry_bg = "white"

    root.configure(bg=bg)
    main.configure(bg=bg)
    form_frame.configure(bg=bg)
    footer_frame.configure(bg=bg)
    compression_frame.configure(bg=bg)

    for widget in main.winfo_children():
        try:
            widget.configure(bg=bg, fg=fg)
        except:
            pass

    for widget in form_frame.winfo_children():
        try:
            widget.configure(bg=bg, fg=fg)
        except:
            pass

    for entry in [entry_input, entry_output, entry_cols, entry_maxsize]:
        entry.configure(bg=entry_bg, fg=fg, insertbackground=fg)

    limit_checkbox.configure(
        bg=bg,
        fg=fg,
        selectcolor=entry_bg,
        activebackground=bg,
        activeforeground=fg
    )

    draw_progress(progress_value)

    config_data["theme"] = theme
    save_config(config_data)

def toggle_theme():
    apply_theme("light" if current_theme == "dark" else "dark")

# ================= PROGRESS =================
def draw_progress(percent):
    global progress_value
    progress_value = percent

    canvas.delete("all")
    width = 650
    height = 22

    fill_color = "#5865F2" if current_theme == "dark" else "#4CAF50"
    bg_color = "#2a2a2a" if current_theme == "dark" else "#dddddd"
    text_color = "white" if current_theme == "dark" else "black"

    canvas.create_rectangle(0, 0, width, height,
                            fill=bg_color, outline=bg_color)

    fill_width = int((percent / 100) * width)
    canvas.create_rectangle(0, 0, fill_width, height,
                            fill=fill_color, outline=fill_color)

    canvas.create_text(width/2, height/2,
                       text=f"{percent}%",
                       fill=text_color,
                       font=("Segoe UI", 9, "bold"))

# ================= SMART SAVE =================
def save_with_limit(image, path, quality, max_mb):
    max_bytes = max_mb * 1024 * 1024

    image.save(path, format="JPEG", quality=quality, optimize=True)
    if os.path.getsize(path) <= max_bytes:
        return quality

    while quality >= 30:
        image.save(path, format="JPEG", quality=quality, optimize=True)
        if os.path.getsize(path) <= max_bytes:
            return quality
        quality -= 5

    return quality

# ================= MERGE =================
def merge_images():
    global cancel_flag
    cancel_flag = False
    btn_merge.config(state="disabled")
    btn_cancel.config(state="normal")
    draw_progress(0)
    set_status("Preparing...")
    threading.Thread(target=process_images, daemon=True).start()

def process_images():
    try:
        input_folder = entry_input.get()
        output_folder = entry_output.get()
        cols = int(entry_cols.get())
        quality = config_data.get("quality", 92)
        TARGET_WIDTH = 800

        files = sorted([f for f in os.listdir(input_folder)
                        if f.lower().endswith((".png", ".jpg", ".jpeg"))])

        total = len(files)
        rows = math.ceil(total / cols)

        first_img = Image.open(os.path.join(input_folder, files[0])).convert("RGB")
        ratio = TARGET_WIDTH / first_img.width
        img_w = TARGET_WIDTH
        img_h = int(first_img.height * ratio)

        canvas_img = Image.new("RGB",
                               (cols * img_w, rows * img_h),
                               (25,25,25))

        for i, filename in enumerate(files):
            if cancel_flag:
                return

            img = Image.open(os.path.join(input_folder, filename)).convert("RGB")
            img = img.resize((img_w, img_h), Image.LANCZOS)

            row = i // cols
            col = i % cols
            canvas_img.paste(img, (col * img_w, row * img_h))
            img.close()

            percent = int(((i+1)/total)*100)
            root.after(0, draw_progress, percent)
            root.after(0, set_status, f"Processing... {percent}%")

        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(
            output_folder,
            f"merge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        )

        if limit_var.get():
            try:
                max_mb = float(entry_maxsize.get())
                save_with_limit(canvas_img, output_path, quality, max_mb)
            except:
                canvas_img.save(output_path, format="JPEG",
                                quality=quality, optimize=True)
        else:
            canvas_img.save(output_path, format="JPEG",
                            quality=quality, optimize=True)

        root.after(0, set_status, "Completed ✔")

    except Exception as e:
        root.after(0, set_status, "Error: " + str(e))

    finally:
        root.after(0, btn_merge.config, {"state": "normal"})
        root.after(0, btn_cancel.config, {"state": "disabled"})

def cancel_process():
    global cancel_flag
    cancel_flag = True

# ================= STATUS =================
def set_status(message):
    status_bar.config(text="  " + message)

# ================= BROWSE =================
def browse_input():
    folder = filedialog.askdirectory()
    if folder:
        entry_input.delete(0, tk.END)
        entry_input.insert(0, folder)

def browse_output():
    folder = filedialog.askdirectory()
    if folder:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, folder)

# ================= GUI =================
root = tk.Tk()
root.title(f"{APP_NAME} v{VERSION}")
root.geometry("780x620")

main = tk.Frame(root, padx=40, pady=30)
main.pack(fill="both", expand=True)

tk.Label(main, text=APP_NAME,
         font=("Segoe UI", 24, "bold")).pack(pady=(0, 10))

tk.Button(main, text="🌗 Toggle Dark/Light",
          command=toggle_theme).pack(pady=(0, 20))

form_frame = tk.Frame(main)
form_frame.pack(pady=10, fill="x")
form_frame.columnconfigure(1, weight=1)

tk.Label(form_frame, text="Input Folder", width=15, anchor="w")\
    .grid(row=0, column=0, sticky="w", pady=8)
entry_input = tk.Entry(form_frame)
entry_input.grid(row=0, column=1, sticky="ew", pady=8)
tk.Button(form_frame, text="Browse",
          command=browse_input).grid(row=0, column=2, padx=5)

tk.Label(form_frame, text="Output Folder", width=15, anchor="w")\
    .grid(row=1, column=0, sticky="w", pady=8)
entry_output = tk.Entry(form_frame)
entry_output.grid(row=1, column=1, sticky="ew", pady=8)
tk.Button(form_frame, text="Browse",
          command=browse_output).grid(row=1, column=2, padx=5)

tk.Label(form_frame, text="Images per row", width=15, anchor="w")\
    .grid(row=2, column=0, sticky="w", pady=8)
entry_cols = tk.Entry(form_frame, width=10)
entry_cols.insert(0, "8")
entry_cols.grid(row=2, column=1, sticky="w", pady=8)

# ===== Compression Section =====
compression_frame = tk.Frame(main)
compression_frame.pack(pady=15)

limit_var = tk.BooleanVar()

limit_checkbox = tk.Checkbutton(
    compression_frame,
    text="Limit output file size (MB)",
    variable=limit_var,
    highlightthickness=0
)
limit_checkbox.pack(side="left")

entry_maxsize = tk.Entry(compression_frame, width=6)
entry_maxsize.insert(0, "2")
entry_maxsize.pack(side="left", padx=5)

btn_merge = tk.Button(main, text="Merge",
                      command=merge_images,
                      bg="#4CAF50", fg="white",
                      width=20, height=2)
btn_merge.pack(pady=20)

btn_cancel = tk.Button(main, text="Cancel",
                       command=cancel_process,
                       bg="#cc3333", fg="white",
                       width=12)
btn_cancel.pack()

canvas = tk.Canvas(main, width=650, height=22, highlightthickness=0)
canvas.pack(pady=25)

footer_frame = tk.Frame(root)
footer_frame.pack(side="bottom", fill="x")

footer = tk.Label(
    footer_frame,
    text=f"{APP_NAME} v{VERSION} • Made by {AUTHOR}",
    font=("Segoe UI", 9),
    fg="#777"
)
footer.pack(pady=4)

status_bar = tk.Label(
    footer_frame,
    text="  Ready",
    fg="white",
    bg="#444",
    anchor="w"
)
status_bar.pack(fill="x")

config_data = load_config()
apply_theme(config_data.get("theme", "dark"))
draw_progress(0)

root.mainloop()