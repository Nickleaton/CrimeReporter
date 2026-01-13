import hashlib
import html
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class DorsetForce(Force):
    def fetch_latest_urls(self) -> list[str]:
        """Fetches the latest Dorset Police news article URLs from the root page.

        Returns:
            list[str]: Fully resolved URLs for news articles found in '.articleList li a[href]'.
        """
        text = Fetcher().fetch(self.root)
        if not text:
            return []

        soup = BeautifulSoup(text, "html.parser")

        # Each <li> contains an <a> linking to a /news-article/... page
        urls = [
            urljoin(self.root, a["href"].strip())
            for a in soup.select(".articleList li a[href]")
            if a["href"].startswith("/news-article/")
        ]

        # Remove duplicates while preserving order
        return list(dict.fromkeys(urls))

    def extract_text(self) -> str:
        """Extracts and cleans the main article text from the Dorset Police article page.

        Returns:
            str: The combined cleaned text from <div class="videoContainer"> inside the article.
        """
        # Select the <div class="videoContainer"> within the <article itemprop="articleBody">
        container = self.soup.select_one('article[itemprop="articleBody"] div.videoContainer')
        if not container:
            return ""
        return Force.clean_text(container.text)

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
        h2 = self.soup.select_one('article[itemprop="articleBody"] h2[itemprop="headline"]')
        if h2:
            return h2.get_text(strip=True)
        return ""

    def extract_date(self) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d 12:00")

    @staticmethod
    def clean_url(url: str | bytes) -> str:
        if isinstance(url, bytes):
            url = url.decode("utf-8", errors="ignore")
        url = html.unescape(url.strip())
        parts = urlsplit(url)

        path = parts.path

        # Keep only the base Persisted.Media.File path (strip /r, /t, etc.)
        # Matches up to the GUID and stops
        match = re.search(r"(/Persisted\.Media\.File/News/[0-9a-fA-F-]{36})", path)

        if match:
            path = match.group(1)
        # Force all components to str
        scheme = str(parts.scheme)
        netloc = str(parts.netloc)
        path = str(path)
        result: str = urlunsplit((scheme, netloc, path, "", ""))
        return result

    def get_file_urls(self) -> list[str]:
        results = set()

        # Main image(s)
        for img in self.soup.select('figure img[itemprop="image"]'):
            src = img.get("src")
            if src:
                src = html.unescape(src)  # decode &amp; → &
                results.add(urljoin(self.root, src))

        # Gallery images
        for a_tag in self.soup.select("a.gallery[href]"):
            href = a_tag.get("href")
            if href:
                href = html.unescape(href)  # decode &amp; → &
                results.add(urljoin(self.root, href))

        return sorted(results)

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
