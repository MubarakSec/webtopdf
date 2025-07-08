import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
from playwright.sync_api import sync_playwright
import re
import os
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class PDFConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Webpage to PDF Converter")
        master.geometry("800x600")

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', padding=5)
        self.style.configure('TButton', padding=5)
        self.style.configure('TLabel', padding=5)

        # Create GUI elements
        self.create_url_frame()
        self.create_save_dir_frame()
        self.create_options_frame()
        self.create_control_frame()
        self.create_progress_frame()
        self.create_log_frame()

        # Initialize variables
        self.save_dir = None
        self.queue = queue.Queue()
        self.running = False
        self.master.after(100, self.process_queue)

    def create_url_frame(self):
        self.url_frame = ttk.LabelFrame(self.master, text="URL List")
        self.url_text = tk.Text(self.url_frame, height=10, wrap=tk.WORD)
        scroll = ttk.Scrollbar(self.url_frame, command=self.url_text.yview)
        self.url_text.configure(yscrollcommand=scroll.set)

        button_frame = ttk.Frame(self.url_frame)
        self.add_url_btn = ttk.Button(button_frame, text="Add URL", command=self.add_url)
        self.import_btn = ttk.Button(button_frame, text="Import File", command=self.import_urls)
        self.clear_btn = ttk.Button(button_frame, text="Clear", command=self.clear_urls)

        self.url_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.url_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        button_frame.pack(side=tk.RIGHT, padx=5)
        self.add_url_btn.pack(fill=tk.X, pady=2)
        self.import_btn.pack(fill=tk.X, pady=2)
        self.clear_btn.pack(fill=tk.X, pady=2)

    def create_save_dir_frame(self):
        frame = ttk.Frame(self.master)
        self.save_dir_label = ttk.Label(frame, text="Save Directory: Not Selected")
        self.choose_dir_btn = ttk.Button(frame, text="Choose Directory", command=self.choose_directory)
        
        frame.pack(padx=10, pady=5, fill=tk.X)
        self.save_dir_label.pack(side=tk.LEFT, expand=True)
        self.choose_dir_btn.pack(side=tk.RIGHT)

    def create_options_frame(self):
        frame = ttk.Frame(self.master)
        self.headless_var = tk.BooleanVar(value=True)
        self.headless_check = ttk.Checkbutton(frame, text="Headless Mode", variable=self.headless_var)
        self.retries_var = tk.IntVar(value=3)
        retries_frame = ttk.Frame(frame)
        ttk.Label(retries_frame, text="Retries:").pack(side=tk.LEFT)
        ttk.Spinbox(retries_frame, from_=1, to=5, textvariable=self.retries_var, width=3).pack(side=tk.LEFT)
        
        frame.pack(padx=10, pady=5, fill=tk.X)
        self.headless_check.pack(side=tk.LEFT)
        retries_frame.pack(side=tk.LEFT, padx=10)

    def create_control_frame(self):
        frame = ttk.Frame(self.master)
        self.start_btn = ttk.Button(frame, text="Start Conversion", command=self.start_conversion)
        self.stop_btn = ttk.Button(frame, text="Stop", command=self.stop_conversion, state=tk.DISABLED)
        
        frame.pack(padx=10, pady=5, fill=tk.X)
        self.start_btn.pack(side=tk.LEFT, expand=True)
        self.stop_btn.pack(side=tk.RIGHT, expand=True)

    def create_progress_frame(self):
        frame = ttk.Frame(self.master)
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, mode='determinate')
        self.status_label = ttk.Label(frame, text="Ready")
        
        frame.pack(padx=10, pady=5, fill=tk.X)
        self.progress.pack(fill=tk.X, expand=True)
        self.status_label.pack()

    def create_log_frame(self):
        frame = ttk.LabelFrame(self.master, text="Log")
        self.log_text = tk.Text(frame, height=8, state=tk.DISABLED)
        scroll = ttk.Scrollbar(frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        
        frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def add_url(self):
        url = tk.simpledialog.askstring("Add URL", "Enter webpage URL:")
        if url:
            self.url_text.insert(tk.END, url + "\n")

    def import_urls(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as f:
                urls = f.read().splitlines()
            self.url_text.insert(tk.END, "\n".join(urls) + "\n")

    def clear_urls(self):
        self.url_text.delete(1.0, tk.END)

    def choose_directory(self):
        self.save_dir = filedialog.askdirectory()
        if self.save_dir:
            self.save_dir_label.config(text=f"Save Directory: {self.save_dir}")

    def start_conversion(self):
        if not self.save_dir:
            messagebox.showerror("Error", "Please select a save directory")
            return
        urls = self.url_text.get(1.0, tk.END).strip().splitlines()
        if not urls:
            messagebox.showerror("Error", "Please enter at least one URL")
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.progress['maximum'] = len(urls)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        thread = threading.Thread(
            target=self.convert_urls,
            args=(urls, self.save_dir, self.headless_var.get(), self.retries_var.get()),
            daemon=True
        )
        thread.start()

    def stop_conversion(self):
        self.running = False
        self.status_label.config(text="Conversion stopped")

    def convert_urls(self, urls, save_dir, headless, max_retries):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            for i, url in enumerate(urls):
                if not self.running:
                    break
                
                success = self.process_page_with_retries(browser, url, save_dir, i, max_retries)
                
                if success:
                    self.queue.put(('progress', 1))
                else:
                    self.queue.put(('progress', 1))
            
            browser.close()
            self.queue.put(('done', None))

    def process_page_with_retries(self, browser, url, save_dir, i, max_retries):
            success = False
            for attempt in range(1, max_retries + 1):
                context = None
                try:
                    self.queue.put(('status', f"Processing {url} (attempt {attempt})"))
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 720},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    )
                    page = context.new_page()

                    page.goto(url, timeout=30000)
                    page.wait_for_load_state('domcontentloaded', timeout=120000)
                    page.wait_for_timeout(2000)

                    title = page.title()
                    filename = self.sanitize_filename(title) or f"page_{i + 1}"
                    filepath = os.path.join(save_dir, f"{filename}.pdf")

                    page.pdf(path=filepath, format='A4', print_background=True)
                    success = True
                    self.queue.put(('log', f"Saved: {filename}.pdf"))
                    break
                except (PlaywrightTimeoutError, Exception) as e:
                    self.queue.put(('log', f"Attempt {attempt} failed: {str(e)}"))
                    if attempt == max_retries:
                        try:
                            # Attempt to save whatever content is available
                            if page and not page.is_closed():
                                partial_title = page.title()
                                partial_filename = self.sanitize_filename(partial_title) or f"page_{i + 1}_partial"
                                partial_filepath = os.path.join(save_dir, f"{partial_filename}.pdf")
                                page.pdf(path=partial_filepath, format='A4', print_background=True)
                                self.queue.put(('log', f"Saved partial PDF: {partial_filename}.pdf"))
                                success = True  # Consider partial save as success for progress
                            else:
                                self.queue.put(('log', "Page unavailable for partial save"))
                        except Exception as e2:
                            self.queue.put(('log', f"Failed to save partial PDF: {str(e2)}"))
                        self.queue.put(('log', f"Failed to process {url} after {max_retries} attempts"))
                finally:
                    if context:
                        context.close()
            return success
    def sanitize_filename(self, filename):
        filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
        return filename.strip()[:100]

    def process_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'progress':
                    self.progress['value'] += msg[1]
                elif msg[0] == 'status':
                    self.status_label.config(text=msg[1])
                elif msg[0] in ('log', 'error'):
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, msg[1] + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
                elif msg[0] == 'done':
                    self.running = False
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    self.status_label.config(text="Conversion completed")
                    messagebox.showinfo("Info", "Processing finished!")
        except queue.Empty:
            pass
        self.master.after(100, self.process_queue)

    def on_closing(self):
        if self.running:
            if messagebox.askokcancel("Quit", "Conversion in progress. Are you sure you want to quit?"):
                self.running = False
                self.master.destroy()
        else:
            self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFConverterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
