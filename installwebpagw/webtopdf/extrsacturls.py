import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class URLExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Extractor")
        self.root.geometry("800x600")
        
        # Variables
        self.url_var = tk.StringVar()
        self.checkboxes = []
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # URL Input Section
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Enter URL:").pack(side=tk.LEFT)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        extract_btn = ttk.Button(url_frame, text="Extract URLs", command=self.extract_urls)
        extract_btn.pack(side=tk.LEFT)
        
        # Results Section
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable Canvas
        self.canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Save Button
        save_btn = ttk.Button(main_frame, text="Save Selected URLs", command=self.save_urls)
        save_btn.pack(pady=5)
        
    def extract_urls(self):
        url = self.url_var.get()
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("Error", "Invalid URL format. Please include http:// or https://")
            return
        
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch URL: {str(e)}")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        
        # Clear previous checkboxes
        for cb in self.checkboxes:
            cb.destroy()
        self.checkboxes = []
        
        # Create new checkboxes
        for link in links:
            href = link.get('href')
            text = link.text.strip() or "[No Text]"
            if href:
                full_url = urljoin(url, href)
                self.create_checkbox_item(text, full_url)
                
    def create_checkbox_item(self, text, url):
        var = tk.BooleanVar(value=False)
        max_text_length = 50
        truncated_text = text[:max_text_length] + "..." if len(text) > max_text_length else text
        
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, pady=2)
        
        cb = ttk.Checkbutton(frame, variable=var)
        cb.pack(side=tk.LEFT)
        
        ttk.Label(frame, text=f"{truncated_text} -> {url}", wraplength=700).pack(side=tk.LEFT)
        
        self.checkboxes.append((frame, var, url))
        
    def save_urls(self):
        selected_urls = [url for (frame, var, url) in self.checkboxes if var.get()]
        if not selected_urls:
            messagebox.showwarning("Warning", "No URLs selected!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                for url in selected_urls:
                    f.write(url + "\n")
            messagebox.showinfo("Success", f"Saved {len(selected_urls)} URLs to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = URLExtractorApp(root)
    root.mainloop()
