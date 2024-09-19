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
from src.utils.acquisition import AsyncRequestHTML, AsyncRequestJSON
from src.utils.logger import AsyncLogger
from src.utils.parsing_util import time_extract, NewsDataFormat
import requests
from bs4 import BeautifulSoup


def extract_text_from_url(url: str) -> str:
    """
    Args:
        url (str): 뉴스 기사 URL

    Returns:
        str: 추출된 기사 본문 텍스트
    """
    try:
        soup = BeautifulSoup(url, "lxml")

        # 일반적인 뉴스 본문 구조 (예시: article 태그, div 태그, p 태그)
        article = soup.find("article")
        if article:
            paragraphs = article.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        # 텍스트를 모두 연결하여 반환
        return "\n".join([p.get_text() for p in paragraphs])
    except Exception:
        pass


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

        # NewsDataFormat.create(
        #     url=item["originallink"],
        #     title=item["title"],
        #     article_time=time_extract(item["pubDate"]),
        #     content=
        # )
        self._logging(logging.INFO, "네이버 시작합니다")
        res_data = await self.fetch_page_urls()

        for i in res_data["items"]:
            print(i)
            # a = await AsyncRequestHTML(i["originallink"]).async_fetch_html("naver")
            # print(extract_text_from_url(a))

        # fmt: off
        data: list[dict[str, str]] = list(map(lambda item: data_format(item), res_data["items"]))
        urls = deque(data)
        self._logging(logging.INFO, f"네이버에서 --> {len(urls)}개 의 뉴스를 가지고 왔습니다")

        return urls
