import hashlib
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.force import Force


class CrimeStoppersForce(Force):

    def clean(self, text: str) -> str:
        return text

    def fetch_latest_urls(self) -> list[str]:
        text = Fetcher().fetch(self.root)
        soup = BeautifulSoup(text, "html.parser")

        urls: list[str] = []

        # Select the gallery row
        gallery = soup.select_one('div.row.wanted-gallery')
        if not gallery:
            return []

        # Each wanted person is a column in the gallery
        for col in gallery.select('div.col-md-4, div.col-lg-3'):
            a_tag = col.find("figure").find("a", href=True) if col.find("figure") else None
            if a_tag:
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
        """
        Combine the 'Summary' and 'Full Details' sections into the article text.
        """
        text_parts = []

        # Find the summary heading
        summary_heading = self.soup.find("h2", string=lambda s: "Summary" in s if s else False)
        if summary_heading:
            # Next siblings until the next major section
            for tag in summary_heading.find_next_siblings():
                # Stop collecting if we hit the next section heading
                if tag.name == "h2":
                    break
                if tag.name == "p":
                    text_parts.append(tag.get_text(strip=True))

        # Full details block — sometimes paragraphs
        details_heading = self.soup.find("h2", string=lambda s: "Full Details" in s if s else False)
        if details_heading:
            for tag in details_heading.find_next_siblings():
                if tag.name == "h2":
                    break
                if tag.name == "p":
                    text_parts.append(tag.get_text(strip=True))

        return "\n\n".join(text_parts)

    def extract_id(self) -> str | None:
        """
        Extract ID from:
        <meta name="description" content="The UK's Most Wanted people | 57624" />
        """
        meta = self.soup.find("meta", attrs={"name": "description"})
        if not meta:
            return None

        content = meta.get("content", "")
        if "|" not in content:
            return None

        # ID is after the pipe
        ident =  content.split("|")[-1].strip()
        return ident

    def extract_name(self) -> str:
        # Look for <li><strong>Suspect name:</strong> Name</li>
        name_li = self.soup.find("li", string=lambda s: "Suspect name:" in s if s else False)
        if name_li:
            # Get text after the strong tag
            strong = name_li.find("strong")
            if strong and strong.next_sibling:
                return strong.next_sibling.strip()
        # Fallback to title
        return self.extract_title()

    def extract_title(self) -> str:
        h1 = self.soup.find("h1")
        return h1.get_text(strip=True) if h1 else ""

    def extract_date(self) -> str:
        """
        Crimestoppers Most Wanted appeal pages do not include a published date.
        Return empty string.
        """
        return ""


    def get_file_urls(self) -> list[str]:
        urls = []
        # Images in figure tags
        for img in self.soup.select("figure img[src]"):
            src = img.get("src", "").strip()
            if src:
                urls.append(urljoin(self.root, src))
        return list(dict.fromkeys(urls))

    def get_href_files(self) -> FileDirectory:
        return FileDirectory()

    def get_zip_files(self) -> FileDirectory:
        return FileDirectory()

    def get_embedded_files(self) -> FileDirectory:
        return FileDirectory()

    def get_video_files(self) -> FileDirectory:
        return FileDirectory()
