import hashlib
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from dateutil import parser

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class LancsPoliceForce(Force):
    INCLUDED_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "strong", "em"]

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")

        urls = []
        container = soup.find("div", class_="container home-page")
        if container:
            seen = set()
            # Find all <a> tags containing <h3> inside this container
            for a_tag in container.find_all("a"):
                if a_tag.find("h3"):
                    href = a_tag.get("href")
                    if href:
                        full_url = urljoin(self.root, href)
                        if full_url not in seen:
                            urls.append(full_url)
                            seen.add(full_url)
        return urls

    def extract_text(self) -> str:
        # Select the main article container
        container = self.soup.select_one("div.container.news-article")
        if not container:
            return ""

        all_text = []

        # Replace <a> tags with "text (URL)"
        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            link_text = a.get_text(strip=True)
            a.replace_with(f"{link_text} ({href})")

        # Extract all heading and paragraph content
        for element in container.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = element.get_text(strip=True)
            if not text or text == "\xa0":
                continue

            tag = element.name

            # Headings
            if tag.startswith("h"):
                all_text.append("")
                all_text.append(text)
                all_text.append("")
                continue

            # Paragraphs
            if tag == "p":
                all_text.append(text)
                all_text.append("")
                continue

            # List items
            if tag == "li":
                all_text.append(f"• {text}")
                continue

        # Join and clean
        return Force.clean_text("\n".join(all_text))

    def clean(self, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")
        timestamp_div = soup.find("div", class_="u-hidden u-no-print")
        if timestamp_div:
            timestamp_div.decompose()
        return soup.prettify()

    def extract_id(self) -> str:
        title = self.extract_title()
        digest = hashlib.sha1(title.encode()).hexdigest()
        return str(int(digest, 16) % 1_000_000)

    def extract_name(self) -> str:
        """No explicit name field in Type A articles."""
        return ""

    def extract_title(self) -> str:
        container = self.soup.select_one("div.container.news-article")
        if not container:
            return ""

        title_tag = container.find("h2")
        return title_tag.get_text(strip=True) if title_tag else ""

    def extract_date(self) -> str:
        container = self.soup.select_one("div.container.news-article")
        if not container:
            return ""

        # find the first <p> after the <h2>
        h2 = container.find("h2")
        if not h2:
            return ""

        p = h2.find_next("p")
        if not p:
            return ""

        date_text = p.get_text(strip=True)

        # Parse natural language date like: "Monday, November 24, 2025"
        try:
            dt = parser.parse(date_text)
            return dt.strftime("%Y-%m-%d")
        except Exception:
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

        # Target the correct container
        container = self.soup.select_one("div.container.news-article")
        if not container:
            return results

        # Extract <img src="">
        results.extend(self.extract_urls_from_tag(container, "img", "src"))

        # Extract <source srcset="">
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
