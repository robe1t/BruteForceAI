# -*- coding: utf-8 -*-
"""
Browser pool for managing Playwright browser instances
Singleton pattern - single browser instance with multiple contexts
"""
import asyncio
import threading
from typing import Dict, Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserPool:
    """
    浏览器复用池 - 单例模式

    Manages a single browser instance with multiple isolated contexts per domain.
    This ensures efficient resource usage while maintaining session isolation.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_browsers: int = 1, headless: bool = True):
        """
        Initialize browser pool

        Args:
            max_browsers: Maximum browser instances (limited to 1 for Playwright)
            headless: Whether to run in headless mode
        """
        # Prevent re-initialization
        if BrowserPool._initialized:
            return

        self.max_browsers = max_browsers
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.playwright = None
        self._lock = None  # Will be created lazily in the correct event loop
        self._event_loop_id = None  # Track which event loop we're bound to

        BrowserPool._initialized = True

    async def _get_lock(self):
        """Get or create lock for current event loop"""
        current_loop = id(asyncio.get_running_loop())
        if self._lock is None or self._event_loop_id != current_loop:
            self._lock = asyncio.Lock()
            self._event_loop_id = current_loop
        return self._lock

    async def _ensure_browser(self) -> Browser:
        """Ensure browser instance exists"""
        current_loop = id(asyncio.get_running_loop())

        # If we're in a different event loop, reset everything
        if self._event_loop_id is not None and self._event_loop_id != current_loop:
            print(f"[BrowserPool] Detected new event loop (was {self._event_loop_id}, now {current_loop}), resetting browser state...")
            self.browser = None
            self.contexts = {}
            self.playwright = None
            self._lock = None

        if self.browser is None or not self.browser.is_connected():
            if self.playwright is None:
                print("[BrowserPool] Starting Playwright...")
                self.playwright = await async_playwright().start()

            print("[BrowserPool] Launching Chromium browser...")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            self._event_loop_id = current_loop
            print(f"[BrowserPool] Browser launched, event_loop_id: {self._event_loop_id}")

        return self.browser

    async def get_browser(self) -> Browser:
        """
        Get browser instance

        Returns:
            Browser instance
        """
        async with await self._get_lock():
            return await self._ensure_browser()

    async def get_context(self, domain: str) -> BrowserContext:
        """
        Get or create browser context for a domain

        Args:
            domain: Domain name for context isolation

        Returns:
            BrowserContext instance
        """
        async with await self._get_lock():
            # Ensure browser exists
            await self._ensure_browser()

            # Normalize domain
            domain = self._normalize_domain(domain)

            # Return existing context or create new one
            if domain not in self.contexts:
                self.contexts[domain] = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

            return self.contexts[domain]

    async def create_page(self, domain: str) -> Page:
        """
        Create a new page for a domain

        Args:
            domain: Domain name

        Returns:
            Page instance
        """
        print(f"[BrowserPool] create_page called for domain: {domain}")
        print(f"[BrowserPool] Current browser state: browser={self.browser is not None}, is_connected={self.browser.is_connected() if self.browser else 'N/A'}")
        context = await self.get_context(domain)
        print(f"[BrowserPool] Context obtained, creating new page...")
        page = await context.new_page()
        print(f"[BrowserPool] Page created successfully")

        # Set default timeout
        page.set_default_timeout(30000)

        return page

    async def release_page(self, page: Page):
        """
        Release a page (close it)

        Args:
            page: Page to release
        """
        try:
            await page.close()
        except Exception:
            pass

    async def close_context(self, domain: str):
        """
        Close a specific domain context

        Args:
            domain: Domain name
        """
        async with await self._get_lock():
            domain = self._normalize_domain(domain)
            if domain in self.contexts:
                try:
                    await self.contexts[domain].close()
                except Exception:
                    pass
                del self.contexts[domain]

    async def cleanup(self):
        """Clean up all resources"""
        async with await self._get_lock():
            # Close all contexts
            for domain, context in list(self.contexts.items()):
                try:
                    await context.close()
                except Exception:
                    pass
            self.contexts.clear()

            # Close browser
            if self.browser:
                try:
                    await self.browser.close()
                except Exception:
                    pass
                self.browser = None

            # Stop playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception:
                    pass
                self.playwright = None

            # Reset lock for next use
            self._lock = None

    def _normalize_domain(self, domain: str) -> str:
        """
        Normalize domain name from URL or domain string

        Args:
            domain: URL or domain string

        Returns:
            Normalized domain name
        """
        if domain.startswith('http://') or domain.startswith('https://'):
            parsed = urlparse(domain)
            return parsed.netloc
        return domain

    def set_headless(self, headless: bool):
        """
        Set headless mode

        Args:
            headless: Whether to run in headless mode
        """
        self.headless = headless
        # Reset browser so new mode takes effect on next page creation
        self.browser = None

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)"""
        if cls._instance:
            asyncio.create_task(cls._instance.cleanup())
        cls._instance = None
        cls._initialized = False