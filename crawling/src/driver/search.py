import asyncio
from datetime import datetime

from bs4 import BeautifulSoup
from crawling.src.utils.parsing_util import url_addition
from crawling.src.utils.acquisition import AsyncRequestHTML
from crawling.src.core.types import UrlDictCollect


class DeepAsyncWebCrawler:
    """BFS"""

    def __init__(self, start_url: str, max_pages: int, max_depth: int) -> None:
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls = set()
        self.url_queue = asyncio.Queue()
        self.url_queue.put_nowait((start_url, 0))  # Put start URL with depth 0
        self.results = {}

    # fmt: off
    def parse_links(self, content: str, base_url: str) -> tuple[set, UrlDictCollect]:
        soup = BeautifulSoup(content, "lxml")
        links = set()
        data_list: UrlDictCollect = []

        for a_tag in soup.find_all("a", href=True):
            link: str = a_tag["href"]
            # 자바스크립트 링크 제외
            if link.startswith(("javascript:", "#", "-", "i")) or "index.html" in link:
                continue

            if link.startswith("/"):
                link: str = url_addition(base_url, link)
            if link.startswith("http"):
                links.add(link)

            # 링크 정보를 데이터 포맷에 추가
            data_format = {
                "title": a_tag.text,
                "link": link,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            data_list.append(data_format)
        return links, data_list

    async def crawl(self) -> None:
        while not self.url_queue.empty() and len(self.visited_urls) < self.max_pages:
            current_url, depth = await self.url_queue.get()

            if current_url in self.visited_urls or depth > self.max_depth:
                continue

            self.visited_urls.add(current_url)
            content = await AsyncRequestHTML(current_url).async_fetch_html(current_url)

            if content:
                if depth < self.max_depth:
                    new_links, url_format = self.parse_links(content, current_url)
                    self.results[current_url] = url_format
                    for link in new_links:
                        if link not in self.visited_urls:
                            await self.url_queue.put((link, depth + 1))

    async def run(self, num_tasks: int = 4) -> dict[str, set[str]]:
        tasks = [asyncio.create_task(self.crawl()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        return self.results
