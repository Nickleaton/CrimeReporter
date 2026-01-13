import logging
import re
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force

logger = logging.getLogger(__name__)


class TypeAPoliceForce(Force):
    INCLUDED_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "strong", "em"]

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")

        urls = []
        for a_tag in soup.find_all("a", class_=["c-news-panel", "c-news-results_title"]):
            href = a_tag.get("href")
            if href:
                full_url = urljoin(self.root, href)
                urls.append(full_url)
        return urls

    def extract_text(self) -> str:
        divs = self.soup.select("div.cms-content, div.c-news-article, div.c-news-article.s-cms, cms-content")
        all_text = []

        for div in divs:
            # Replace <a> tags with "text (URL)"
            for a in div.find_all("a", href=True):
                href = a["href"].strip()
                link_text = a.get_text(strip=True)
                a.replace_with(f" {link_text} ({href}) ")

            # Include paragraphs, headers, list items, and divs with text
            for element in div.find_all(self.INCLUDED_TAGS + ["div"]):
                # Skip irrelevant divs
                text = element.get_text(strip=True)
                if not text or text == "\xa0":  # ignore &nbsp;
                    continue

                name = element.name or ""

                # Bullet lists
                if name == "li" or text.lstrip().startswith("-"):
                    text = f"• {text.lstrip('-').strip()}"

                # Headings
                if name.startswith("h"):
                    all_text.append("")
                    all_text.append(text)
                    all_text.append("")
                    continue

                # Regular paragraphs
                if name == "p":
                    all_text.append(text)
                    all_text.append("")
                    continue

                # Default case
                all_text.append(text)

        return Force.clean_text("\n".join(all_text))

    def clean(self, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")
        timestamp_div = soup.find("div", class_="u-hidden u-no-print")
        if timestamp_div:
            timestamp_div.decompose()
        return soup.prettify()

    def extract_id(self) -> str:
        body_tag = self.soup.find("body")
        return body_tag.get("data-content-id", "") if body_tag else ""

    def extract_name(self) -> str:
        """No explicit name field in Type A articles."""
        return ""

    def extract_title(self) -> str:
        title_tag = self.soup.find("h1", class_="c-page-header_title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return ""

    def extract_date(self) -> str:
        time_info = self.soup.find("span", class_="c-meta-tag-time_info")
        if time_info:
            spans = time_info.find_all("span", recursive=False)
            if len(spans) >= 4:
                time_text = spans[2].get_text(strip=True)
                date_text = spans[3].get_text(strip=True)
                try:
                    day, month, year = date_text.split("/")
                    return f"{year}-{month}-{day} {time_text}"
                except ValueError:
                    return ""
        return ""

    def extract_urls_from_tag(self, div, tag: str, attr: str) -> list[str]:
        urls: list[str] = []
        for element in div.find_all(tag):
            value: str | None = element.get(attr)
            if not value or value.startswith("data:image"):
                logger.warning("Skipping DATA IMAGE")
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

        classes_to_search = [
            "c-news-article",
            "cms-content",
            "image-block",
            "x_elementToProof",
        ]
        class_pattern = re.compile(r"(" + "|".join(classes_to_search) + r")")

        divs = self.soup.find_all("div", class_=class_pattern)

        for div in divs:
            results.extend(self.extract_urls_from_tag(div, "img", "src"))
            results.extend(self.extract_urls_from_tag(div, "source", "srcset"))

        return sorted(set(results))

    def get_zip_files(self) -> FileDirectory:
        return FileDirectory()

    def get_embedded_files(self) -> FileDirectory:
        """Return FileRecords for base64-embedded images (already saved to disk)."""
        return FileDirectory()

    def get_video_files(self) -> FileDirectory:
        """Return FileRecords for associated video files (YouTube, MP4, etc.)."""
        return FileDirectory()
