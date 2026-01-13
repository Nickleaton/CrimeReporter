import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class CPSSource(Force):

    def fetch_latest_urls(self) -> list[str]:
        """Fetch all news article URLs from the CPS news page."""
        fetcher = Fetcher()
        text = fetcher.fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")
        urls = []
        for item in soup.select("div.teaser h3.teaser__title a"):
            href = item.get("href")
            if href:
                full_url = urljoin(self.root, href)
                urls.append(full_url)
        return urls

    def extract_text(self) -> str:
        # Find all possible content containers
        divs = self.soup.find_all(
            "div",
            class_=[
                "news-story__content",
                "cms-content",
                "c-news-article",
                "cps-content__body",
            ],
        )
        all_paragraphs = []

        for div in divs:
            for p in div.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    all_paragraphs.append(text)

        return Force.clean_text("\n".join(all_paragraphs))

    def clean(self, text: str) -> str:
        return text

    def get_file_urls(self) -> list[str]:
        """Extract image URLs from the page."""
        urls: set[str] = set()
        for img in self.soup.find_all("img"):
            src = img.get("src")
            if src and src.startswith("/sites/"):
                full_url = urljoin(self.root, src)
                urls.add(full_url)
        return list(urls)

    def extract_id(self) -> str:
        link_tag = self.soup.find("link", rel="shortlink")
        if link_tag and "href" in link_tag.attrs:
            url = link_tag["href"]
            match = re.search(r"/(\d+)$", url)
            if match:
                return match.group(1)
        return ""

    def extract_name(self) -> str:
        """CPS pages don’t have a distinct name field, return empty string."""
        return ""

    def extract_title(self) -> str:
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.replace(" | The Crown Prosecution Service", "").strip()
        return ""

    def extract_date(self) -> str:
        time_tag = self.soup.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            return time_tag["datetime"].strip().replace("T", " ")[:-3]
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
