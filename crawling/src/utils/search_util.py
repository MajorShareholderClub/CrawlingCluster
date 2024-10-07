from collections import Counter
from datetime import datetime

import re
import pandas as pd

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


from crawling.src.core.types import ChromeDriver
from crawling.config.setting import WITH_TIME


def web_element_clicker(driver: ChromeDriver, xpath: str):
    element = WebDriverWait(driver, WITH_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    return element


class PageScroller:
    """스크롤 내리는 클래스"""

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


class NewsWeightScoring:
    """가중치 계산"""

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
