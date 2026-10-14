"""
Browser manager using Playwright with anti-bot features
"""

import asyncio
import random
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright, Response
from fake_useragent import UserAgent
from loguru import logger

from .config import settings


class BrowserManager:
    """Manages browser instances with anti-bot features"""

    def __init__(
        self,
        headless: Optional[bool] = None,
        browser_type: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        self.headless = headless if headless is not None else settings.browser.headless
        self.browser_type = browser_type or settings.browser.browser_type
        self.proxy = proxy or self._pick_configured_proxy()

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.ua = UserAgent()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start the browser"""
        logger.info(f"Starting {self.browser_type} browser (headless={self.headless})")

        self.playwright = await async_playwright().start()

        # Get browser launcher
        if self.browser_type == "chromium":
            launcher = self.playwright.chromium
        elif self.browser_type == "firefox":
            launcher = self.playwright.firefox
        elif self.browser_type == "webkit":
            launcher = self.playwright.webkit
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")

        # Browser launch options
        launch_options: Dict[str, Any] = {"headless": self.headless}
        if self.browser_type == "chromium":
            # Chromium-only flags; Firefox and WebKit don't understand them
            launch_options["args"] = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]

        # Add proxy if configured
        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}

        self.browser = await launcher.launch(**launch_options)

        # Create context with anti-detection features
        context_options = {
            "viewport": {
                "width": settings.browser.viewport_width,
                "height": settings.browser.viewport_height,
            },
            "user_agent": self._get_random_user_agent() if settings.anti_bot.user_agent_rotation else None,
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        self.context = await self.browser.new_context(**context_options)

        # Add stealth scripts to avoid detection
        await self.context.add_init_script("""
            // Overwrite the `plugins` property to use a custom getter.
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Overwrite the `plugins` property to use a custom getter.
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Overwrite the `languages` property to use a custom getter.
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // Pass the Chrome Test.
            window.chrome = {
                runtime: {},
            };

            // Pass the Permissions Test.
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
            );
        """)

        # Create a new page
        self.page = await self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(settings.browser.timeout)

        logger.info("Browser started successfully")

    async def close(self):
        """Close the browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("Browser closed")

    async def navigate(self, url: str, wait_until: str = "networkidle") -> Optional[Response]:
        """
        Navigate to a URL with human-like behavior

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation succeeded (load, domcontentloaded, networkidle)

        Returns:
            The main resource response (use .status to check for HTTP errors),
            or None for navigations that don't produce one
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        # Random delay before navigation (simulate human behavior)
        await self._random_delay()

        logger.info(f"Navigating to {url}")
        response = await self.page.goto(url, wait_until=wait_until)

        # Random mouse movements to simulate human behavior
        await self._simulate_human_behavior()

        return response

    async def get_content(self) -> str:
        """Get page content"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        return await self.page.content()

    async def screenshot(self, path: str, full_page: bool = False):
        """Take a screenshot"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.screenshot(path=path, full_page=full_page)
        logger.info(f"Screenshot saved to {path}")

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        """Wait for a selector to appear"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.wait_for_selector(selector, timeout=timeout)

    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript on the page"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        return await self.page.evaluate(script)

    async def click(self, selector: str, delay: Optional[int] = None):
        """Click an element with optional delay"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        # Random delay before clicking
        await self._random_delay()

        await self.page.click(selector, delay=delay or random.randint(50, 150))

    async def type_text(self, selector: str, text: str):
        """Type text into an input field with human-like typing"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.type(selector, text, delay=random.randint(50, 150))

    async def scroll_page(self, distance: Optional[int] = None):
        """Scroll the page to simulate human browsing"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        if distance is None:
            distance = random.randint(300, 700)

        await self.page.evaluate(f"window.scrollBy(0, {distance})")
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _random_delay(self):
        """Add random delay between actions"""
        delay = random.uniform(settings.anti_bot.min_delay, settings.anti_bot.max_delay)
        logger.debug(f"Random delay: {delay:.2f}s")
        await asyncio.sleep(delay)

    async def _simulate_human_behavior(self):
        """Simulate random human-like mouse movements and scrolling"""
        try:
            # Random mouse movement
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            await self.page.mouse.move(x, y)

            # Random small scroll
            if random.random() > 0.5:
                await self.scroll_page(random.randint(100, 300))

        except Exception as e:
            logger.debug(f"Could not simulate human behavior: {e}")

    @staticmethod
    def _pick_configured_proxy() -> Optional[str]:
        """Pick a random proxy from PROXY_LIST when PROXY_ENABLED is set"""
        if not settings.anti_bot.proxy_enabled:
            return None
        proxies = settings.anti_bot.get_proxy_list()
        if not proxies:
            logger.warning("PROXY_ENABLED is true but PROXY_LIST is empty")
            return None
        return random.choice(proxies)

    def _get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return self.ua.random

    async def extract_links(self, selector: Optional[str] = "a") -> List[str]:
        """Extract all links from the page"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        # Pass the selector as data rather than formatting it into the script
        links = await self.page.eval_on_selector_all(
            selector or "a",
            "elements => elements.map(el => el.href).filter(href => href)",
        )

        return links

    async def extract_images(self) -> List[Dict[str, str]]:
        """Extract all images from the page"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        images = await self.page.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    width: img.width,
                    height: img.height
                }));
            }
        """)

        return images

    async def get_page_info(self) -> Dict[str, Any]:
        """Get basic page information"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "content": await self.page.content(),
        }
