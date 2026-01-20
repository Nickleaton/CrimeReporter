import atexit
import logging
import mimetypes
import time
from pathlib import Path
from urllib.parse import urlparse

from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)
config = Config()


class Fetcher:
    _instance: "Fetcher | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, headless: bool = True) -> None:
        if getattr(self, "_initialized", False):
            return
        logger.debug("Initialize Fetcher")
        self._playwright = None
        self._browser = None
        self._headless = headless  # default headless
        self._initialized = True
        atexit.register(self.stop)

    @staticmethod
    def storage_file_for_url(url: str) -> Path:
        hostname = urlparse(url).hostname
        return Path(config.root) / f"local_storage/{hostname}.json"

    @staticmethod
    def user_agent():
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )

    def start(self) -> None:
        if not self._playwright:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            # Launch browser with default headless mode
            self._browser = self._playwright.chromium.launch(headless=self._headless)

    def fetch(self, url: str) -> str:
        logger.info(f"Fetching       {url}")
        self.start()

        storage_file = self.storage_file_for_url(url)
        manual_interaction = not storage_file.exists()

        # If manual interaction is required, use headful browser
        if manual_interaction and self._headless:
            logger.info("Switching to headful browser for manual interaction")
            self.stop()  # stop current headless browser
            self._headless = False
            self.start()  # restart browser headful

        # Create fresh context per site
        context = self._browser.new_context(
            user_agent=self.user_agent(),
            java_script_enabled=True,
            storage_state=str(storage_file) if storage_file.exists() else None,
        )

        page = context.new_page()

        try:
            response = page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # --- Handle HTTP status codes ---
            if response is None:
                raise RuntimeError(f"No response received for {url}")

            status = response.status
            if status == 403:
                logger.error(f"(403)          {url}")
                raise PermissionError(f"403 Forbidden: {url}")
            elif status == 404:
                logger.error(f"(404)          {url}")
                raise FileNotFoundError(f"404 Not Found: {url}")
            elif status == 500:
                logger.warning(f"Server {status}     {url}")
            elif status >= 400:
                logger.warning(f"HTTP error {status} {url}")

            # ------------------------------------------------------------------
            # SAFE retrieval of content inline without helper function
            # ------------------------------------------------------------------
            import time

            retries = 5
            delay = 0.4

            # Read URL first (never crashes)
            current_url = page.url

            # Try reading content without crashing during navigation
            content_now = ""
            for _ in range(retries):
                try:
                    content_now = page.content()
                    break
                except Exception:
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=2000)
                    except Exception:
                        pass
                    time.sleep(delay)
            # ------------------------------------------------------------------

            # --- Handle Cloudflare / cookies ---
            if "challenge-platform" in current_url or "challenge-platform" in content_now or manual_interaction:
                self.handle_challenge(page, url, manual=manual_interaction)

            elif manual_interaction:
                logger.info("Manual interaction: accept cookies if required.")
                page.pause()

            # ------------------------------------------------------------------
            # SAFE final content retrieval (again, inline)
            # ------------------------------------------------------------------
            content = ""
            for _ in range(retries):
                try:
                    content = page.content()
                    break
                except Exception:
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=2000)
                    except Exception:
                        pass
                    time.sleep(delay)
            # ------------------------------------------------------------------

            # Save storage state only if it’s a new site or manual interaction
            if manual_interaction:
                context.storage_state(path=str(storage_file))
                logger.info(f"Storage state saved to {storage_file}")

            # Close page/context if not manual interaction
            if not manual_interaction:
                page.close()
                context.close()
            else:
                logger.info("Browser left open for manual interaction. Close the page manually to continue.")

            return content

        except (PermissionError, FileNotFoundError):
            raise

        except Exception as e:
            logger.exception(f"Unexpected error while fetching {url}: {e}")
            raise

        finally:
            if not manual_interaction:
                try:
                    if page and not page.is_closed():
                        page.close()
                except Exception:
                    pass
                try:
                    context.close()
                except Exception:
                    pass

    @staticmethod
    def handle_challenge(page, url: str, manual: bool = True):
        """Handle Cloudflare challenge and optionally allow manual interaction for cookies."""
        hostname = urlparse(url).hostname
        home_url = f"https://{hostname}/"
        logger.warning(f"Cloudflare challenge detected — opening home page {home_url}")
        page.goto(home_url, wait_until="domcontentloaded")

        if manual:
            logger.info("Manual interaction required — accept cookies / solve Cloudflare now.")
            page.pause()  # let user interact manually
        else:
            Fetcher.accept_cookies(page)

    @staticmethod
    def accept_cookies(page):
        """Try to automatically click common cookie accept buttons."""
        try:
            selectors = [
                'button:has-text("Accept")',
                'button:has-text("Accept All")',
                'button:has-text("Agree")',
                'button[aria-label*="accept"]',
                'button[class*="cookie"]',
            ]
            for selector in selectors:
                if page.locator(selector).count() > 0:
                    logger.info(f"Clicking cookie button: {selector}")
                    page.locator(selector).first.click()
                    time.sleep(1)
                    break
        except Exception as e:
            logger.warning(f"Failed to auto-accept cookies: {e}")

    def download_file(self, page_url: str, file_url: str, save_path: Path):
        """Download a file using Playwright session (cookies preserved) with proper extension."""

        if save_path.exists():
            logger.info(f"File already exists, skipping download: {save_path}")
            return

        logger.info(f"Downloading File {file_url} to {save_path}")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.start()

        context = self._browser.new_context(
            user_agent=self.user_agent(),
            java_script_enabled=True,
        )

        try:
            # Visit page first to set cookies / Cloudflare clearance
            page = context.new_page()
            page.goto(page_url, wait_until="domcontentloaded", timeout=60000)

            # Fetch the file with browser session (cookies included)
            response = context.request.get(file_url, timeout=60000)
            if not response.ok:
                raise RuntimeError(f"HTTP {response.status} while downloading {file_url}")

            # Determine extension
            extension = ""
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
            if content_type.startswith("image/"):
                extension = mimetypes.guess_extension(content_type)
                if extension == ".jpe":  # normalize
                    extension = ".jpg"

            # Fallback: try to get extension from URL
            if not extension:
                path_ext = Path(urlparse(file_url).path).suffix
                if path_ext:
                    extension = path_ext
                else:
                    extension = ".jpg"

            # Add extension if missing
            if not save_path.suffix and extension:
                save_path = save_path.with_suffix(extension)

            save_path.write_bytes(response.body())
            logger.info(f"Saved FILE {save_path}")

        except Exception as e:
            logger.error(f"Failed to download file {file_url}: {e}")

        finally:
            try:
                context.close()
            except Exception:
                pass

    def stop(self) -> None:
        logger.debug("Stop Fetcher")
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
