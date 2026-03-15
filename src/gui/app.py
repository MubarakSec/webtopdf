import customtkinter as ctk
import os
from PIL import Image
from .tabs.extraction_tab import ExtractionTab
from .tabs.conversion_tab import ConversionTab
from ..utils.helpers import get_asset_path

class WebToPDFApp(ctk.CTk):
    def __init__(self, start_tab="extract"):
        super().__init__()

        self.title("Web to PDF Toolkit - Pro")
        self.geometry("1100x750")
        self.minsize(1000, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Try to set the application icon
        try:
            icon_path = get_asset_path("app.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # Set theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="WebToPDF", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.extract_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="Link Extractor", 
            command=self.show_extraction,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w"
        )
        self.extract_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.convert_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="PDF Converter", 
            command=self.show_conversion,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w"
        )
        self.convert_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Appearance mode setting
        self.appearance_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance:", anchor="w")
        self.appearance_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_optionmenu = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        self.appearance_optionmenu.grid(row=6, column=0, padx=20, pady=(10, 20))

        # Content areas (Tabs)
        self.extraction_tab = ExtractionTab(self, self)
        self.conversion_tab = ConversionTab(self, self)

        # Default view
        if start_tab == "convert":
            self.show_conversion()
        else:
            self.show_extraction()

    def show_extraction(self):
        self.conversion_tab.grid_forget()
        self.extraction_tab.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.extract_btn.configure(fg_color=("gray75", "gray25"))
        self.convert_btn.configure(fg_color="transparent")

    def show_conversion(self):
        self.extraction_tab.grid_forget()
        self.conversion_tab.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.convert_btn.configure(fg_color=("gray75", "gray25"))
        self.extract_btn.configure(fg_color="transparent")

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def send_to_converter(self, urls):
        """Send URLs from extraction tab to conversion tab."""
        self.conversion_tab.add_urls(urls)
        self.show_conversion()

    def on_closing(self):
        """Handle application shutdown gracefully."""
        # Stop the converter if it is running
        if hasattr(self, 'conversion_tab'):
            self.conversion_tab.converter.stop()
        self.destroy()

