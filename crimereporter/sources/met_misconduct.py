from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force
from crimereporter.utils.config import Config

config = Config()


class MetMisconductForce(Force):
    """Extracts the latest misconduct hearing summary URLs from the Met Police site."""

    def fetch_latest_urls(self) -> list[str]:
        """Returns all misconduct outcome summary URLs from the listing."""
        fetcher = Fetcher()
        text = fetcher.fetch(self.root)

        soup = BeautifulSoup(text, "html.parser")
        urls = []

        for a in soup.select("li.result-item h3 a"):
            href = a.get("href")
            if href and href.endswith("-summary/"):
                urls.append(urljoin(self.root, href))

        return urls

    def clean(self, text: str) -> str:
        return text

    def extract_date(self) -> str:
        div = self.soup.find("div", class_="u-hidden u-no-print")
        if div:
            text = div.get_text(strip=True)
            # Extract the date part after "Current timestamp: "
            if "Current timestamp:" in text:
                ts_str = text.split("Current timestamp:")[1].strip()
                # Parse original format dd/mm/yyyy hh:mm:ss
                dt = datetime.strptime(ts_str, "%d/%m/%Y %H:%M:%S")
                # Convert to yyyy-mm-dd hh:mm
                return dt.strftime("%Y-%m-%d %H:%M")
        return ""

    def extract_id(self) -> str:
        body = self.soup.find("body")
        if body and body.has_attr("data-content-id"):
            return body["data-content-id"]
        return ""

    def extract_name(self) -> str:
        return self.extract_meta("g:description").replace(" outcome summary", "")

    def extract_title(self) -> str:
        return self.extract_meta("og:title")

    def extract_text(self) -> str:
        div = self.soup.find("div", class_="page-intro cms-content")
        if div:
            return "\n".join(s.strip() for s in div.strings if s.strip())
        return ""

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
