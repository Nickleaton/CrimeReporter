import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class PSNIForce(Force):

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")

        urls = []
        # Each card has an <a> inside .card-detail-top
        for a_tag in soup.select(".card-detail-top a[href]"):
            href = a_tag["href"].strip()
            full_url = urljoin(self.root, href)
            urls.append(full_url)

        return urls

    def extract_text(self) -> str:
        """Extracts the main article text from <div class="editor">."""
        divs = self.soup.find_all("div", class_="editor")
        all_paragraphs = []

        for div in divs:
            for p in div.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    all_paragraphs.append(text)

        return Force.clean_text("\n".join(all_paragraphs))

    def clean(self, text: str) -> str:
        return text

    def extract_id(self) -> str:
        title = self.extract_title()
        digest = hashlib.sha1(title.encode()).hexdigest()
        return str(int(digest, 16) % 1_000_000)

    def extract_name(self) -> str:
        """No explicit name field in Type A articles."""
        return ""

    def extract_title(self) -> str:
        return self.extract_meta("og:title").replace(" | PSNI", "")

    def extract_date(self) -> str:
        """Extracts and normalizes the date (YYYY-MM-DD)."""
        ul = self.soup.find("ul", class_="pipe font-tiny")
        if not ul:
            return ""

        li = ul.find("li")
        if not li:
            return ""

        date_text = li.get_text(strip=True)

        # Parse "13 October 2025" into "YYYY-MM-DD"
        try:
            dt = datetime.strptime(date_text, "%d %B %Y")
            return dt.strftime("%Y-%m-%d 12:00")
        except ValueError:
            return ""

    def extract_urls_from_tag(self, div, tag: str, attr: str) -> list[str]:
        urls: list[str] = []
        for element in div.find_all(tag):
            value: str | None = element.get(attr)
            if not value or value.startswith("data:image"):
                continue

            # For srcset, take first URL if multiple
            if attr == "srcset":
                value = value.split(",")[0].split()[0]

            if isinstance(value, bytes):
                value = value.decode()

            parsed = urlparse(value)
            clean_src = str(urlunparse(parsed._replace(query="")))
            urls.append(urljoin(self.root, clean_src))
        return urls

    def get_file_urls(self) -> list[str]:
        results: list[str] = []

        # Existing classes
        classes_to_search = [
            "c-news-article",
            "cms-content",
            "image-block",
            "x_elementToProof",
        ]
        class_pattern = re.compile(r"(" + "|".join(classes_to_search) + r")")

        # Find all relevant divs AND articles/figures
        containers = self.soup.find_all(["div", "article", "figure"], class_=class_pattern)

        # Include <article> and <figure> even if they don't match class_pattern
        containers.extend(self.soup.find_all(["article", "figure"]))

        for container in containers:
            results.extend(self.extract_urls_from_tag(container, "img", "src"))
            results.extend(self.extract_urls_from_tag(container, "source", "srcset"))

        return sorted(set(results))

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
