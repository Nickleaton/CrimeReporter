import re
from collections import defaultdict
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class AvonSomersetForce(Force):

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")

        urls = []
        for a_tag in soup.find_all("a", class_="asp-card__title-link"):
            href = a_tag.get("href")
            if href:
                full_url = urljoin(self.root, href)
                urls.append(full_url)
        return urls

    def extract_text(self) -> str:
        # Find all possible content containers
        divs = self.soup.find_all("div", class_=["news-story__content", "cms-content", "c-news-article"])
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
        body_tag = self.soup.find("body")
        if not body_tag:
            return ""

        class_attr = body_tag.attrs.get("class")
        if not class_attr:
            return ""

        for cls in class_attr:
            match = re.match(r"postid-(\d+)", cls)
            if match:
                return match.group(1)
        return ""

    def extract_name(self) -> str:
        """No explicit name field in Type A articles."""
        return ""

    def extract_title(self) -> str:
        return self.extract_meta("og:title").replace(" | Avon and Somerset Police", "")

    def extract_date(self) -> str:
        meta_tag = self.soup.find("meta", {"property": "article:published_time"})
        if not meta_tag:
            return ""
        content = meta_tag.get("content")
        if not content:
            return ""
        dt = datetime.fromisoformat(content.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")

    def get_file_urls(self) -> list[str]:
        """Return a sorted list of unique highest-resolution image URLs, excluding 'crest.png' and '.webp'."""
        urls = []

        # Collect all <img> sources
        for img in self.soup.find_all("img"):
            src = img.get("src")
            if src:
                urls.append(src)

        # Collect all <source> URLs from srcset
        for source in self.soup.find_all("source"):
            srcset = source.get("srcset")
            if srcset:
                for part in srcset.split(","):
                    url = part.strip().split()[0]
                    urls.append(url)

        # Filter out unwanted files
        urls = [
            u
            for u in urls
            if not u.endswith("crest.png")
            and not u.endswith(".webp")
            and not u.split("/")[-1].startswith("Social-media-stock")
        ]

        # Group files by base name
        images_by_base = defaultdict(list)
        for url in urls:
            filename = url.split("/")[-1]
            match = re.match(r"(.*?)(?:-(\d+)x(\d+))?(\.\w+)$", filename)
            if match:
                base_name, width, height, ext = match.groups()
                w, h = int(width) if width else 0, int(height) if height else 0
                images_by_base[base_name + ext].append((w, h, url))
            else:
                # fallback if filename doesn't match pattern
                images_by_base[filename].append((0, 0, url))

        # Select the largest resolution image for each base
        highest_res_urls = []
        for versions in images_by_base.values():
            largest = max(versions, key=lambda x: x[0] * x[1])
            highest_res_urls.append(largest[2])

        return sorted(highest_res_urls)

    def get_zip_files(self) -> FileDirectory:
        return FileDirectory()

    def get_embedded_files(self) -> FileDirectory:
        """Return FileRecords for base64-embedded images (already saved to disk)."""
        return FileDirectory()

    def get_video_files(self) -> FileDirectory:
        """Return FileRecords for associated video files (YouTube, MP4, etc.)."""
        return FileDirectory()
