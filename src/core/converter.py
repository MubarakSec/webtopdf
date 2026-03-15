import os
import threading
from typing import List, Callable, Optional, Dict
from playwright.sync_api import sync_playwright, Browser, TimeoutError as PlaywrightTimeoutError
from ..utils.helpers import sanitize_filename
from ..utils.logger import app_logger

class PDFConverter:
    def __init__(self, 
                 headless: bool = True, 
                 max_retries: int = 3, 
                 timeout: int = 30000, 
                 user_agent: str = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/118.0.0.0 Safari/537.36")):
        self.headless = headless
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = user_agent
        self.stop_event = threading.Event()

    def convert_multiple(self, 
                         urls: List[str], 
                         save_dir: str, 
                         on_progress: Optional[Callable[[int], None]] = None,
                         on_status: Optional[Callable[[str], None]] = None,
                         on_log: Optional[Callable[[str], None]] = None) -> Dict[str, bool]:
        """Convert multiple URLs to PDF."""
        results = {}
        app_logger.info(f"Starting batch conversion of {len(urls)} URLs to {save_dir}")
        try:
            with sync_playwright() as playwright:
                app_logger.debug("Playwright initialized, launching browser.")
                browser = playwright.chromium.launch(headless=self.headless)
                try:
                    for index, url in enumerate(urls, start=1):
                        if self.stop_event.is_set():
                            app_logger.info("Conversion stopped by user.")
                            break
                        
                        success = self._convert_single(browser, url, save_dir, index, on_status, on_log)
                        results[url] = success
                        
                        if on_progress:
                            on_progress(1)
                finally:
                    app_logger.debug("Closing Playwright browser.")
                    browser.close()
        except Exception as exc:
            app_logger.error(f"Fatal Error during batch conversion: {exc}", exc_info=True)
            if on_log:
                on_log(f"Fatal Error: {exc}")
            raise exc
        
        app_logger.info("Batch conversion process completed.")
        return results

    def _convert_single(self, 
                        browser: Browser, 
                        url: str, 
                        save_dir: str, 
                        index: int,
                        on_status: Optional[Callable[[str], None]],
                        on_log: Optional[Callable[[str], None]]) -> bool:
        """Convert a single URL to PDF with retries."""
        for attempt in range(1, self.max_retries + 1):
            if self.stop_event.is_set():
                return False
            
            context = None
            page = None
            try:
                msg = f"Processing: {url} (Attempt {attempt}/{self.max_retries})"
                app_logger.info(msg)
                if on_status:
                    on_status(msg)
                
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=self.user_agent
                )
                page = context.new_page()
                
                # Navigate and wait for content
                page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                # Wait a bit longer for animations and lazy-loading
                page.wait_for_timeout(2000)

                title = page.title()
                filename = sanitize_filename(title) or f"page_{index}"
                filepath = os.path.join(save_dir, f"{filename}.pdf")

                # Generate PDF
                page.pdf(
                    path=filepath, 
                    format="A4", 
                    print_background=True,
                    margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"}
                )
                
                success_msg = f"Successfully converted and saved: {filepath}"
                app_logger.info(success_msg)
                if on_log:
                    on_log(f"Success: {filename}.pdf")
                return True
                
            except (PlaywrightTimeoutError, Exception) as exc:
                error_msg = f"Attempt {attempt} failed for {url}: {exc}"
                app_logger.warning(error_msg)
                if on_log:
                    on_log(error_msg)
                
                if attempt == self.max_retries:
                    app_logger.error(f"All {self.max_retries} attempts failed for {url}.")
                    # Try to save partial PDF on last attempt if page exists
                    self._save_partial(page, save_dir, index, on_log)
                    
            finally:
                if context:
                    context.close()
        
        return False

    def _save_partial(self, page, save_dir, index, on_log):
        """Attempt to save a partial PDF if possible."""
        try:
            if page and not page.is_closed():
                title = page.title()
                filename = sanitize_filename(title) or f"page_{index}_partial"
                filepath = os.path.join(save_dir, f"{filename}.pdf")
                page.pdf(path=filepath, format="A4", print_background=True)
                
                msg = f"Saved partial PDF: {filepath}"
                app_logger.info(msg)
                if on_log:
                    on_log(f"Saved partial PDF: {filename}.pdf")
                return True
        except Exception as e:
            app_logger.error(f"Failed to save partial PDF: {e}")
            if on_log:
                on_log("Failed to save partial PDF.")
        return False

    def stop(self):
        """Stop current conversion process."""
        app_logger.info("Stop signal received for conversion process.")
        self.stop_event.set()

    def reset(self):
        """Reset the stop event for a new run."""
        self.stop_event.clear()
