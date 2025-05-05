import asyncio
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from crawling.src.utils.parsing_util import url_addition
from crawling.src.utils.acquisition import AsyncRequestHTML
from crawling.src.core.types import UrlDictCollect


class DeepAsyncWebCrawler:
    """기본 비동기 웹 크롤러 - BFS 알고리즘 기반
    
    너비 우선 탐색(BFS) 알고리즘을 사용하여 웹 페이지를 크롤링하는 비동기 크롤러입니다.
    시작 URL에서부터 지정된 깊이까지 링크를 따라가며 데이터를 수집합니다.
    
    Attributes:
        start_url (str): 크롤링을 시작할 URL
        max_pages (int): 최대 크롤링할 페이지 수
        max_depth (int): 최대 탐색 깊이
        visited_urls (set): 이미 방문한 URL 집합
        url_queue (asyncio.Queue): 방문할 URL을 저장하는 비동기 큐
        results (dict): 결과를 저장할 딕셔너리
    """

    def __init__(self, start_url: str, max_pages: int, max_depth: int) -> None:
        """DeepAsyncWebCrawler 초기화
        
        Args:
            start_url: 크롤링을 시작할 URL
            max_pages: 최대 크롤링할 페이지 수
            max_depth: 최대 탐색 깊이
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls: set[str] = set()
        self.url_queue: asyncio.Queue = asyncio.Queue()
        self.url_queue.put_nowait((start_url, 0))  # 시작 URL을 깊이 0으로 큐에 추가
        self.results: dict[str, UrlDictCollect] = {}

    def parse_links(self, content: str, base_url: str) -> tuple[set[str], UrlDictCollect]:
        """HTML 콘텐츠에서 링크를 추출하고 정보를 구성
        
        Args:
            content: HTML 콘텐츠
            base_url: 기본 URL (상대 경로를 절대 경로로 변환하는 데 사용)
            
        Returns:
            links: 추출된 링크 집합
            data_list: 링크 정보가 담긴 리스트 (제목, URL, 날짜)
        """
        soup = BeautifulSoup(content, "lxml")
        links: set[str] = set()
        data_list: UrlDictCollect = []

        for a_tag in soup.find_all("a", href=True):
            link: str = a_tag["href"]
            # 자바스크립트 링크 제외
            if link.startswith(("javascript:", "#", "-", "i")) or "index.html" in link:
                continue

            if link.startswith("/"):
                link = url_addition(base_url, link)
            if link.startswith("http"):
                links.add(link)

            # 링크 정보를 데이터 포맷에 추가
            data_format = {
                "title": a_tag.text.strip(),
                "link": link,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            data_list.append(data_format)
        return links, data_list

    async def crawl(self) -> None:
        """BFS 알고리즘으로 웹 페이지 크롤링
        
        URL 큐에서 URL을 꺼내 방문하고, 페이지의 링크를 추출하여 다시 큐에 추가합니다.
        최대 페이지 수 또는 최대 깊이에 도달하면 크롤링을 중단합니다.
        """
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

    async def run(self, num_tasks: int = 4) -> dict[str, UrlDictCollect]:
        """여러 개의 크롤링 태스크를 동시에 실행
        
        Args:
            num_tasks: 동시에 실행할 크롤링 태스크 수 (기본값: 4)
            
        Returns:
            results: 크롤링 결과 딕셔너리
        """
        tasks = [asyncio.create_task(self.crawl()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        return self.results
