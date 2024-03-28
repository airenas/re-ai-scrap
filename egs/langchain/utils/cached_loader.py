import asyncio
import hashlib
import json
import os
import time
from typing import Iterator, List

from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document

from utils.logger import logger


class CachedLoader(BaseLoader):
    def __init__(
            self,
            urls,
            dir,
    ):
        self.urls = urls
        self.dir = dir
        os.makedirs(dir, exist_ok=True)

    def lazy_load(self) -> Iterator[Document]:
        for url in self.urls:
            valid_filename = hashlib.md5(url.encode()).hexdigest()
            filepath = os.path.join(self.dir, valid_filename + ".json")
            if os.path.exists(filepath):
                logger.info(f"returning cached: {url}")
                with open(filepath, 'r') as f:
                    loaded = json.load(f)
                    docs = Document(page_content=loaded["page_content"], metadata=loaded["metadata"])
            else:
                loader = AsyncChromiumLoader([url])
                docs = loader.load()[0]
                logger.info(f"caching: {url}")
                with open(filepath, 'w') as f:
                    json.dump({"metadata": docs.metadata, "page_content": docs.page_content}, fp=f)
                filepath = os.path.join(self.dir, valid_filename + ".html")
                with open(filepath, 'w') as f:
                    f.write(docs.page_content)
            yield docs


class AsyncChromiumLoader(BaseLoader):
    """Scrape HTML pages from URLs using a
    headless instance of the Chromium."""

    def __init__(
            self,
            urls: List[str],
    ):
        """
        Initialize the loader with a list of URL paths.

        Args:
            urls (List[str]): A list of URLs to scrape content from.

        Raises:
            ImportError: If the required 'playwright' package is not installed.
        """
        self.urls = urls

        try:
            import playwright  # noqa: F401
        except ImportError:
            raise ImportError(
                "playwright is required for AsyncChromiumLoader. "
                "Please install it with `pip install playwright`."
            )

    async def ascrape_playwright(self, url: str) -> str:
        """
        Asynchronously scrape the content of a given URL using Playwright's async API.

        Args:
            url (str): The URL to scrape.

        Returns:
            str: The scraped HTML content or an error message if an exception occurs.

        """
        from playwright.async_api import async_playwright

        logger.info("Starting scraping...")
        results = ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            try:
                page = await browser.new_page()
                await page.goto(url)
                results = await page.content()  # Simply get the HTML content
                time.sleep(1)
                logger.info("Content scraped")
            except Exception as e:
                results = f"Error: {e}"
            await browser.close()
        return results

    def lazy_load(self) -> Iterator[Document]:
        """
        Lazily load text content from the provided URLs.

        This method yields Documents one at a time as they're scraped,
        instead of waiting to scrape all URLs before returning.

        Yields:
            Document: The scraped content encapsulated within a Document object.

        """
        for url in self.urls:
            html_content = asyncio.run(self.ascrape_playwright(url))
            metadata = {"source": url}
            yield Document(page_content=html_content, metadata=metadata)
