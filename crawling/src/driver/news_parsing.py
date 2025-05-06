import asyncio
import logging
from itertools import chain
from typing import Generator

from bs4 import BeautifulSoup
from config.setting import BasicAsyncNewsDataCrawling
from crawling.src.core.types import SelectJson, SelectHtml, UrlDictCollect
from crawling.src.utils.acquisition import AsyncRequestJSON, AsyncRequestHTML
from crawling.src.utils.parsing_util import (
    href_from_text_preprocessing,
    href_from_a_tag,
    parse_time_ago,
    time_extract,
    NewsDataFormat,
)
from crawling.src.driver import (
    InvestingSeleniumNews,
    InvestingSeleniumTargetNews,
    GoogleReqestNews,
    GooglSeleniumeNews,
)


def data_format_create(title: str, article_time: str, url: str) -> NewsDataFormat:
    """데이터 포맷 함수"""
    return NewsDataFormat.create(
        url=url,
        title=href_from_text_preprocessing(title),
        article_time=parse_time_ago(article_time),
    ).model_dump()


# get selenium
class GoogleNewsDataSeleniumCrawling(GooglSeleniumeNews):
    def extract_format(self, tag: BeautifulSoup) -> NewsDataFormat:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            tag (BeautifulSoup): 뉴스 페이지의 HTML tag

        Yields:
            dict: 뉴스 제목, 기사 시간, URL 포함된 딕셔너리
        """
        return (
            data_format_create(
                url=href_from_a_tag(a_tag),
                title=a_tag.text[:20],
                article_time=self.news_create_time_from_div(a_tag),
            )
            for div_1 in self.extract_content_div(tag)
            for a_tag in self.extract_links_from_div(div_1)
        )

    def extract_news_urls(self, html: str) -> UrlDictCollect:
        """수집 시작점"""
        start = self.div_in_data_hveid(html=html)
        data = list(chain.from_iterable(self.extract_format(html) for html in start))
        return data


# get request
class GoogleAsyncDataReqestCrawling(BasicAsyncNewsDataCrawling):
    async def fetch_page_urls(self) -> SelectHtml:
        """JSON 비동기 호출
        Args:
            url (str): URL
            headers (dict[str, str]): 해더
        Returns:
            dict: JSON
        """
        try:
            load_f = AsyncRequestHTML(
                url=self.url, params=self.param, headers=self.header
            )
            urls = await load_f.async_fetch_html(target=self.home)
            return urls
        except ConnectionError as error:
            self.logger.error(f"{self.home} 기사를 가져오지 못햇습니다 --> {error}")
            return False

    # fmt: off
    def extract_format(self, driver: GoogleReqestNews, tag: BeautifulSoup) -> NewsDataFormat:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            driver (GoogleReqestNews): 파싱드라이버

        Yields:
            dict: 뉴스 제목, 기사 시간, URL, context가 포함된 딕셔너리
        """
        return data_format_create(
            url=driver.extract_content_url(tag),
            title=href_from_text_preprocessing(tag.get_text()),
            article_time=driver.news_create_time_from_div(tag),
        )

    async def extract_news_urls(self) -> UrlDictCollect:
        """수집 시작점"""
        self.logger.info(f"{self.home} 시작합니다")

        # parsing driver
        parsing = GoogleReqestNews()
        
        res_data = await self.fetch_page_urls()
        if res_data:
            start = parsing.div_start(html=res_data)

            data = [self.extract_format(parsing, i) for i in start]
            self.logger.info(f"{self.home}에서 --> {len(data)}개 의 뉴스 수집")

            return data


# Investing Selenium
class InvestingNewsDataSeleniumCrawling(InvestingSeleniumNews):
    def extract_format(self, tag: BeautifulSoup) -> NewsDataFormat:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            tag (BeautifulSoup): 뉴스 페이지의 HTML tag

        Yields:
            dict: 뉴스 제목, 기사 시간, URL 포함된 딕셔너리
        """
        return (
            data_format_create(
                url=url["href"],
                title=url.text,
                article_time=self.extract_timestamp(tag).text,
            )
            if (url := self.extract_content_url(tag))
            else None
        )

    def extract_news_urls(self, html: str) -> UrlDictCollect:
        """
        HTML에서 여러 개의 기사 정보를 추출 (URL 및 timestamp)
        """
        start = self.find_article_elements(html)
        data = [self.extract_format(html) for html in start]
        return data


# Investing Selenium
class InvestingNewsDataTargetSeleniumCrawling(InvestingSeleniumTargetNews):
    def extract_format(self, tag: BeautifulSoup) -> NewsDataFormat:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            tag (BeautifulSoup): 뉴스 페이지의 HTML tag

        Yields:
            dict: 뉴스 제목, 기사 시간, URL 포함된 딕셔너리
        """
        data: str = self.extract_news_textdiv(div_tag=tag)
        return data_format_create(
            url=f"https://kr.investing.com/{data.a["href"]}",
            title=data.a.text.replace("\n", "").replace(" ", ""),
            article_time=data.div.time.text,
        )

    def extract_news_urls(self, html: str) -> UrlDictCollect:
        """
        HTML에서 여러 개의 기사 정보를 추출 (URL 및 timestamp)
        """
        start = self.find_article_elements(html)
        data = [self.extract_format(html) for html in start]
        return data


# api request format json (Naver Daum)
class NaverDaumAsyncDataCrawling(BasicAsyncNewsDataCrawling):
    async def fetch_page_urls(self) -> SelectJson:
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
            self.logger.error(f"{self.home} 기사를 가져오지 못햇습니다 --> {error}")
            return False

    async def extract_format(self, item: dict[str, str], **kwargs) -> NewsDataFormat:
        """데이터 포맷을 생성하는 공통 메서드"""
        url_key = kwargs.get("url_key", "url")
        title_key = kwargs.get("title_key", "title")
        datetime_key = kwargs.get("datetime_key", "datetime")

        return data_format_create(
            url=item[url_key],
            title=item[title_key],
            article_time=time_extract(item[datetime_key]),
        )

    async def extract_news_urls(self, element: str, **kwargs) -> UrlDictCollect:
        """뉴스 URL을 추출합니다.
        Args:
            element (str): 첫 번째 접근

        Returns:
            UrlDictCollect: [URL, ~]
        """
        self.logger.info(f"{self.home} 시작합니다")
        res_data = await self.fetch_page_urls()

        data = [self.extract_format(item=item, **kwargs) for item in res_data[element]]
        s = await asyncio.gather(*data)
        self.logger.info(f"{self.home}에서 --> {len(s)}개 의 뉴스 수집")
        return s
