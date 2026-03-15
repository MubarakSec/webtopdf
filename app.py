import os
import re
import sys
import threading
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

APP_TITLE = "Web to PDF Toolkit"


class WebtoPDFApp:
    def __init__(self, root, start_tab="extract"):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x720")
        self.root.minsize(900, 650)

        self.colors = {
            "bg": "#f7f6f3",
            "panel": "#ffffff",
            "accent": "#0f4c81",
            "accent_dark": "#0b3b63",
            "text": "#111827",
            "muted": "#6b7280",
        }
        self.root.configure(bg=self.colors["bg"])

        self.style = ttk.Style(self.root)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        self.style.configure("TButton", padding=(10, 6))
        self.style.configure("TLabel", padding=(2, 2))
        self.style.configure("TEntry", padding=(4, 4))
        self.style.configure("TNotebook.Tab", padding=(12, 6))
        self.style.configure(
            "Accent.TButton",
            foreground="white",
            background=self.colors["accent"],
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", self.colors["accent_dark"]), ("pressed", self.colors["accent_dark"])],
            foreground=[("active", "white"), ("pressed", "white")],
        )

        self.ui_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.running = False

        self._set_window_icon()
        self._build_header()
        self._build_tabs()

        if start_tab == "convert":
            self.notebook.select(self.convert_tab)

        self.root.after(100, self.process_ui_queue)

    def _set_window_icon(self):
        icon_path = Path(__file__).with_name("assets") / "app.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.colors["accent"], padx=16, pady=12)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text=APP_TITLE,
            bg=self.colors["accent"],
            fg="white",
            font=("Bahnschrift", 18, "bold"),
        )
        subtitle = tk.Label(
            header,
            text="Extract links and convert web pages into PDFs in one place.",
            bg=self.colors["accent"],
            fg="#dbeafe",
            font=("Bahnschrift", 10),
        )
        title.pack(anchor="w")
        subtitle.pack(anchor="w")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.extract_tab = ttk.Frame(self.notebook)
        self.convert_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.extract_tab, text="Extract URLs")
        self.notebook.add(self.convert_tab, text="Convert to PDF")

        self._build_extract_tab()
        self._build_convert_tab()

    def _build_extract_tab(self):
        self.extract_tab.columnconfigure(0, weight=1)
        self.extract_tab.rowconfigure(1, weight=1)

        source_frame = ttk.LabelFrame(self.extract_tab, text="Source Page")
        source_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        source_frame.columnconfigure(1, weight=1)

        ttk.Label(source_frame, text="URL").grid(row=0, column=0, sticky="w")
        self.extract_url_var = tk.StringVar()
        self.extract_url_entry = ttk.Entry(source_frame, textvariable=self.extract_url_var)
        self.extract_url_entry.grid(row=0, column=1, sticky="ew", padx=6)

        self.extract_btn = ttk.Button(
            source_frame,
            text="Extract Links",
            style="Accent.TButton",
            command=self.start_extract,
        )
        self.extract_btn.grid(row=0, column=2, padx=6)

        options_frame = ttk.Frame(source_frame)
        options_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=6)

        self.same_domain_var = tk.BooleanVar(value=False)
        self.dedupe_var = tk.BooleanVar(value=True)
        self.skip_non_http_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Same domain only", variable=self.same_domain_var).pack(
            side=tk.LEFT, padx=(0, 12)
        )
        ttk.Checkbutton(options_frame, text="Deduplicate results", variable=self.dedupe_var).pack(
            side=tk.LEFT, padx=(0, 12)
        )
        ttk.Checkbutton(options_frame, text="Skip non-http links", variable=self.skip_non_http_var).pack(
            side=tk.LEFT
        )

        results_frame = ttk.LabelFrame(self.extract_tab, text="Extracted Links")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.links_tree = ttk.Treeview(
            results_frame,
            columns=("text", "url"),
            show="headings",
            selectmode="extended",
        )
        self.links_tree.heading("text", text="Link Text")
        self.links_tree.heading("url", text="URL")
        self.links_tree.column("text", width=240, anchor="w")
        self.links_tree.column("url", width=640, anchor="w")

        tree_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.links_tree.yview)
        self.links_tree.configure(yscrollcommand=tree_scroll.set)

        self.links_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")

        actions_frame = ttk.Frame(results_frame)
        actions_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Button(actions_frame, text="Select All", command=self.select_all_links).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions_frame, text="Clear Selection", command=self.clear_link_selection).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions_frame, text="Copy Selected", command=self.copy_selected_links).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions_frame, text="Save Selected", command=self.save_selected_links).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(actions_frame, text="Send to Converter", command=self.send_selected_to_converter).pack(
            side=tk.LEFT, padx=4
        )

        self.extract_status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self.extract_tab, textvariable=self.extract_status_var, foreground=self.colors["muted"])
        status.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _build_convert_tab(self):
        self.convert_tab.columnconfigure(0, weight=1)
        self.convert_tab.rowconfigure(0, weight=1)
        self.convert_tab.rowconfigure(5, weight=1)

        queue_frame = ttk.LabelFrame(self.convert_tab, text="URL Queue")
        queue_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(0, weight=1)

        self.queue_listbox = tk.Listbox(queue_frame, selectmode=tk.EXTENDED, height=8)
        queue_scroll = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_listbox.yview)
        self.queue_listbox.configure(yscrollcommand=queue_scroll.set)

        self.queue_listbox.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        queue_scroll.grid(row=0, column=1, sticky="ns", pady=4)

        queue_buttons = ttk.Frame(queue_frame)
        queue_buttons.grid(row=0, column=2, sticky="ns", padx=8, pady=4)

        ttk.Button(queue_buttons, text="Add URL", command=self.add_url).pack(fill=tk.X, pady=2)
        ttk.Button(queue_buttons, text="Paste", command=self.paste_urls).pack(fill=tk.X, pady=2)
        ttk.Button(queue_buttons, text="Import File", command=self.import_urls).pack(fill=tk.X, pady=2)
        ttk.Button(queue_buttons, text="Remove Selected", command=self.remove_selected_urls).pack(fill=tk.X, pady=2)
        ttk.Button(queue_buttons, text="Clear", command=self.clear_urls).pack(fill=tk.X, pady=2)

        output_frame = ttk.LabelFrame(self.convert_tab, text="Output")
        output_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        output_frame.columnconfigure(0, weight=1)

        self.save_dir_label = ttk.Label(output_frame, text="Save Directory: Not selected")
        self.choose_dir_btn = ttk.Button(output_frame, text="Choose Directory", command=self.choose_directory)
        self.open_folder_var = tk.BooleanVar(value=True)
        self.open_folder_check = ttk.Checkbutton(
            output_frame, text="Open folder when done", variable=self.open_folder_var
        )

        self.save_dir_label.grid(row=0, column=0, sticky="w", padx=4)
        self.choose_dir_btn.grid(row=0, column=1, padx=4)
        self.open_folder_check.grid(row=1, column=0, sticky="w", padx=4, pady=(4, 0))

        options_frame = ttk.Frame(self.convert_tab)
        options_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=4)

        self.headless_var = tk.BooleanVar(value=True)
        self.headless_check = ttk.Checkbutton(options_frame, text="Headless Mode", variable=self.headless_var)
        self.headless_check.pack(side=tk.LEFT)

        self.retries_var = tk.IntVar(value=3)
        ttk.Label(options_frame, text="Retries:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Spinbox(options_frame, from_=1, to=5, textvariable=self.retries_var, width=4).pack(side=tk.LEFT)

        controls_frame = ttk.Frame(self.convert_tab)
        controls_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=4)
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)

        self.start_btn = ttk.Button(controls_frame, text="Start Conversion", style="Accent.TButton", command=self.start_conversion)
        self.stop_btn = ttk.Button(controls_frame, text="Stop", command=self.stop_conversion, state=tk.DISABLED)

        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.stop_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        progress_frame = ttk.Frame(self.convert_tab)
        progress_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=4)
        progress_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode="determinate")
        self.status_label = ttk.Label(progress_frame, text="Ready")

        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.status_label.grid(row=1, column=0, sticky="w")

        log_frame = ttk.LabelFrame(self.convert_tab, text="Run Log")
        log_frame.grid(row=5, column=0, sticky="nsew", padx=12, pady=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        log_scroll.grid(row=0, column=1, sticky="ns", pady=4)

    def start_extract(self):
        url = self.extract_url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL to extract.")
            return
        if not url.startswith(("http://", "https://")):
            messagebox.showerror("Error", "Please include http:// or https:// in the URL.")
            return

        self.extract_btn.config(state=tk.DISABLED)
        self.extract_status_var.set("Fetching links...")

        threading.Thread(
            target=self.extract_worker,
            args=(
                url,
                self.same_domain_var.get(),
                self.dedupe_var.get(),
                self.skip_non_http_var.get(),
            ),
            daemon=True,
        ).start()

    def extract_worker(self, url, same_domain_only, dedupe, skip_non_http):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            self.ui_queue.put(("extract_error", f"Failed to fetch URL: {exc}"))
            return

        soup = BeautifulSoup(response.text, "html.parser")
        raw_links = soup.find_all("a", href=True)
        base_domain = urlparse(url).netloc

        seen = set()
        results = []

        for link in raw_links:
            href = link.get("href", "").strip()
            if not href:
                continue
            if skip_non_http and (href.startswith("mailto:") or href.startswith("javascript:") or href.startswith("#")):
                continue

            full_url = urljoin(url, href)
            if same_domain_only:
                parsed = urlparse(full_url)
                if parsed.netloc and parsed.netloc != base_domain:
                    continue

            if dedupe and full_url in seen:
                continue

            seen.add(full_url)
            text = link.get_text(strip=True) or "(No text)"
            results.append((text, full_url))

        self.ui_queue.put(("extract_results", {"links": results, "total": len(raw_links), "unique": len(results)}))

    def _apply_extract_results(self, payload):
        for item in self.links_tree.get_children():
            self.links_tree.delete(item)

        for text, url in payload["links"]:
            self.links_tree.insert("", tk.END, values=(text, url))

        self.extract_status_var.set(
            f"Found {payload['total']} links ({payload['unique']} after filters)."
        )
        self.extract_btn.config(state=tk.NORMAL)

    def _handle_extract_error(self, message):
        self.extract_btn.config(state=tk.NORMAL)
        self.extract_status_var.set("Ready")
        messagebox.showerror("Error", message)

    def select_all_links(self):
        for item in self.links_tree.get_children():
            self.links_tree.selection_add(item)

    def clear_link_selection(self):
        self.links_tree.selection_remove(self.links_tree.selection())

    def _get_selected_links(self):
        selected_items = self.links_tree.selection()
        urls = []
        for item in selected_items:
            values = self.links_tree.item(item, "values")
            if len(values) >= 2:
                urls.append(values[1])
        return urls

    def copy_selected_links(self):
        urls = self._get_selected_links()
        if not urls:
            messagebox.showwarning("Warning", "No links selected.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(urls))
        self.extract_status_var.set(f"Copied {len(urls)} URL(s) to clipboard.")

    def save_selected_links(self):
        urls = self._get_selected_links()
        if not urls:
            messagebox.showwarning("Warning", "No links selected.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(urls))
            self.extract_status_var.set(f"Saved {len(urls)} URL(s) to {file_path}.")
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to save file: {exc}")

    def send_selected_to_converter(self):
        urls = self._get_selected_links()
        if not urls:
            messagebox.showwarning("Warning", "No links selected.")
            return
        added = self.add_urls_to_queue(urls)
        self.extract_status_var.set(f"Sent {added} URL(s) to the converter queue.")
        self.notebook.select(self.convert_tab)

    def add_url(self):
        url = simpledialog.askstring("Add URL", "Enter webpage URL:")
        if url:
            self.add_urls_to_queue([url.strip()])

    def paste_urls(self):
        try:
            data = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("Warning", "Clipboard is empty.")
            return
        urls = [line.strip() for line in data.splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning("Warning", "No valid URLs found in clipboard.")
            return
        self.add_urls_to_queue(urls)

    def import_urls(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file.read().splitlines() if line.strip()]
            self.add_urls_to_queue(urls)
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to read file: {exc}")

    def remove_selected_urls(self):
        selected = list(self.queue_listbox.curselection())
        if not selected:
            return
        for index in reversed(selected):
            self.queue_listbox.delete(index)

    def clear_urls(self):
        self.queue_listbox.delete(0, tk.END)

    def add_urls_to_queue(self, urls):
        existing = set(self.queue_listbox.get(0, tk.END))
        added = 0
        for url in urls:
            if not url:
                continue
            if url in existing:
                continue
            self.queue_listbox.insert(tk.END, url)
            existing.add(url)
            added += 1
        return added

    def choose_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_dir = directory
            self.save_dir_label.config(text=f"Save Directory: {self.save_dir}")

    def start_conversion(self):
        if self.running:
            return
        self.save_dir = getattr(self, "save_dir", None)
        if not self.save_dir:
            messagebox.showerror("Error", "Please select a save directory.")
            return
        urls = list(self.queue_listbox.get(0, tk.END))
        if not urls:
            messagebox.showerror("Error", "Please add at least one URL to convert.")
            return

        self.running = True
        self.stop_event.clear()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.progress["maximum"] = len(urls)
        self.status_label.config(text="Starting conversion...")
        self._reset_log()

        thread = threading.Thread(
            target=self.convert_urls,
            args=(urls, self.save_dir, self.headless_var.get(), self.retries_var.get()),
            daemon=True,
        )
        thread.start()

    def stop_conversion(self):
        if not self.running:
            return
        self.stop_event.set()
        self.status_label.config(text="Stopping after current page...")
        self.stop_btn.config(state=tk.DISABLED)

    def convert_urls(self, urls, save_dir, headless, max_retries):
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=headless)
                try:
                    for index, url in enumerate(urls, start=1):
                        if self.stop_event.is_set():
                            break
                        self.process_page_with_retries(browser, url, save_dir, index, max_retries)
                        self.ui_queue.put(("convert_progress", 1))
                finally:
                    browser.close()
        except Exception as exc:
            self.ui_queue.put(("convert_log", f"Fatal error: {exc}"))
            self.ui_queue.put(("convert_done", {"stopped": True, "error": str(exc)}))
            return
        self.ui_queue.put(("convert_done", {"stopped": self.stop_event.is_set()}))

    def process_page_with_retries(self, browser, url, save_dir, index, max_retries):
        success = False
        for attempt in range(1, max_retries + 1):
            if self.stop_event.is_set():
                break
            context = None
            page = None
            try:
                self.ui_queue.put(("convert_status", f"Processing {url} (attempt {attempt})"))
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/118.0.0.0 Safari/537.36"
                    ),
                )
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)

                title = page.title()
                filename = self.sanitize_filename(title) or f"page_{index}"
                filepath = os.path.join(save_dir, f"{filename}.pdf")

                page.pdf(path=filepath, format="A4", print_background=True)
                success = True
                self.ui_queue.put(("convert_log", f"Saved: {filename}.pdf"))
                break
            except (PlaywrightTimeoutError, Exception) as exc:
                self.ui_queue.put(("convert_log", f"Attempt {attempt} failed: {exc}"))
                if attempt == max_retries:
                    try:
                        if page and not page.is_closed():
                            partial_title = page.title()
                            partial_filename = self.sanitize_filename(partial_title) or f"page_{index}_partial"
                            partial_filepath = os.path.join(save_dir, f"{partial_filename}.pdf")
                            page.pdf(path=partial_filepath, format="A4", print_background=True)
                            self.ui_queue.put(("convert_log", f"Saved partial PDF: {partial_filename}.pdf"))
                            success = True
                        else:
                            self.ui_queue.put(("convert_log", "Page unavailable for partial save"))
                    except Exception as exc2:
                        self.ui_queue.put(("convert_log", f"Failed to save partial PDF: {exc2}"))
                    self.ui_queue.put(("convert_log", f"Failed to process {url} after {max_retries} attempts"))
            finally:
                if context:
                    context.close()
        return success

    def sanitize_filename(self, filename):
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return filename.strip()[:100]

    def _reset_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _append_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _open_output_folder(self):
        if not getattr(self, "save_dir", None):
            return
        try:
            if os.name == "nt":
                os.startfile(self.save_dir)
            elif os.name == "posix":
                import subprocess

                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", self.save_dir])
        except Exception:
            pass

    def process_ui_queue(self):
        try:
            while True:
                msg_type, payload = self.ui_queue.get_nowait()
                if msg_type == "extract_results":
                    self._apply_extract_results(payload)
                elif msg_type == "extract_error":
                    self._handle_extract_error(payload)
                elif msg_type == "convert_progress":
                    self.progress["value"] += payload
                elif msg_type == "convert_status":
                    self.status_label.config(text=payload)
                elif msg_type == "convert_log":
                    self._append_log(payload)
                elif msg_type == "convert_done":
                    stopped = payload.get("stopped", False)
                    error = payload.get("error")
                    self.running = False
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    if error:
                        self.status_label.config(text="Conversion failed")
                        messagebox.showerror("Error", error)
                        continue
                    self.status_label.config(text="Conversion stopped" if stopped else "Conversion completed")
                    if not stopped:
                        messagebox.showinfo("Info", "Processing finished!")
                        if self.open_folder_var.get():
                            self._open_output_folder()
        except queue.Empty:
            pass
        self.root.after(100, self.process_ui_queue)

    def on_closing(self):
        if self.running:
            if messagebox.askokcancel("Quit", "Conversion in progress. Quit anyway?"):
                self.stop_event.set()
                self.root.destroy()
        else:
            self.root.destroy()


def main(start_tab="extract"):
    root = tk.Tk()
    app = WebtoPDFApp(root, start_tab=start_tab)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
