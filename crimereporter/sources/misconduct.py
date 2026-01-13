from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class MisconductSource(Force):
    IGNORE_IMAGES = [
        "misconduct999-newsletter.jpg",
        "twitter-ad-3.png",
        "news.jpg",
        "uknewsmedia-logo-2021-black.png",
    ]

    def fetch_latest_urls(self) -> list[str]:
        """Fetch the latest misconduct article URLs."""
        fetcher = Fetcher()
        text = fetcher.fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")
        urls: list[str] = []

        # Each article link is in the <h2 class="entry-title"><a href="...">
        for header in soup.select("h2.entry-title a[href]"):
            href = header["href"]
            full_url = urljoin(self.root, href)
            urls.append(full_url)

        return urls

    def extract_text(self) -> str:
        """Extract the main article text."""
        content = self.soup.find("div", class_="entry-content")
        if content:
            paragraphs = content.find_all("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs)
        return ""

    def clean(self, text: str) -> str:
        """Optional text cleaning."""
        return text.strip()

    def get_file_urls(self) -> list[str]:
        """Extract image URLs from the article, excluding certain files."""
        image_tags = self.soup.find_all("img")
        image_urls = [
            urljoin(self.root, img["src"])
            for img in image_tags
            if img.get("src") and not any(ignored in img["src"] for ignored in self.IGNORE_IMAGES)
        ]
        return image_urls

    def extract_date(self) -> str:
        """Extract the publication date from the meta tag and format as yyyy-mm-dd hh:mm."""
        meta_tag = self.soup.find("meta", property="article:published_time")
        if meta_tag and meta_tag.get("content"):
            content = meta_tag["content"]
            try:
                # Try to parse any common date-time format
                dt = datetime.fromisoformat(content.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    dt = datetime.strptime(content[:16], "%Y-%m-%dT%H:%M")
                    return dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass
        return ""

    def extract_id(self) -> str:
        """Extract a unique identifier for the article from the shortlink."""
        link_tag = self.soup.find("link", rel="shortlink")
        if link_tag and "href" in link_tag.attrs:
            href = link_tag["href"]
            if "p=" in href:
                return href.split("p=")[1]
        return ""

    def extract_name(self) -> str:
        """Extract the name of the officer involved."""
        name_tag = self.soup.find("p", class_="officer")
        if name_tag:
            name_link = name_tag.find("a", class_="discreet")
            if name_link:
                return name_link.get_text(strip=True)
        return ""

    def extract_title(self) -> str:
        """Extract the article title without the '- Misconduct999' suffix."""
        meta_tag = self.soup.find("meta", property="og:title")
        if meta_tag and meta_tag.has_attr("content"):
            title = meta_tag["content"].strip()
            suffix = " - Misconduct999"
            if title.endswith(suffix):
                title = title[: -len(suffix)].strip()
            return title
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
