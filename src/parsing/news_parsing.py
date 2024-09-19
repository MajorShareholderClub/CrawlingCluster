from itertools import chain
from typing import Generator

from concurrent.futures import ThreadPoolExecutor
from src.core.types import UrlDictCollect
from src.parsing.bs_parsing import (
    GoogleNewsCrawlingParsingDrive as GoogleNews,
    BingNewsCrawlingParsingDrive as BingNews,
    DaumNewsCrawlingParsingDrive as DaumNews,
)
from src.utils.parsing_util import (
    href_from_text_preprocessing,
    href_from_a_tag,
    parse_time_ago,
    url_news_text,
    NewsDataFormat,
)


# 공통 로직을 함수로 추출하여 중복 제거
def create_news_data(title: str, article_time: str, url_type: tuple) -> dict:
    """공통 포맷으로 뉴스 데이터를 생성"""
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_href = pool.submit(href_from_a_tag, url_type)
        url = future_href.result()

        content = pool.submit(url_news_text, url)
        return NewsDataFormat.create(
            title=title,
            article_time=parse_time_ago(article_time),
            url=url,
            content=content.result(),
        ).model_dump()


class GoogleNewsDataCrawling(GoogleNews):
    def extract_format(self, tag: str) -> Generator:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            tag (str): 뉴스 페이지의 HTML tag

        Yields:
            dict: 뉴스 제목, 기사 시간, URL, context가 포함된 딕셔너리
        """
        return (
            create_news_data(
                title=href_from_text_preprocessing(a_tag.text[:20]),
                article_time=self.news_create_time_from_div(a_tag),
                url_type=(a_tag),
            )
            for div_1 in self.extract_content_div(tag)
            for a_tag in self.extract_links_from_div(div_1)
        )

    def news_info_collect(self, html: str) -> UrlDictCollect:
        """수집 시작점"""
        parsing_data = list(
            chain.from_iterable(
                self.extract_format(html) for html in self.div_in_data_hveid(html=html)
            )
        )
        return parsing_data


class BingNewsDataCrawling(BingNews):
    def extract_format(self, html: str, attr: str) -> Generator:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            html (str): 뉴스 페이지의 HTML 내용

        Yields:
            dict: 뉴스 제목, 기사 시간, URL, context가 포함된 딕셔너리
        """
        return (
            create_news_data(
                title=div_2.text[:20],
                article_time=i,
                url_type=(div_2, "url"),
            )
            for div_2 in self.div_in_class(html, attr)
            for i in self.news_create_time_from_div(div_2)
        )

    def news_info_collect(self, html: str) -> UrlDictCollect:
        """수집 시작점"""

        # 첫번쨰 요소 접근  -> <div class="algocore"> or nwscnt
        # 요소 필터링 하여 확인 되는 요소만 크롤링할 수 있게 행동 제약
        attr: tuple[str] = self.detection_element(
            html,
            "nwscnt",
            "newscard vr",
            "algocore",
            "news-card newsitem cardcommon",
        )
        # print(f"Bing 다음요소로 수집 진행합니다 --> {attr}")

        start_div = self.div_class_algocore(html=html, attrs={"class": attr[0]})
        data = list(
            chain.from_iterable(
                self.extract_format(div_1, attr[1]) for div_1 in start_div
            )
        )
        return data


class DaumNewsDataCrawling(DaumNews):

    def extract_format(self, tag: str) -> Generator:
        """
        HTML에서 뉴스 데이터를 생성하는 제너레이터 함수.

        Args:
            tag (str): 뉴스 페이지의 HTML 내용

        Yields:
            dict: 뉴스 제목, 기사 시간, URL, context가 포함된 딕셔너리
        """
        return (
            create_news_data(
                title=self.strong_in_class(div_2).find("a").get_text(strip=True),
                article_time=self.span_in_class(div_2).get_text(strip=True),
                url_type=(self.strong_in_class(div_2).find("a")),
            )
            for div_2 in self.li_in_data_docid(tag)
        )

    def news_info_collect(self, html: str) -> UrlDictCollect:
        """HTML 소스에서 요소 추출을 시작함.

        Args:
            html_source (str): HTML 소스 코드 문자열.
        Returns:
            list[dict[str, str, str]]: 각 뉴스 항목에 대한 'url', 'date', 'title'을 포함하는 딕셔너리 리스트.
        """
        start = self.ul_class_c_list_basic(html=html, attrs={"class": "c-list-basic"})
        data = list(chain.from_iterable(self.extract_format(div_1) for div_1 in start))
        return data
