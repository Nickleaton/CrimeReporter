from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from crimereporter.utils.config import Config

config = Config()


class StorageSaver:
    """Handles saving Playwright storage state for a given site."""

    def __init__(self, site_url: str, storage_dir: str = "local_storage"):
        self.site_url = site_url
        self.domain = self.extract_domain(site_url)
        self.storage_dir = Path(storage_dir)
        self.storage_file = self.storage_dir / f"{self.domain}.json"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extracts the domain name from a full URL."""
        return urlparse(url).netloc

    def save(self) -> None:
        """Launches a browser, lets the user solve Cloudflare, and saves storage state."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print(f"\nNavigating to {self.site_url}...")
            page.goto(self.site_url)

            print("Solve the Cloudflare challenge manually in the browser.")
            input("Press Enter when done...")

            context.storage_state(path=str(self.storage_file))
            print(f"Storage state saved to {self.storage_file.resolve()}")

            browser.close()


def ensure_storage_states() -> None:
    roots = []
    for entry in config.sources:
        root = entry["source"]["root"]
        if not root:
            continue
        roots.append(root)
    roots.append("http://www.youtube.com/")

    for root in roots:
        saver = StorageSaver(root, r'D:/PycharmProjects/CrimeReportData/local_storage')
        if saver.storage_file.exists():
            print(f"✅ {saver.storage_file} already exists — skipping.")
        else:
            print(f"⚠️  {saver.storage_file} not found — creating...")
            saver.save()


if __name__ == "__main__":
    ensure_storage_states()
