import customtkinter as ctk
import threading
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from ...core.converter import PDFConverter
from ...utils.helpers import open_directory
from ..components.scrollable_link_frame import ScrollableLinkFrame

class ConversionTab(ctk.CTkFrame):
    def __init__(self, master, parent_app):
        super().__init__(master)
        self.parent_app = parent_app
        self.converter = PDFConverter()

        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(
            self, text="Webpage to PDF Converter", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.grid(row=0, column=0, padx=20, pady=(0, 20), sticky="w")

        # Top Bar (Input & Output)
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)

        # Save Directory
        self.dir_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.dir_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.dir_frame.grid_columnconfigure(1, weight=1)

        self.dir_label = ctk.CTkLabel(self.dir_frame, text="Save To:")
        self.dir_label.grid(row=0, column=0, padx=(0, 10))

        self.dir_path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.dir_entry = ctk.CTkEntry(self.dir_frame, textvariable=self.dir_path_var)
        self.dir_entry.grid(row=0, column=1, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            self.dir_frame, text="Browse", width=80, 
            command=self.browse_directory
        )
        self.browse_btn.grid(row=0, column=2, padx=(10, 0))

        # Main Content (Queue and Log)
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=2, column=0, padx=20, pady=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)

        # Queue Column
        self.queue_header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.queue_header_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        self.queue_label = ctk.CTkLabel(self.queue_header_frame, text="URL Queue", font=ctk.CTkFont(weight="bold"))
        self.queue_label.pack(side="left")
        
        self.clear_queue_btn = ctk.CTkButton(
            self.queue_header_frame, text="Clear", width=60, height=20,
            command=self.clear_queue, fg_color="gray30", hover_color="gray20"
        )
        self.clear_queue_btn.pack(side="right", padx=(5, 0))

        self.import_btn = ctk.CTkButton(
            self.queue_header_frame, text="Import", width=60, height=20,
            command=self.import_urls, fg_color="gray50", hover_color="gray40"
        )
        self.import_btn.pack(side="right", padx=(5, 0))

        self.paste_btn = ctk.CTkButton(
            self.queue_header_frame, text="Paste", width=60, height=20,
            command=self.paste_urls, fg_color="gray50", hover_color="gray40"
        )
        self.paste_btn.pack(side="right", padx=(5, 0))
        
        self.add_url_btn = ctk.CTkButton(
            self.queue_header_frame, text="+ Add", width=60, height=20,
            command=self.prompt_add_url, fg_color="gray50", hover_color="gray40"
        )
        self.add_url_btn.pack(side="right", padx=(5, 0))
        
        self.queue_frame = ScrollableLinkFrame(
            self.content_frame, show_checkboxes=False, can_remove=True, label_text="URLs to Convert"
        )
        self.queue_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Log Column
        self.log_label = ctk.CTkLabel(self.content_frame, text="Execution Log", font=ctk.CTkFont(weight="bold"))
        self.log_label.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")

        self.log_textbox = ctk.CTkTextbox(self.content_frame, fg_color=("gray90", "gray15"), state="disabled")
        self.log_textbox.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Progress Frame
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        # Control Buttons
        self.controls_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.controls_frame.grid(row=0, column=1, rowspan=2, padx=10)

        self.start_btn = ctk.CTkButton(
            self.controls_frame, text="Start Conversion", 
            command=self.start_conversion, 
            fg_color="blue", hover_color="darkblue"
        )
        self.start_btn.pack(side="top", pady=5)

        self.stop_btn = ctk.CTkButton(
            self.controls_frame, text="Stop", 
            command=self.stop_conversion, 
            fg_color="red", hover_color="darkred", 
            state="disabled"
        )
        self.stop_btn.pack(side="top", pady=5)

    def add_urls(self, urls):
        """Add URLs to the queue."""
        existing = set(self.queue_frame.get_all_urls())
        for url in urls:
            url = url.strip()
            if not url:
                continue
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            if url not in existing:
                self.queue_frame.add_link(url, url)
                existing.add(url)

    def prompt_add_url(self):
        dialog = ctk.CTkInputDialog(text="Enter webpage URL:", title="Add URL")
        url = dialog.get_input()
        if url:
            self.add_urls([url])

    def paste_urls(self):
        try:
            data = self.parent_app.clipboard_get()
            urls = [line.strip() for line in data.splitlines() if line.strip()]
            if not urls:
                messagebox.showwarning("Warning", "No valid URLs found in clipboard.")
                return
            self.add_urls(urls)
        except tk.TclError:
            messagebox.showwarning("Warning", "Clipboard is empty.")

    def import_urls(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file.read().splitlines() if line.strip()]
            self.add_urls(urls)
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to read file: {exc}")

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_path_var.set(directory)

    def start_conversion(self):
        urls = self.queue_frame.get_all_urls()
        if not urls:
            messagebox.showwarning("Warning", "Queue is empty")
            return
        
        save_dir = self.dir_path_var.get()
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create directory: {e}")
                return

        self.converter.reset()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        thread = threading.Thread(target=self.run_conversion, args=(urls, save_dir))
        thread.daemon = True
        thread.start()

    def run_conversion(self, urls, save_dir):
        total = len(urls)
        processed = 0

        def update_progress(n):
            nonlocal processed
            processed += n
            self.after(0, lambda: self.progress_bar.set(processed / total))

        def update_status(text):
            self.after(0, lambda: self.status_label.configure(text=text))

        def update_log(text):
            self.after(0, lambda: self.append_log(text))

        try:
            self.converter.convert_multiple(
                urls, 
                save_dir, 
                on_progress=update_progress,
                on_status=update_status,
                on_log=update_log
            )
            self.after(0, self.finish_conversion)
        except Exception as e:
            update_log(f"CRITICAL ERROR: {e}")
            self.after(0, self.finish_conversion)

    def finish_conversion(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Finished")
        if messagebox.askyesno("Finished", "Conversion process completed. Open folder?"):
            open_directory(self.dir_path_var.get())

    def stop_conversion(self):
        self.converter.stop()
        self.status_label.configure(text="Stopping...")
        self.stop_btn.configure(state="disabled")

    def append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def clear_queue(self):
        self.queue_frame.clear()
