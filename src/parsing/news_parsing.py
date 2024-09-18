from itertools import chain

from typing import Any, Generator
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
    NewsDataFormat,
)


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
            NewsDataFormat.create(
                title=href_from_text_preprocessing(a_tag.text[:20]),
                article_time=parse_time_ago(self.news_create_time_from_div(a_tag)),
                url=href_from_a_tag(a_tag),
            ).model_dump()
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
            NewsDataFormat.create(
                title=div_2.text[:20],
                url=href_from_a_tag(div_2, "url"),
                article_time=parse_time_ago(i),
            ).model_dump()
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
            NewsDataFormat.create(
                title=href_from_a_tag(self.strong_in_class(div_2).find("a")),
                url=self.strong_in_class(div_2).find("a").get_text(strip=True),
                article_time=parse_time_ago(
                    self.span_in_class(div_2).get_text(strip=True)
                ),
            ).model_dump()
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
