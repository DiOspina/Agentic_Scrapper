"""
Web Scraper Agent for extracting structured and unstructured data from websites.
"""
import asyncio
import hashlib
import json
import re
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from pydantic import HttpUrl

from app.agents.base import BaseAgent, AgentContext, AgentResult, AgentState
from app.models.agent_log import AgentType, LogLevel
from app.core.config import settings


@dataclass
class ScrapedPage:
    url: str
    title: Optional[str]
    content: str
    html: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    structured_data: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ScrapingConfig:
    max_pages: int = 10
    max_depth: int = 2
    follow_links: bool = True
    same_domain_only: bool = True
    wait_for_selector: Optional[str] = None
    wait_timeout: int = 10000
    extract_tables: bool = True
    extract_images: bool = True
    extract_structured_data: bool = True
    user_agent: str = settings.SCRAPER_USER_AGENT
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None
    retry_count: int = settings.SCRAPER_MAX_RETRIES
    retry_delay: float = settings.SCRAPER_RETRY_DELAY
    timeout: int = settings.SCRAPER_TIMEOUT


class ScraperAgent(BaseAgent):
    """Agent for web scraping with dynamic content support."""

    def __init__(
        self,
        llm=None,
        config: Optional[Dict[str, Any]] = None,
        scraping_config: Optional[ScrapingConfig] = None,
    ):
        super().__init__(
            agent_type=AgentType.SCRAPER,
            name="scraper",
            llm=llm,
            config=config,
        )
        self.scraping_config = scraping_config or ScrapingConfig()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._visited_urls: Set[str] = set()
        self._session: Optional[httpx.AsyncClient] = None

    async def _on_initialize(self) -> None:
        """Initialize browser and HTTP session."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=self.scraping_config.user_agent,
            viewport={"width": 1920, "height": 1080},
        )

        self._session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.scraping_config.timeout),
            follow_redirects=True,
            headers={**self.scraping_config.headers, "User-Agent": self.scraping_config.user_agent},
            cookies=self.scraping_config.cookies,
        )

        self.logger.info("Scraper agent initialized with Playwright")

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute scraping based on input configuration."""
        urls = context.input_data.get("urls", [])
        config_overrides = context.input_data.get("config", {})

        if isinstance(urls, str):
            urls = [urls]

        if not urls:
            return AgentResult(
                success=False,
                error="No URLs provided for scraping",
            )

        # Apply config overrides
        scraping_config = ScrapingConfig(**{**self.scraping_config.__dict__, **config_overrides})

        all_pages: List[ScrapedPage] = []
        total_tokens = 0

        for url in urls:
            try:
                pages = await self._scrape_url(url, scraping_config)
                all_pages.extend(pages)

                # Log metrics
                self.log(
                    LogLevel.INFO,
                    f"Scraped {len(pages)} pages from {url}",
                    step_name="scrape_complete",
                    details={"url": url, "pages_count": len(pages)},
                )
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}", error=str(e))
                self.log(
                    LogLevel.ERROR,
                    f"Failed to scrape URL: {str(e)}",
                    step_name="scrape_error",
                    details={"url": url, "error": str(e)},
                )
                context.errors.append(f"Scraping {url}: {str(e)}")

        # Prepare output
        output_data = {
            "pages": [self._page_to_dict(p) for p in all_pages],
            "total_pages": len(all_pages),
            "urls_processed": urls,
            "errors": context.errors,
        }

        return AgentResult(
            success=len(all_pages) > 0,
            output_data=output_data,
            error="; ".join(context.errors) if context.errors else None,
            tokens_used=total_tokens,
        )

    async def _scrape_url(self, url: str, config: ScrapingConfig) -> List[ScrapedPage]:
        """Scrape a URL and optionally follow links."""
        pages = []
        queue = [(url, 0)]  # (url, depth)
        base_domain = urlparse(url).netloc

        while queue and len(pages) < config.max_pages:
            current_url, depth = queue.pop(0)

            if current_url in self._visited_urls:
                continue

            if depth > config.max_depth:
                continue

            if config.same_domain_only and urlparse(current_url).netloc != base_domain:
                continue

            self._visited_urls.add(current_url)

            try:
                page = await self._scrape_single_page(current_url, config)
                pages.append(page)

                # Extract links for crawling
                if config.follow_links and depth < config.max_depth:
                    for link in page.links:
                        if link not in self._visited_urls:
                            queue.append((link, depth + 1))

            except Exception as e:
                self.logger.warning(f"Failed to scrape {current_url}", error=str(e))
                continue

        return pages

    async def _scrape_single_page(self, url: str, config: ScrapingConfig) -> ScrapedPage:
        """Scrape a single page using Playwright for dynamic content."""
        page = await self._context.new_page()

        try:
            # Set extra headers
            await page.set_extra_http_headers(config.headers)

            # Navigate with retry
            for attempt in range(config.retry_count):
                try:
                    response = await page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=config.wait_timeout,
                    )
                    if response and response.status < 400:
                        break
                except Exception as e:
                    if attempt == config.retry_count - 1:
                        raise
                    await asyncio.sleep(config.retry_delay * (attempt + 1))

            # Wait for specific selector if configured
            if config.wait_for_selector:
                await page.wait_for_selector(config.wait_for_selector, timeout=config.wait_timeout)

            # Get page content
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            # Extract data
            title = soup.title.string if soup.title else None
            content = self._extract_text_content(soup)

            # Extract links
            links = self._extract_links(soup, url)

            # Extract images
            images = self._extract_images(soup, url) if config.extract_images else []

            # Extract tables
            tables = self._extract_tables(soup) if config.extract_tables else []

            # Extract structured data (JSON-LD, microdata, etc.)
            structured_data = self._extract_structured_data(soup) if config.extract_structured_data else []

            # Metadata
            metadata = {
                "url": url,
                "status_code": response.status if response else None,
                "content_length": len(html),
                "word_count": len(content.split()),
                "link_count": len(links),
                "image_count": len(images),
                "table_count": len(tables),
            }

            return ScrapedPage(
                url=url,
                title=title,
                content=content,
                html=html,
                metadata=metadata,
                links=links,
                images=images,
                tables=tables,
                structured_data=structured_data,
            )

        finally:
            await page.close()

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute_url = urljoin(base_url, href)
            # Filter out non-http links
            if absolute_url.startswith(("http://", "https://")):
                links.append(absolute_url)
        return list(set(links))

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all images from the page."""
        images = []
        for img in soup.find_all("img", src=True):
            src = img["src"]
            absolute_url = urljoin(base_url, src)
            if absolute_url.startswith(("http://", "https://")):
                images.append(absolute_url)
        return list(set(images))

    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract tables from the page."""
        tables = []
        for table in soup.find_all("table"):
            rows = []
            headers = []

            # Get headers
            thead = table.find("thead")
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all(["th", "td"])]

            # Get rows
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)

            if headers or rows:
                tables.append({
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows),
                    "col_count": len(headers) if headers else (len(rows[0]) if rows else 0),
                })

        return tables

    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract structured data (JSON-LD, microdata, RDFa)."""
        structured = []

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    structured.extend(data)
                else:
                    structured.append(data)
            except json.JSONDecodeError:
                pass

        # Microdata
        for item in soup.find_all(itemscope=True):
            item_data = {"type": item.get("itemtype", ""), "properties": {}}
            for prop in item.find_all(itemprop=True):
                name = prop.get("itemprop")
                value = prop.get("content") or prop.get("datetime") or prop.get_text(strip=True)
                if name:
                    item_data["properties"][name] = value
            if item_data["properties"]:
                structured.append(item_data)

        return structured

    def _page_to_dict(self, page: ScrapedPage) -> Dict[str, Any]:
        """Convert ScrapedPage to dictionary."""
        return {
            "url": page.url,
            "title": page.title,
            "content": page.content,
            "metadata": page.metadata,
            "links": page.links,
            "images": page.images,
            "tables": page.tables,
            "structured_data": page.structured_data,
            "timestamp": page.timestamp,
        }

    async def scrape_with_selectors(
        self,
        url: str,
        selectors: Dict[str, str],
        config: Optional[ScrapingConfig] = None,
    ) -> Dict[str, Any]:
        """Scrape specific elements using CSS selectors."""
        config = config or self.scraping_config
        page = await self._context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=config.wait_timeout)

            result = {}
            for name, selector in selectors.items():
                elements = await page.query_selector_all(selector)
                values = []
                for el in elements:
                    text = await el.inner_text()
                    values.append(text.strip())
                result[name] = values if len(values) > 1 else (values[0] if values else None)

            return result

        finally:
            await page.close()

    async def take_screenshot(self, url: str, full_page: bool = True) -> bytes:
        """Take a screenshot of a page."""
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            return await page.screenshot(full_page=full_page)
        finally:
            await page.close()

    async def close(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.aclose()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, "_playwright"):
            await self._playwright.stop()
        self.logger.info("Scraper agent closed")


class AsyncScraperAgent(ScraperAgent):
    """Async version of ScraperAgent with connection pooling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

    async def _scrape_url(self, url: str, config: ScrapingConfig) -> List[ScrapedPage]:
        """Scrape with semaphore for concurrency control."""
        async with self._semaphore:
            return await super()._scrape_url(url, config)