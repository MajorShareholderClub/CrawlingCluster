"""
=========================================================================================================== test session starts ===========================================================================================================
테스트 성공 시간 --> 2024년 9월 15일 AM 01시 24분
platform darwin -- Python 3.12.3, pytest-8.3.3, pluggy-1.5.0
rootdir: /Users/imhaneul/Documents/project/JuJuClub/CrawlingCluster
configfile: pyproject.toml
plugins: asyncio-0.24.0, Faker-28.4.1
asyncio: mode=Mode.STRICT, default_loop_scope=function
collected 1 item                                                                                                                                                                                                                          

test_naver.py .  [100%]                                                                                                                                                                                                                   
============================================================================================================ 1 passed in 0.84s ============================================================================================================
"""

import asyncio
import logging
from config.properties import naver_id, naver_secret, naver_url, daum_auth, daum_url
from concurrent.futures import ThreadPoolExecutor

from collections import deque
from src.core.types import SelectHtmlOrJson, UrlDictCollect
from src.utils.acquisition import AsyncRequestJSON, AsyncRequestHTML
from src.utils.logger import AsyncLogger
from src.utils.parsing_util import time_extract, NewsDataFormat, url_news_text


class AsyncNewsParsingDriver:
    def __init__(
        self, target: str, count: int, url: str, home: str, header: dict[str, str]
    ) -> None:
        self.target = target
        self.count = count
        self.url = url
        self.home = home
        self.header = header
        self._logging = AsyncLogger(
            target=home, log_file=f"{home}_crawling.log"
        ).log_message_sync
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def fetch_page_urls(self) -> SelectHtmlOrJson:
        """JSON 비동기 호출
        Args:
            url (str): URL
            headers (dict[str, str]): 해더
        Returns:
            dict: JSON
        """
        try:
            load_f = AsyncRequestJSON(url=self.url, headers=self.header)
            urls = await load_f.async_fetch_json(target=self.home)
            return urls
        except ConnectionError as error:
            self._logging(
                logging.ERROR, f"Naver 기사를 가져오지 못햇습니다 --> {error}"
            )
            return False

    async def _fetch_url_news_text(self, url: str) -> str:
        """비동기 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, url_news_text, url)

    async def data_format(
        self,
        item: dict[str, str],
        url_key: str = "url",
        title_key: str = "title",
        datetime_key: str = "datetime",
    ) -> dict[str, str]:
        return NewsDataFormat.create(
            url=item[url_key],
            title=item[title_key],
            article_time=time_extract(item[datetime_key]),
            content=await self._fetch_url_news_text(item[url_key]),
        ).model_dump()

    async def extract_news_urls(
        self,
        element: str,
        url_key: str = "url",
        title_key: str = "title",
        datetime_key: str = "datetime",
    ) -> UrlDictCollect:
        """new parsing
        Args:
            items (str): 첫번째 접근
            link (str): url
        Returns:
            UrlCollect: [URL, ~]
        """

        self._logging(logging.INFO, f"{self.home} 시작합니다")
        res_data = await self.fetch_page_urls()

        data = list(
            map(
                lambda item: self.data_format(item, url_key, title_key, datetime_key),
                res_data[element],
            )
        )
        s = await asyncio.gather(*data)

        urls = deque(s)
        self._logging(logging.INFO, f"{self.home}에서 --> {len(urls)}개 의 뉴스 수집")
        return urls


class AsyncNaverNewsParsingDriver(AsyncNewsParsingDriver):
    """네이버 NewsAPI 비동기 호출"""

    def __init__(self, target: str, count: int) -> None:
        """생성자 초기화"""
        self.header = {
            "X-Naver-Client-Id": naver_id,
            "X-Naver-Client-Secret": naver_secret,
        }
        self.url = f"{naver_url}/news.json?query={target}&start={count}&display=100"
        super().__init__(
            target=target, count=count, url=self.url, home="naver", header=self.header
        )

    async def news_colletor(self) -> UrlDictCollect:
        return await self.extract_news_urls(
            element="items", url_key="originallink", datetime_key="pubDate"
        )


class AsyncDaumrNewsParsingDriver(AsyncNewsParsingDriver):
    """다음 크롤링"""

    def __init__(self, target: str, count: int) -> None:
        """생성자 초기화"""
        self.url = f"{daum_url}?query={target} /news&page=10&size={count}"
        self.auth = {"Authorization": f"KakaoAK {daum_auth}"}
        super().__init__(target, count, url=self.url, home="daum", header=self.auth)

    async def news_colletor(self) -> UrlDictCollect:
        return await self.extract_news_urls(element="documents")
