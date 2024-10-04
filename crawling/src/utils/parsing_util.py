from __future__ import annotations
from pydantic import BaseModel
from collections import Counter

import pytz
from datetime import timedelta, datetime
from dateutil import parser

import re
import pandas as pd
from bs4 import BeautifulSoup

import time
import random
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)


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


class PageScroller:
    def __init__(self, driver: ChromeDriver, second_delay: bool = False) -> None:
        self.driver = driver
        self.second_delay = second_delay
        self.scroll_heights = [int(random.uniform(1000, 3000)) for _ in range(5)]

    def delay_function(self, i: int) -> None:
        if i % 3 == 0:
            print(i, "1초쉽니다")
            time.sleep(1)

    def fast_scroll(self, scroll_cal: int) -> None:
        """빠르게 스크롤"""
        current_position = self.driver.execute_script("return window.pageYOffset;")
        self.driver.execute_script(
            f"window.scrollTo(0, {current_position + scroll_cal})"
        )

    def smooth_type_scroll(
        self, scroll: int, steps: int = 10, delay: float = 0.05
    ) -> None:
        current_position = self.driver.execute_script("return window.pageYOffset;")
        step_size = scroll / steps

        for i in range(steps):
            self.driver.execute_script(
                f"window.scrollTo(0, {current_position + (step_size * (i + 1))})"
            )
            if self.second_delay:
                self.delay_function(i)

            time.sleep(delay)

    def check_and_close_popup(self) -> bool:
        try:
            popup_xpath = '//*[@id="PromoteSignUpPopUp"]/div[2]/i'
            popup = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.XPATH, popup_xpath))
            )
            self.driver.execute_script("arguments[0].click();", popup)
            popup.click()
            return True
        except (
            TimeoutException,
            NoSuchElementException,
            ElementNotInteractableException,
        ):
            return False

    def page_scroll(self) -> None:
        """스크롤을 5번에 걸쳐서 내리기, 3가지 스크롤 케이스 포함"""
        self.driver.implicitly_wait(10)

        # 3가지 스크롤 케이스 실행
        for scroll_distance in self.scroll_heights:
            popup = self.check_and_close_popup()
            if popup:
                print("팝업이 감지되어 닫습니다.")

            # 랜덤 스크롤 시작
            scroll_type = random.choice(["smooth", "fast", "slow"])
            if scroll_type == "smooth":
                print(f"부드러운 스크롤 실행 중: {scroll_distance}px")
                self.smooth_type_scroll(scroll_distance, steps=50, delay=0.2)
            elif scroll_type == "fast":
                print(f"빠른 스크롤 실행 중: {scroll_distance}px")
                self.fast_scroll(scroll_distance)
            elif scroll_type == "slow":
                print(f"느린 스크롤 실행 중: {scroll_distance}px")
                self.smooth_type_scroll(scroll_distance, steps=30, delay=0.3)
