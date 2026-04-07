import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from curl_cffi.requests import AsyncSession
from loguru import logger


class BrowserClient:
    def __init__(self):
        self.session = AsyncSession()
        self.count = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=False,
    )
    async def request(self, url: str):
        target_browsers = ["chrome110", "chrome120", "edge101", "chrome116"]
        chosen_browser = random.choice(target_browsers)

        response = await self.session.get(
            url, impersonate=chosen_browser, timeout=30, allow_redirects=True
        )
        response.raise_for_status()
        return response

    async def fetch(self, url: str) -> str:
        """Fetch URL and return clean HTML. Returns empty string on failure."""
        task_log = logger.bind(context="browser_client", url=url)
        try:
            response = await self.request(url)
            if not response:
                return ""

            html = response.text
            self.count += 1

            # Basic Bot Detection Check
            if any(
                term in html.lower() for term in ["cloudflare", "datadome", "captcha"]
            ):
                task_log.warning(f"No {self.count} Bot detection triggered for {url}")
                return ""
            return html

        except Exception:
            task_log.exception(f"No {self.count} Failed after all retries for {url}")
            return ""

    async def close(self):
        await self.session.close()
