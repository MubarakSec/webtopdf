import customtkinter as ctk
import threading
import tkinter as tk
from tkinter import messagebox
from ...core.extractor import URLExtractor
from ..components.scrollable_link_frame import ScrollableLinkFrame

class ExtractionTab(ctk.CTkFrame):
    def __init__(self, master, parent_app):
        super().__init__(master)
        self.parent_app = parent_app
        self.extractor = URLExtractor()

        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(
            self, text="URL Link Extractor", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.grid(row=0, column=0, padx=20, pady=(0, 20), sticky="w")

        # Input Frame
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.url_label = ctk.CTkLabel(self.input_frame, text="Target URL:")
        self.url_label.grid(row=0, column=0, padx=(20, 10), pady=20)

        self.url_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="https://example.com"
        )
        self.url_entry.grid(row=0, column=1, padx=0, pady=20, sticky="ew")

        self.extract_btn = ctk.CTkButton(
            self.input_frame, 
            text="Extract Links", 
            command=self.start_extraction
        )
        self.extract_btn.grid(row=0, column=2, padx=20, pady=20)

        # Options
        self.options_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.options_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="w")

        self.same_domain_var = tk.BooleanVar(value=True)
        self.same_domain_check = ctk.CTkCheckBox(
            self.options_frame, text="Same Domain Only", 
            variable=self.same_domain_var
        )
        self.same_domain_check.pack(side="left", padx=(0, 20))

        self.dedupe_var = tk.BooleanVar(value=True)
        self.dedupe_check = ctk.CTkCheckBox(
            self.options_frame, text="Deduplicate", 
            variable=self.dedupe_var
        )
        self.dedupe_check.pack(side="left", padx=(0, 20))

        # Results Frame
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.grid(row=2, column=0, padx=20, pady=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)

        # Scrollable list of checkboxes
        self.scrollable_frame = ScrollableLinkFrame(self.results_frame, label_text="Extracted Links")
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Selection Actions
        self.selection_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.selection_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        self.select_all_btn = ctk.CTkButton(
            self.selection_frame, text="Select All", width=80, 
            command=self.scrollable_frame.select_all
        )
        self.select_all_btn.pack(side="left", padx=(0, 10))

        self.deselect_all_btn = ctk.CTkButton(
            self.selection_frame, text="Deselect All", width=80, 
            command=self.scrollable_frame.deselect_all
        )
        self.deselect_all_btn.pack(side="left")

        # Actions Frame
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        self.copy_btn = ctk.CTkButton(
            self.actions_frame, text="Copy Selected", 
            command=self.copy_selected, width=120
        )
        self.copy_btn.pack(side="left", padx=(0, 10))

        self.send_btn = ctk.CTkButton(
            self.actions_frame, text="Send Selected to Converter", 
            command=self.send_to_converter, 
            fg_color="green", hover_color="darkgreen"
        )
        self.send_btn.pack(side="right")

    def start_extraction(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.extract_btn.configure(state="disabled", text="Extracting...")
        self.scrollable_frame.clear()
        
        thread = threading.Thread(target=self.run_extraction, args=(url,))
        thread.daemon = True
        thread.start()

    def run_extraction(self, url):
        try:
            links = self.extractor.extract_links(
                url, 
                same_domain_only=self.same_domain_var.get(),
                deduplicate=self.dedupe_var.get()
            )
            self.after(0, lambda: self.finish_extraction(links))
        except Exception as e:
            self.after(0, lambda: self.handle_error(str(e)))

    def finish_extraction(self, links):
        self.extract_btn.configure(state="normal", text="Extract Links")
        
        for text, url in links:
            self.scrollable_frame.add_link(text, url)
        
        if not links:
            messagebox.showinfo("Info", "No links found.")

    def handle_error(self, error_msg):
        self.extract_btn.configure(state="normal", text="Extract Links")
        messagebox.showerror("Extraction Error", error_msg)

    def copy_selected(self):
        selected = self.scrollable_frame.get_selected_urls()
        if not selected:
            messagebox.showwarning("Warning", "No links selected")
            return
        self.parent_app.clipboard_clear()
        self.parent_app.clipboard_append("\n".join(selected))
        messagebox.showinfo("Success", f"{len(selected)} links copied to clipboard!")

    def send_to_converter(self):
        selected = self.scrollable_frame.get_selected_urls()
        if not selected:
            messagebox.showwarning("Warning", "No links selected")
            return
        self.parent_app.send_to_converter(selected)
