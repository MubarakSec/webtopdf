import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Set, Optional
from ..utils.logger import app_logger

class URLExtractor:
    def __init__(self, user_agent: str = "Mozilla/5.0"):
        self.headers = {"User-Agent": user_agent}

    def extract_links(self, 
                      url: str, 
                      same_domain_only: bool = True, 
                      deduplicate: bool = True, 
                      skip_non_http: bool = True) -> List[Tuple[str, str]]:
        """Extract links from a given URL."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        app_logger.info(f"Starting extraction for URL: {url}")

        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            app_logger.error(f"Failed to fetch URL {url}: {exc}")
            raise Exception(f"Failed to fetch URL: {exc}")

        soup = BeautifulSoup(response.text, "html.parser")
        raw_links = soup.find_all("a", href=True)
        base_domain = urlparse(url).netloc

        seen: Set[str] = set()
        results: List[Tuple[str, str]] = []

        for link in raw_links:
            href = link.get("href", "").strip()
            if not href:
                continue
            
            # Filter non-http links
            if skip_non_http:
                if (href.startswith("mailto:") or 
                    href.startswith("javascript:") or 
                    href.startswith("#") or 
                    href.startswith("tel:")):
                    continue

            full_url = urljoin(url, href)
            
            # Normalize URL (remove fragment)
            parsed_full = urlparse(full_url)
            normalized_url = parsed_full._replace(fragment="").geturl()

            # Filter by domain
            if same_domain_only:
                if parsed_full.netloc and parsed_full.netloc != base_domain:
                    continue

            # Deduplicate
            if deduplicate and normalized_url in seen:
                continue

            seen.add(normalized_url)
            text = link.get_text(strip=True) or "(No text)"
            results.append((text, normalized_url))

        app_logger.info(f"Extraction complete for {url}. Found {len(results)} links.")
        return results
