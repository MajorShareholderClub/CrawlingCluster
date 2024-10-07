from __future__ import annotations

import pytz
from datetime import datetime, timedelta
from dateutil import parser
from pydantic import BaseModel

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def url_create(url: str) -> str:
    """URL 합성
    Args:
        url (str): url

    Returns:
        str: 완품 URL
            - ex) naver.com -> https://www.naver.com
    """
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        return f"https://{parsed_url.netloc or url}/"
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"


def url_addition(base_url: str, url: str) -> str:
    """/~ 로 끝나는 URL을 붙여주는 함수
    Args:
        base_url (str): 기준 URL
        url (str): 추가할 URL

    Returns:
        str: 합쳐진 URL
    """
    if url.startswith("/"):
        return urljoin(url_create(base_url), url)
    return url


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

        if unit is None:
            return time_str

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
    except TypeError as error:
        date_obj = datetime.strptime(time_str, "%Y.%m.%d")
        if date_obj:
            return date_obj.strftime("%Y-%m-%d")
    except Exception as error:
        return None


class NewsDataFormat(BaseModel):
    url: str
    title: str
    article_time: str
    timestamp: str
    time_ago: str

    @classmethod
    def create(cls, **kwargs) -> NewsDataFormat:
        korea_seoul_time = datetime.now(pytz.timezone("Asia/Seoul")).strftime(
            "%Y-%m-%d"
        )
        # kwargs에 timestamp를 추가하여 NewsData 인스턴스 생성
        kwargs["timestamp"] = korea_seoul_time
        return cls(**kwargs)
