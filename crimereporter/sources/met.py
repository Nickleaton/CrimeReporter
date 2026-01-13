import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class MetPoliceForce(Force):

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")
        urls = []
        for article in soup.find_all("article"):
            a_tag = article.find("a", class_="panel__link")
            if a_tag and "href" in a_tag.attrs:
                full_url = urljoin(self.root, a_tag["href"])
                urls.append(full_url)
        return urls

    def extract_text(self) -> str:
        div = self.soup.find("div", class_="panel__text")
        if div:
            paragraphs = []
            for p in div.find_all("p"):
                text = p.get_text()
                if text:
                    paragraphs.append(Force.clean_text(text))
            return "\n\n".join(paragraphs)
        return ""

    def clean(self, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")

        # Remove nonce attributes
        for tag in soup.find_all(attrs={"nonce": True}):
            del tag["nonce"]

        # Remove CSRF token content
        meta_tag = soup.find("meta", attrs={"name": "csrf-token"})
        if meta_tag and meta_tag.has_attr("content"):
            del meta_tag["content"]

        # Remove authenticity_token values
        for input_tag in soup.find_all("input", attrs={"name": "authenticity_token", "type": "hidden"}):
            if input_tag.has_attr("value"):
                del input_tag["value"]

        # Clean up signed links
        for a_tag in soup.find_all("a", class_="button", href=True):
            original_href = a_tag["href"]
            cleaned_href = re.sub(r"([?&])(timestamp|expires_at|signature)=\w+&?", r"\1", original_href)
            cleaned_href = re.sub(r"[?&]$", "", cleaned_href)
            a_tag["href"] = cleaned_href

        return soup.prettify()

    def extract_id(self) -> str | None:
        meta_tag = self.soup.find("meta", property="og:url")
        if meta_tag and meta_tag.has_attr("content"):
            url = meta_tag["content"]
            match = re.search(r"-([0-9]+)$", url)
            if match:
                return match.group(1)
        return None

    def extract_name(self) -> str:
        """Met Police articles do not expose a separate name field."""
        return ""

    def extract_title(self) -> str:
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.replace(" | Metropolitan Police", "").strip()
        return ""

    def extract_date(self) -> str:
        time_tag = self.soup.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            return time_tag["datetime"].strip()[:-3]
        return ""

    def get_file_urls(self) -> list[str]:
        """Return a list of absolute download file and image URLs found in the page."""
        results: list[str] = []

        # Existing "download all" link
        # link = self.soup.find('a', id='related-media__download-all-button')
        # if link and link.has_attr('href'):
        #     href = link['href'].strip()
        #     if href:
        #         results.append(href)

        # Find all images
        for img in self.soup.find_all("img"):
            src = img.get("src")
            if src:
                src = src.strip()
                if src:
                    results.append(src)

        return results

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
