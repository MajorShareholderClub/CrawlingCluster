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
from selenium.webdriver import ActionChains

from crawling.src.core.types import ChromeDriver
from config.setting import WITH_TIME


def web_element_clicker(driver: ChromeDriver, xpath: str):
    element = WebDriverWait(driver, WITH_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    return element


class PageScroller:
    """사람처럼 스크롤하는 클래스"""

    def __init__(self, driver: ChromeDriver, second_delay: bool = False) -> None:
        self.driver = driver
        self.second_delay = second_delay
        # 다양한 스크롤 높이 설정
        self.scroll_heights = [int(random.uniform(300, 1500)) for _ in range(5)]
        # 최대 페이지 높이 저장용
        self.max_height = 0
        # 현재 스크롤 위치
        self.current_position = 0

    def move_mouse_randomly(self) -> None:
        """마우스를 화면 내 랜덤한 위치로 이동"""
        try:
            # 뷰포트 크기 가져오기
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")

            # 랜덤 위치 계산
            x = random.randint(10, viewport_width - 10)
            y = random.randint(10, viewport_height - 10)

            # ActionChains로 마우스 이동
            actions = ActionChains(self.driver)
            actions.move_by_offset(x, y).perform()

            # 0.1~0.8초 사이 랜덤 일시정지
            time.sleep(random.uniform(0.1, 0.8))
        except Exception as e:
            # 마우스 이동 중 오류는 무시 (일부 환경에서 지원되지 않을 수 있음)
            print(f"마우스 이동 중 오류 (무시됨): {e}")
            pass

    def simulate_reading(self, min_time: float = 2.0, max_time: float = 8.0) -> None:
        """페이지 읽는 시간 시뮬레이션"""
        read_time = random.uniform(min_time, max_time)
        print(f"페이지 내용을 {read_time:.1f}초 동안 읽는 중...")
        time.sleep(read_time)

    def delay_function(self, i: int) -> None:
        """불규칙한 일시정지 추가"""
        # 30% 확률로 일시정지
        if random.random() < 0.3:
            pause_time = random.uniform(0.2, 2.0)
            print(f"{i}번째 스크롤, {pause_time:.1f}초 일시정지")
            time.sleep(pause_time)

    def fast_scroll(self, scroll_cal: int) -> None:
        """빠르게 스크롤하되 2단계로 나누어 더 자연스럽게"""
        self.current_position = self.driver.execute_script("return window.pageYOffset;")

        # 스크롤을 2단계로 나누어 실행
        first_part = scroll_cal * random.uniform(0.3, 0.7)
        second_part = scroll_cal - first_part

        # 첫 번째 스크롤
        self.driver.execute_script(
            f"window.scrollTo(0, {self.current_position + first_part})"
        )
        time.sleep(random.uniform(0.1, 0.3))  # 짧은 대기

        # 두 번째 스크롤
        self.driver.execute_script(
            f"window.scrollTo(0, {self.current_position + second_part})"
        )

    def smooth_type_scroll(
        self, scroll: int, steps: int = 10, delay: float = 0.05
    ) -> None:
        """불규칙한 속도로 부드럽게 스크롤"""
        self.current_position = self.driver.execute_script("return window.pageYOffset;")

        # 불규칙한 스텝 크기 생성
        irregular_steps = []
        total = 0
        for _ in range(steps):
            step = random.uniform(0.5, 1.5)  # 0.5~1.5 사이의 랜덤 계수
            irregular_steps.append(step)
            total += step

        # 정규화하여 총합이 1이 되도록 조정
        normalized_steps = [step / total for step in irregular_steps]

        # 불규칙한 스텝으로 스크롤
        current_scroll = 0
        for i, step_ratio in enumerate(normalized_steps):
            current_scroll += scroll * step_ratio
            self.driver.execute_script(
                f"window.scrollTo(0, {self.current_position + current_scroll})"
            )

            if self.second_delay:
                self.delay_function(i)

            # 불규칙한 지연 시간
            actual_delay = delay * random.uniform(0.8, 1.2)
            time.sleep(actual_delay)

            # 5% 확률로 잠시 위로 스크롤백
            if random.random() < 0.05 and i > 2:
                back_scroll = random.uniform(50, 150)
                self.driver.execute_script(
                    f"window.scrollTo(0, {self.current_position + current_scroll - back_scroll})"
                )
                time.sleep(random.uniform(0.3, 0.8))
                self.driver.execute_script(
                    f"window.scrollTo(0, {self.current_position + current_scroll})"
                )

    def hover_random_elements(self, num_elements: int = 3) -> None:
        """페이지 내 랜덤 요소에 마우스 호버"""
        try:
            # 링크, 버튼, 이미지 등 상호작용 가능한 요소들 찾기
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, "a, button, img, div[onclick], [role=button]"
            )

            if len(elements) > 0:
                # 랜덤하게 몇 개 선택
                selected = random.sample(elements, min(num_elements, len(elements)))

                for element in selected:
                    try:
                        # 요소가 보이는지 확인
                        if element.is_displayed():
                            actions = ActionChains(self.driver)
                            actions.move_to_element(element).perform()
                            # 0.3~2초 사이 랜덤하게 호버 유지
                            time.sleep(random.uniform(0.3, 2))
                    except:
                        pass  # 특정 요소 호버 실패시 무시하고 계속 진행
        except Exception as e:
            print(f"호버 중 오류 (무시됨): {e}")
            pass

    def check_and_close_popup(self) -> bool:
        """팝업 확인 및 닫기"""
        try:
            popup_xpath = '//*[@id="PromoteSignUpPopUp"]/div[2]/i'
            popup = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.XPATH, popup_xpath))
            )
            # 실제 사람처럼 약간의 지연 시간 후 클릭
            time.sleep(random.uniform(0.5, 1.5))
            self.driver.execute_script("arguments[0].click();", popup)
            return True
        except (
            TimeoutException,
            NoSuchElementException,
            ElementNotInteractableException,
        ):
            return False

    def scroll_back_slightly(self) -> None:
        """약간 위로 스크롤"""
        current = self.driver.execute_script("return window.pageYOffset;")
        back_pixels = random.randint(50, 200)
        self.driver.execute_script(
            f"window.scrollTo(0, {max(0, current - back_pixels)})"
        )
        time.sleep(random.uniform(0.5, 1.5))

    def page_scroll(self) -> None:
        """사람과 유사한 패턴으로 페이지 스크롤"""
        self.driver.implicitly_wait(10)

        # 최대 페이지 높이 확인
        self.max_height = self.driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
        )

        # 실제 사람처럼 페이지 탐색
        for i, scroll_distance in enumerate(self.scroll_heights):
            # 20% 확률로 마우스 랜덤 이동
            if random.random() < 0.2:
                self.move_mouse_randomly()

            # 팝업 확인 및 닫기
            popup = self.check_and_close_popup()
            if popup:
                print("팝업이 감지되어 닫습니다.")
                time.sleep(random.uniform(0.3, 1.0))  # 팝업 닫은 후 잠시 대기

            # 사람이 실제로 읽는 시간 시뮬레이션
            # 처음 페이지에 도달했거나, 50% 확률로 읽는 시간 추가
            if i == 0 or random.random() < 0.5:
                self.simulate_reading()

            # 페이지의 스크롤 위치에 따라 실제 스크롤 거리 조정
            current_pos = self.driver.execute_script("return window.pageYOffset;")
            remaining_height = self.max_height - current_pos
            actual_distance = min(
                scroll_distance, int(remaining_height * 0.8)
            )  # 최대 80%까지만 스크롤

            # 스크롤 방식 랜덤 선택
            scroll_weights = [0.6, 0.2, 0.2]  # 부드러운, 빠른, 느린 스크롤 확률
            scroll_type = random.choices(
                ["smooth", "fast", "slow"], weights=scroll_weights, k=1
            )[0]

            if scroll_type == "smooth":
                print(f"부드러운 스크롤 실행 중: {actual_distance}px")
                self.smooth_type_scroll(
                    actual_distance,
                    steps=random.randint(15, 30),
                    delay=random.uniform(0.05, 0.2),
                )
            elif scroll_type == "fast":
                print(f"빠른 스크롤 실행 중: {actual_distance}px")
                self.fast_scroll(actual_distance)
                time.sleep(random.uniform(0.3, 1.0))  # 빠른 스크롤 후 잠시 대기
            elif scroll_type == "slow":
                print(f"느린 스크롤 실행 중: {actual_distance}px")
                self.smooth_type_scroll(
                    actual_distance,
                    steps=random.randint(25, 40),
                    delay=random.uniform(0.1, 0.3),
                )

            # 15% 확률로 위로 약간 스크롤백
            if random.random() < 0.15:
                self.scroll_back_slightly()
                print("내용을 다시 확인하기 위해 약간 위로 스크롤")

            # 10% 확률로 페이지 내 요소에 마우스 호버
            if random.random() < 0.1:
                self.hover_random_elements()

            # 스크롤 후 불규칙한 대기 시간
            wait_time = random.uniform(0.5, 3.0)
            print(f"다음 스크롤까지 {wait_time:.1f}초 대기 중...")
            time.sleep(wait_time)

        # 페이지 탐색 완료 후 콘텐츠 읽는 시간 시뮬레이션
        self.simulate_reading(min_time=3.0, max_time=10.0)


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
