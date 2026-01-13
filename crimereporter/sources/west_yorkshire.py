import re
import textwrap
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class WestYorkshireForce(Force):

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")
        urls = []
        for article in soup.find_all("article", class_="listing"):
            a_tag = article.find("a", href=True)
            if a_tag:
                full_url = urljoin(self.root, a_tag["href"])
                urls.append(full_url)
        return urls

    def extract_text(self) -> str:
        content_div = self.soup.find("div", class_="content")
        if content_div:
            paragraphs = content_div.find_all("p")
            wrapped = [textwrap.fill(p.get_text(strip=True), width=100) for p in paragraphs if p.get_text(strip=True)]
            return Force.clean_text("\n".join(wrapped))
        return ""

    def clean(self, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")

        # Clean gtm and tag_exp query params from <script src="">
        for tag in soup.find_all("script", src=True):
            src = tag["src"]
            cleaned_src = re.sub(r"([?&])gtm=[^&]*&?", r"\1", src)
            cleaned_src = re.sub(r"([?&])tag_exp=[\d~]*&?", r"\1", cleaned_src)
            cleaned_src = re.sub(r"[?&]$", "", cleaned_src)
            tag["src"] = cleaned_src

        # Remove "bottom:" inline style from sliding-popup
        for tag in soup.find_all(style=True):
            if tag.has_attr("identifier") and tag["identifier"] == "sliding-popup":
                style_value = tag["style"]
                parts = [s.strip() for s in style_value.split(";") if s.strip()]
                cleaned_parts = [p for p in parts if not p.lower().startswith("bottom:")]
                if cleaned_parts:
                    tag["style"] = "; ".join(cleaned_parts)
                else:
                    del tag["style"]

        return soup.prettify()

    def extract_id(self) -> str:
        link_tag = self.soup.find("link", rel="shortlink")
        if link_tag and link_tag.has_attr("href"):
            href = link_tag["href"]
            match = re.search(r"/node/(\d+)", href)
            if match:
                return match.group(1)
        return ""

    def extract_name(self) -> str:
        """No separate name field in West Yorkshire articles."""
        return ""

    def extract_title(self) -> str:
        title_tag = self.soup.find("title")
        if title_tag:
            raw_title = title_tag.get_text(strip=True)
            return raw_title.replace("| West Yorkshire Police", "").strip()
        return ""

    def extract_date(self) -> str:
        meta_tag = self.soup.find("meta", property="article:published_time")
        if meta_tag and meta_tag.has_attr("content"):
            try:
                dt = datetime.strptime(meta_tag["content"], "%Y-%m-%dT%H:%M:%S%z")
                return dt.astimezone().strftime("%Y-%m-%d %H:%M")
            except ValueError:
                return ""
        return ""

    def get_file_urls(self) -> list[str]:
        results: list[str] = []
        divs = self.soup.find_all("div", class_="content")
        for div in divs:
            images = div.find_all("img")
            for img in images:
                src = img.get("src", "")
                parsed = urlparse(src)
                clean_src = str(urlunparse(parsed._replace(query="")))
                results.append(urljoin(self.root, clean_src))
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
