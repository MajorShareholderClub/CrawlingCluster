import time
import random
import logging
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from common.utils.error_handling import SeleniumExceptionType
from crawling.src.core.types import ChromeDriver


class TypingController:
    """사람처럼 보이는 타이핑 행동을 시뮬레이션하는 클래스

    이 클래스는 검색어 입력, 텍스트 삭제, 키보드 단축키 동작 등 타이핑 관련 동작을 구현합니다.
    """

    def __init__(self, driver: ChromeDriver) -> None:
        """타이핑 컨트롤러 초기화

        Args:
            driver: 셀레니움 웹드라이버 인스턴스
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def find_input_element(self, selectors: list[str]) -> Optional[object]:
        """다양한 선택자를 사용하여 입력 필드 요소 찾기

        Args:
            selectors: 시도할 CSS 선택자 목록

        Returns:
            찾은 요소 또는 None
        """
        for selector in selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].is_displayed():
                return elements[0]
        return None

    def type_text(self, element, text: str, natural: bool = True) -> bool:
        """텍스트를 사람처럼 천천히 입력

        Args:
            element: 텍스트를 입력할 요소
            text: 입력할 텍스트
            natural: 자연스러운 타이핑 속도 변화 적용 여부

        Returns:
            입력 성공 여부
        """
        try:
            # 사람처럼 글자별로 타이핑
            for char in text:
                element.send_keys(char)
                if natural:
                    # 사람이 타이핑하는 것처럼 속도 변화
                    delay = self._get_typing_delay(char)
                    time.sleep(delay)
                else:
                    # 일정한 속도로 타이핑
                    time.sleep(random.uniform(0.05, 0.1))

            # 가끔 오타를 내고 수정하는 행동 (10% 확률)
            if natural and random.random() < 0.1 and len(text) > 5:
                self._simulate_typing_mistake(element)

            return True
        except SeleniumExceptionType as e:
            self.logger.error(f"텍스트 입력 중 오류: {e}")
            return False

    def _get_typing_delay(self, char: str) -> float:
        """문자에 따른 타이핑 지연 시간 계산

        Args:
            char: 입력할 문자

        Returns:
            지연 시간(초)
        """
        # 복잡한 문자(특수문자 등)는 입력에 더 시간이 걸림
        if char in "!@#$%^&*()_+-={}|[]\\:\";'<>?,./":
            return random.uniform(0.1, 0.3)
        # 숫자는 중간 정도 속도
        elif char.isdigit():
            return random.uniform(0.08, 0.15)
        # 알파벳은 빠른 속도
        elif char.isalpha():
            return random.uniform(0.05, 0.12)
        # 공백은 생각하는 시간을 포함
        elif char.isspace():
            return random.uniform(0.1, 0.4)
        # 기타 문자
        else:
            return random.uniform(0.08, 0.2)

    def _simulate_typing_mistake(self, element) -> None:
        """타이핑 실수를 시뮬레이션

        Args:
            element: 입력 요소
        """
        # 몇 글자 지우기
        delete_count = random.randint(1, 3)
        self.logger.info(f"타이핑 실수 시뮬레이션: {delete_count}자 삭제")

        for _ in range(delete_count):
            element.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.1, 0.3))

        # 약간의 생각 시간
        time.sleep(random.uniform(0.3, 0.7))

        # 임의의 수정 문자열 입력
        correction = "abcdef"[:delete_count]  # 실제로는 지운 텍스트를 기억해야 함
        for char in correction:
            element.send_keys(char)
            time.sleep(random.uniform(0.08, 0.15))

    def clear_input(self, element) -> None:
        """입력 필드의 내용을 사람처럼 지우기

        Args:
            element: 내용을 지울 입력 요소
        """
        try:
            current_value = element.get_attribute("value")
            if not current_value:
                return

            action = ActionChains(self.driver)

            # 텍스트가 길면 전체 선택 후 삭제
            if len(current_value) > 10:
                # 운영체제에 따라 다른 단축키 사용
                if self.driver.capabilities.get("platformName", "").lower() == "mac":
                    action.key_down(Keys.COMMAND).send_keys("a").key_up(
                        Keys.COMMAND
                    ).perform()
                else:
                    action.key_down(Keys.CONTROL).send_keys("a").key_up(
                        Keys.CONTROL
                    ).perform()
                time.sleep(random.uniform(0.2, 0.4))
                action.send_keys(Keys.DELETE).perform()
            else:
                # 짧은 텍스트는 백스페이스로 한글자씩 지우기
                for _ in range(len(current_value)):
                    action.send_keys(Keys.BACK_SPACE).perform()
                    time.sleep(random.uniform(0.05, 0.1))

            # 지운 후 약간의 대기
            time.sleep(random.uniform(0.3, 0.6))
        except SeleniumExceptionType as e:
            self.logger.warning(f"입력 필드 내용 지우기 실패: {e}")

    def human_like_search(
        self, keyword: str, search_selectors: list[str] = None
    ) -> bool:
        """사람처럼 검색어 입력 및 검색 실행

        Args:
            keyword: 검색할 키워드
            search_selectors: 검색창을 찾기 위한 CSS 선택자 목록

        Returns:
            검색 성공 여부
        """
        if search_selectors is None:
            search_selectors = [
                "input[name='q']",
                "input[type='search']",
                "#search",
                ".search",
                "input.gLFyf",
            ]

        try:
            # 검색창 찾기
            search_box = self.find_input_element(search_selectors)
            if not search_box:
                self.logger.error("검색창을 찾을 수 없음")
                return False

            # 검색창에 포커스
            action = ActionChains(self.driver)
            action.move_to_element(search_box).click().perform()
            time.sleep(random.uniform(0.5, 1.0))

            # 기존 내용 지우기
            self.clear_input(search_box)

            # 검색어 입력
            self.type_text(search_box, keyword, natural=True)

            # 검색 전 잠시 생각하는 시간
            time.sleep(random.uniform(0.8, 1.5))

            # 검색 실행 (70% 확률로 엔터키, 30% 확률로 검색 버튼 클릭)
            if random.random() < 0.7:
                search_box.send_keys(Keys.RETURN)
                self.logger.info("엔터키로 검색 실행")
            else:
                try:
                    search_buttons = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "button[type='submit'], input[type='submit'], .search-button",
                    )
                    if search_buttons:
                        button = search_buttons[0]
                        action.move_to_element(button).click().perform()
                        self.logger.info("검색 버튼 클릭으로 검색 실행")
                    else:
                        search_box.send_keys(Keys.RETURN)
                        self.logger.info("검색 버튼을 찾을 수 없어 엔터키 사용")
                except SeleniumExceptionType:
                    search_box.send_keys(Keys.RETURN)
                    self.logger.info("검색 버튼 클릭 실패, 엔터키 사용")

            # 검색 결과 로딩 대기
            loading_wait = random.uniform(2.0, 4.0)
            self.logger.info(f"검색 결과 로딩 중... ({loading_wait:.1f}초)")
            time.sleep(loading_wait)

            return True
        except SeleniumExceptionType as e:
            self.logger.error(f"검색 수행 중 오류 발생: {e}")
            return False
