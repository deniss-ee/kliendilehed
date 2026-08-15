import asyncio
from typing import Optional, AsyncGenerator, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright
from app.scrapers.middleware import get_random_user_agent
from app.config import settings

class BrowserEngine:
    """Headless browser automation engine for SPAs and infinite scroll pages."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def start(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                ],
            )

    async def get_page(self) -> Page:
        if self._browser is None:
            await self.start()

        context = await self._browser.new_context(
            user_agent=get_random_user_agent(),
            viewport={"width": 1920, "height": 1080},
            locale="et-EE",
            timezone_id="Europe/Tallinn",
        )
        page = await context.new_page()
        return page

    async def scroll_infinite(
        self,
        page: Page,
        item_selector: str,
        max_items: int = 500,
        scroll_pause_ms: int = 800,
    ) -> int:
        """Scrolls down an infinite feed until max_items are rendered or bottom is reached."""
        last_count = 0
        stagnant_cycles = 0

        while True:
            items = await page.query_selector_all(item_selector)
            current_count = len(items)

            if current_count >= max_items:
                break

            if current_count == last_count:
                stagnant_cycles += 1
                if stagnant_cycles >= 3:
                    # Reached end of page
                    break
            else:
                stagnant_cycles = 0

            last_count = current_count
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(scroll_pause_ms / 1000.0)

        return last_count

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
