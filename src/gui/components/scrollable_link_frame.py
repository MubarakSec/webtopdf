import customtkinter as ctk
import tkinter as tk

class LinkItem(ctk.CTkFrame):
    def __init__(self, master, text, url, on_remove=None, show_checkbox=True):
        super().__init__(master, fg_color="transparent")
        self.url = url
        self.on_remove = on_remove

        self.grid_columnconfigure(1, weight=1)

        if show_checkbox:
            self.checkbox = ctk.CTkCheckBox(self, text="")
            self.checkbox.grid(row=0, column=0, padx=(5, 0))
        else:
            self.checkbox = None

        # Shorten text and url for display
        display_text = f"{text[:80]}..." if len(text) > 80 else text
        display_url = f"{url[:120]}..." if len(url) > 120 else url
        
        self.label = ctk.CTkLabel(
            self, 
            text=f"{display_text}\n{display_url}", 
            anchor="w", 
            justify="left",
            font=ctk.CTkFont(size=11)
        )
        self.label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        if on_remove:
            self.remove_btn = ctk.CTkButton(
                self, text="✕", width=30, height=30, 
                fg_color="transparent", 
                text_color=("gray10", "gray90"),
                hover_color=("red", "darkred"),
                command=self.remove
            )
            self.remove_btn.grid(row=0, column=2, padx=(0, 5))

    def remove(self):
        if self.on_remove:
            self.on_remove(self)
        self.destroy()

    def is_selected(self):
        return self.checkbox.get() == 1 if self.checkbox else True

    def select(self):
        if self.checkbox:
            self.checkbox.select()

    def deselect(self):
        if self.checkbox:
            self.checkbox.deselect()

class ScrollableLinkFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, show_checkboxes=True, can_remove=False, **kwargs):
        super().__init__(master, **kwargs)
        self.items = []
        self.show_checkboxes = show_checkboxes
        self.can_remove = can_remove
        self.grid_columnconfigure(0, weight=1)

    def add_link(self, text, url):
        # Avoid duplicates in the UI if needed (logic can be here or in tab)
        item = LinkItem(
            self, text, url, 
            on_remove=self.remove_item if self.can_remove else None,
            show_checkbox=self.show_checkboxes
        )
        item.grid(row=len(self.items), column=0, padx=5, pady=2, sticky="ew")
        self.items.append(item)

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            # Rearrange grid
            self._rearrange_grid()

    def _rearrange_grid(self):
        for i, item in enumerate(self.items):
            item.grid(row=i, column=0, padx=5, pady=2, sticky="ew")

    def get_selected_urls(self):
        return [item.url for item in self.items if item.is_selected()]

    def get_all_urls(self):
        return [item.url for item in self.items]

    def clear(self):
        for item in self.items:
            item.destroy()
        self.items = []

    def select_all(self):
        for item in self.items:
            item.select()

    def deselect_all(self):
        for item in self.items:
            item.deselect()
