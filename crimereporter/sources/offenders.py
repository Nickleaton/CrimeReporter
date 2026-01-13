import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force
from crimereporter.utils.config import Config

config = Config()


class OffendersSource(Force):

    def fetch_urls_from_page(self, page: int) -> list[str]:
        """Fetch a page and extract offender URLs from it."""
        fetcher = Fetcher()
        url = f"{self.root}?page={page}"
        html = fetcher.fetch(url)

        soup = BeautifulSoup(html, "html.parser")
        urls = []

        for card in soup.select("div.card.mb-4.box-shadow"):
            link_tag = card.select_one("a.btn.btn-secondary")
            if link_tag:
                href = link_tag.get("href")
                if href:
                    match = re.search(r"offender\?id=(\d+)", href)
                    if match:
                        offender_id = match.group(1)
                        full_url = urljoin(self.root, f"offender?id={offender_id}")
                        urls.append(full_url)

        return urls

    def fetch_latest_urls(self) -> list[str]:
        """Fetch offender URLs from the first N pages."""
        all_urls = []
        for page in range(
            config.source.offender_source.start_page,
            config.source.offender_source.end_page + 1,
        ):
            page_urls = self.fetch_urls_from_page(page)
            all_urls.extend(page_urls)
        return all_urls

    def extract_text(self) -> str:
        """Extract the main article text from the Description section."""
        # Find the div where h2 text is "Description"
        description_div = None
        for div in self.soup.find_all("div", class_="p-3 mb-4 rounded"):
            h2 = div.find("h2")
            if h2 and h2.get_text(strip=True) == "Description":
                description_div = div
                break

        if description_div:
            # Extract all paragraph text inside the div
            paragraphs = description_div.find_all("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs)

        return ""

    def clean(self, text: str) -> str:
        """Optional text cleaning."""
        return text.strip()

    def get_file_urls(self) -> list[str]:
        """Extract the main offender image URLs from the page."""
        urls: set[str] = set()

        for img in self.soup.find_all("img", attrs={"data-bs-target": "#offender-photo"}, src=True):
            src = img["src"]
            if src.startswith("/uploads/"):
                full_url = urljoin(self.root, src)
                urls.add(full_url)

        return list(urls)

    def extract_date(self) -> str:
        date_tag = self.soup.find("a", class_="badge bg-secondary")
        if date_tag:
            # Store as datetime or string as needed
            return f"{date_tag.get_text(strip=True)} 00:00"
        return ""

    def extract_id(self) -> str:
        dispute_tags = self.soup.find_all("a", class_="btn-success", href=True)
        for tag in dispute_tags:
            href = tag["href"]
            if href.startswith("dispute"):
                query = urlparse(href).query
                params = parse_qs(query)
                return params.get("id", [""])[0]
        return ""

    def extract_name(self) -> str:
        dispute_tags = self.soup.find_all("a", class_="btn-success", href=True)
        for tag in dispute_tags:
            href = tag["href"]
            if href.startswith("dispute"):
                query = urlparse(href).query
                params = parse_qs(query)
                return params.get("name", [""])[0].replace("+", " ")
        return ""

    def extract_title(self) -> str:
        og_desc = self.soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()
        else:
            return self.soup.title.string.strip()

    def get_href_files(self) -> FileDirectory:
        """Return FileRecords for normal <a href> or <img src> URLs."""
        return FileDirectory()

    def get_zip_files(self) -> FileDirectory:
        return FileDirectory()

    def get_embedded_files(self) -> FileDirectory:
        """Return FileRecords for base64-embedded images (already saved to disk)."""
        return FileDirectory()

    def get_video_files(self) -> FileDirectory:
        """Return FileRecords for associated video files (YouTube, MP4, etc.)."""
        return FileDirectory()
