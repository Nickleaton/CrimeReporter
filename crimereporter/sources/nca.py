from datetime import datetime
import hashlib
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class NCAForce(Force):
    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")

        urls: list[str] = []

        # Select ALL blog posts (leading + normal)
        for post in soup.select('div[itemprop="blogPost"]'):
            header = post.find("div", class_="page-header")
            if not header:
                continue

            a_tag = header.find("a", href=True)
            if not a_tag:
                continue

            urls.append(urljoin(self.root, a_tag["href"]))

        # Deduplicate, preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def extract_text(self) -> str:
        body = self.soup.find("div", itemprop="articleBody")
        if not body:
            return ""

        paragraphs = [
            p.get_text() for p in body.find_all("p") if p.get_text(strip=True)
        ]

        return "\n\n".join(paragraphs)

    def clean(self, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")
        return soup.prettify()

    def extract_id(self) -> str | None:
        title = self.extract_title()
        digest = hashlib.sha1(title.encode()).hexdigest()
        return str(int(digest, 16) % 1_000_000)

    def extract_name(self) -> str:
        """
        NCA exposes the subject name explicitly.
        Prefer the article headline.
        """
        h = self.soup.find("h2", itemprop="headline")
        if h:
            return h.get_text(strip=True)
        return ""

    def extract_title(self) -> str:
        """
        Title exists in both <title> and <h2>.
        Use <title> as fallback, but clean branding.
        """
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.replace(
                " - National Crime Agency", ""
            ).strip()
        return ""

    def extract_date(self) -> str:
        """
        Extract the date of the article:
        - First, looks for <strong> inside <p> in articleBody.
        - Parses date in format 'DD Month YYYY'.
        Returns date as 'YYYY-MM-DD' string if found, else empty string.
        """
        # Find all <strong> tags inside <p> elements
        strong_tags = self.soup.select("div[itemprop='articleBody'] p strong")

        for strong in strong_tags:
            date_str = strong.get_text(strip=True)
            try:
                dt = datetime.strptime(date_str, "%d %B %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue  # Not a date, try next strong tag

        return ""  # No valid date found

    def get_file_urls(self) -> list[str]:
        """
        Return absolute image URLs from article body + OpenGraph image
        """
        results: list[str] = []

        article = self.soup.find("div", itemprop="articleBody")
        if article:
            for img in article.select("img[src]"):
                src = img.get("src", "").strip()
                if src:
                    results.append(urljoin(self.root, src))

        # OpenGraph image (often higher quality)
        og = self.soup.find("meta", property="og:image")
        if og and og.get("content"):
            results.append(og["content"].strip())

        # Deduplicate while preserving order
        return list(dict.fromkeys(results))

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
