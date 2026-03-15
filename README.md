# Web to PDF Toolkit - Pro 🚀

A high-performance, locally-hosted desktop application designed to extract links from webpages and batch-convert them into high-fidelity PDFs. Built with modern UI/UX principles and powered by **Playwright**, this toolkit effortlessly handles dynamic, JavaScript-heavy Single Page Applications (SPAs).

---

## 📸 Interface Overview

### 1. Advanced Link Extractor
Scrape, filter, and deduplicate links from any webpage instantly. 
![Link Extractor](images/url_extractor_screenshot2.png)

### 2. High-Fidelity PDF Converter
Queue multiple URLs for batch conversion with real-time logs and progress tracking.
![PDF Converter](images/pdf_converter_screenshot.png)

---

## 🌟 Key Features

*   **Intelligent Link Extraction:** 
    *   Targeted scraping powered by `BeautifulSoup`.
    *   Automated "Same Domain" filtering and URL deduplication.
    *   Smart fragment stripping and protocol auto-correction.
    *   Interactive scrollable selection with one-click transfer to the conversion queue.

*   **Industrial-Grade PDF Rendering:**
    *   Utilizes a headless **Chromium browser via Playwright** to ensure exact visual replication, even for modern frameworks (React, Vue, Angular).
    *   Built-in retry mechanisms and timeouts for unstable networks.
    *   *Failsafe rendering:* Automatically attempts to save partial PDFs if the primary rendering fails.

*   **Modern, Agent-Ready UI/UX:**
    *   Sleek interface constructed with `CustomTkinter`.
    *   Full support for **Light, Dark, and System appearance modes**.
    *   Thread-safe architecture ensures the UI remains responsive during heavy batch operations.
    *   Comprehensive execution logs and real-time progress bars.

---

## 🛠️ Architecture

The project has been rigorously refactored to follow a strictly decoupled, modular architecture:

```text
webtopdf/
├── main.py               # Unified application entry point
├── requirements.txt      # Dependency manifest
├── .venv/                # Isolated virtual environment (ignored in git)
├── images/               # Visual documentation assets
└── src/
    ├── core/             # Headless business logic (extractor.py, converter.py)
    ├── gui/              # CustomTkinter interface (tabs, components, app.py)
    └── utils/            # OS-level helpers and sanitization
```

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   Git

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/webtopdf.git
   cd webtopdf
   ```

2. **Initialize a Virtual Environment:**
   *(Recommended to prevent system-level package conflicts)*
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Rendering Engine:**
   Install the necessary Playwright browser binaries and system dependencies:
   ```bash
   playwright install chromium
   playwright install-deps chromium
   ```

---

## 💻 Usage

Ensure your virtual environment is active, then launch the application:

```bash
# Launch the main application (Defaults to Extractor)
python main.py

# Launch directly into the PDF Converter tab
python main.py --tab convert
```

---

## 🤝 Contributing

Contributions are welcome! Since the GUI is entirely decoupled from the business logic (`src/core`), developers can easily integrate the extraction and conversion classes into web APIs, CLIs, or alternate interfaces without modifying the core behavior.

## 📄 License
This project is licensed under the MIT License.
