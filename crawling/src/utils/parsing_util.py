from __future__ import annotations
from pydantic import BaseModel
from collections import Counter
import pandas as pd

import pytz
from datetime import timedelta, datetime
from dateutil import parser

import re
from bs4 import BeautifulSoup
from newspaper import Article


def time_extract(format: str) -> str:
    try:
        # 날짜와 시간 문자열을 datetime 객체로 변환
        date_obj = datetime.strptime(format, "%a, %d %b %Y %H:%M:%S %z")

        # 원하는 형식으로 변환
        formatted_date = date_obj.strftime("%Y-%m-%d: %H:%M:%S")
        return formatted_date
    except ValueError:
        parsed_time = parser.parse(format)
        return parsed_time.strftime("%Y-%m-%d %H:%M")


def href_from_a_tag(a_tag: BeautifulSoup, element: str = "href") -> str:
    """URL 뽑아내기

    Returns:
        str: [URL, ~~]
    """
    if isinstance(a_tag, tuple):
        element = a_tag[1]
        return a_tag[0].get(element)
    return a_tag.get(element)


def href_from_text_preprocessing(text: str) -> str:
    """텍스트 전처리

    Args:
        text (str): URL title 및 시간
            - ex) 어쩌구 저쩌구...12시간

    Returns:
        str: 특수문자 및 시간제거
            - ex) 어쩌구 저쩌구
    """
    return re.sub(r"\b\d+시간 전\b|\.{2,}|[^\w\s]", "", text)


def parse_time_ago(time_str: str) -> str:
    """
    주어진 시간 문자열을 현재 한국 시간으로부터의 시간으로 변환

    Args:
        time_str (str): 예를 들어 '3시간 전', '2분 전', '1일 전' 등

    Returns:
        str: 한국 시간으로부터 주어진 시간 만큼 이전의 시간 (YYYY-MM-DD HH:MM 형식)
    """

    try:
        korea_tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(korea_tz)

        # 기본적으로 시간 차이를 0으로 설정
        time_delta = timedelta()

        # 정규 표현식으로 숫자와 시간 단위를 추출 (분 단위 추가)
        match = re.match(r"(\d+)\s*(시간|h|분|m|초|일|d)?\s*전?", time_str)
        value = int(match.group(1))
        unit = match.group(2)
        # 단위에 따른 시간 차이 계산
        if unit in ["시간", "h"]:
            time_delta = timedelta(hours=value)
        elif unit in ["분", "m"]:
            time_delta = timedelta(minutes=value)
        elif unit in ["일", "d"]:
            time_delta = timedelta(days=value)

        # 현재 시간에서 delta를 빼기
        parsed_time: datetime = now - time_delta
        return parsed_time.strftime("%Y-%m-%d %H:%M")
    except Exception as error:
        date_obj = datetime.strptime(time_str, "%Y.%m.%d")
        if date_obj:
            return date_obj.strftime("%Y-%m-%d")


def url_news_text(url: str) -> str:
    try:
        a = Article(url=url, language="ko")
        a.download()
        a.parse()
        return a.text
    except:
        pass


class NewsDataFormat(BaseModel):
    url: str
    title: str
    article_time: str
    timestamp: str
    content: str | None

    @classmethod
    def create(cls, **kwargs) -> NewsDataFormat:
        korea_seoul_time = datetime.now(pytz.timezone("Asia/Seoul")).strftime(
            "%Y-%m-%d"
        )
        # kwargs에 timestamp를 추가하여 NewsData 인스턴스 생성
        kwargs["timestamp"] = korea_seoul_time
        return cls(**kwargs)


class NewsWeightScoring:
    def __init__(
        self,
        content: str,
        published_date: datetime,
        timestamp: datetime,
    ) -> None:
        """
        Args:
            content (str): 기사 본문
            keywords (list[str]): 키워드 (가상화폐 및 관련 카테고리)
            published_date (datetime): 기사 생성 날짜
            timestamp (datetime): 현재 날짜
        """
        self.content = content
        self.keywords = pd.read_csv("config/keywords.csv")
        self.published_date = published_date
        self.current_date = timestamp

    def find_keywords(self) -> dict[str, int]:
        """
        Returns:
            dict: 발견된 키워드와 그 개수를 포함하는 딕셔너리
        """
        found_keywords = (
            keyword
            for keyword in self.keywords
            for keyword in re.findall(rf"\b{re.escape(keyword)}\b", self.content)
        )
        keyword_count = Counter(found_keywords)
        return keyword_count.most_common()

    def calculate_length_weight(self) -> float:
        """
        Returns:
            float: 기사의 길이에 따른 가중치 (최대 0.1점)
        """
        word_count = len(self.content.split())
        weight = min((word_count / 1000) * 0.01, 0.1)
        return weight

    def calculate_sentence_keyword_weight(self) -> float:
        """
        Returns:
            float: 문장당 키워드 개수에 대한 가중치 (최대 0.3점)
        """
        sentences = self.content.split(".")
        valid_sentence_count = sum(
            1
            for sentence in sentences
            if any(keyword in sentence for keyword in self.keywords)
        )
        total_sentences = len(sentences)
        weight = 0.0

        if total_sentences > 0:
            keyword_ratio = valid_sentence_count / total_sentences
            if valid_sentence_count >= 4:
                weight = 0.3 * min(keyword_ratio * 1.0, 1.0)

        return weight

    def calculate_valid_keyword_weight(self) -> float:
        """
        Returns:
            float: 유효 키워드 개수 및 비율에 대한 가중치 (최대 0.2점)
        """
        keyword_count = self.find_keywords()
        valid_keyword_count = sum(keyword_count.values())
        total_word_count = len(self.content.split())
        weight = 0.0

        if valid_keyword_count >= 30:
            weight += 0.1

        keyword_percentage = (
            (valid_keyword_count / total_word_count) * 0.1
            if total_word_count > 0
            else 0.0
        )
        weight += keyword_percentage
        return weight

    def calculate_date_weight(self) -> float:
        """
        Returns:
            float: 기사 날짜 기준 최신 순 가중치 (최대 0.4점)
        """
        cal_day: int = (self.current_date - self.published_date).days
        quarters_passed = cal_day // 90

        weight = max(0.4 - (quarters_passed * 0.1), 0.0)
        return weight

    def calculate_total_weight(self) -> float:
        """
        Returns:
            float: 총 가중치 점수
        """
        length_weight: float = self.calculate_length_weight()
        date_weight: float = self.calculate_date_weight()
        sentence_keyword_weight: float = self.calculate_sentence_keyword_weight()
        valid_keyword_weight: float = self.calculate_valid_keyword_weight()

        total_weight = (
            length_weight + sentence_keyword_weight + valid_keyword_weight + date_weight
        )

        return min(total_weight, 1.0)  # 최대 가중치는 1.0
