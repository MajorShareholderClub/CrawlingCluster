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

import logging
import datetime
from config.properties import naver_id, naver_secret, naver_url

from collections import deque
from src.core.types import SelectHtmlOrJson, UrlDictCollect
from src.utils.acquisition import AsyncRequestJSON
from src.utils.logger import AsyncLogger
from src.utils.parsing_util import time_extract


class AsyncNaverNewsParsingDriver:
    """네이버 NewsAPI 비동기 호출"""

    def __init__(self, target: str, count: int) -> None:
        """
        Args:
            target (str): 긁어올 타겟
            count (int): 횟수
        """

        self.target = target
        self.count = count
        self.header = {
            "X-Naver-Client-Id": naver_id,
            "X-Naver-Client-Secret": naver_secret,
        }
        self.url = (
            f"{naver_url}/news.json?query={self.target}&start={self.count}&display=100"
        )
        self._logging = AsyncLogger(
            target="naver", log_file="naver_crawling.log"
        ).log_message_sync

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
            urls = await load_f.async_fetch_json(target="Naver")
            return urls
        except ConnectionError as error:
            self._logging(
                logging.ERROR, f"Naver 기사를 가져오지 못햇습니다 --> {error}"
            )
            return False

    async def extract_news_urls(self) -> UrlDictCollect:
        """new parsing
        Args:
            items (str): 첫번째 접근
            link (str): url
        Returns:
            UrlCollect: [URL, ~]
        """

        def data_format(item: dict[str, str]) -> dict[str, str]:
            return {
                "title": item["title"],
                "article_time": time_extract(item["pubDate"]),
                "url": item["originallink"],
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d: %H:%M:%S"),
            }

        self._logging(logging.INFO, "네이버 시작합니다")
        res_data = await self.fetch_page_urls()

        # fmt: off
        data: list[dict[str, str]] = list(map(lambda item: data_format(item), res_data["items"]))
        urls = deque(data)
        self._logging(logging.INFO, f"네이버에서 --> {len(urls)}개 의 뉴스를 가지고 왔습니다")

        return urls
