import time
import random
import logging
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from common.utils.error_handling import SeleniumExceptionType
from crawling.src.core.types import ChromeDriver


class MouseController:
    """사람처럼 보이는 마우스 움직임을 시뮬레이션하는 클래스

    이 클래스는 마우스 이동, 클릭, 호버링 등 사용자와 비슷한 마우스 동작을 구현합니다.
    """

    def __init__(self, driver: ChromeDriver) -> None:
        """마우스 컨트롤러 초기화

        Args:
            driver: 셀레니움 웹드라이버 인스턴스
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def move_to_element(self, selector: str) -> bool:
        """특정 요소로 마우스 이동

        Args:
            selector: 요소를 찾기 위한 CSS 셀렉터

        Returns:
            요소로 이동 성공 여부
        """
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].is_displayed():
                element = elements[0]
                ActionChains(self.driver).move_to_element(element).perform()
                self.logger.info(f"요소 {selector}로 마우스 이동")
                return True
            return False
        except SeleniumExceptionType as e:
            # 예외 타입에 따른 특정 처리를 할 수 있음
            if isinstance(e, NoSuchElementException):
                self.logger.warning(f"요소 {selector}를 찾을 수 없음")
            elif isinstance(e, StaleElementReferenceException):
                self.logger.warning(f"요소 {selector}가 지금은 이용할 수 없음")
            else:
                self.logger.error(f"마우스 이동 중 오류 발생: {e}")
            return False

    def random_mouse_movements(self, count: int = 3) -> None:
        """화면 내에서 랜덤한 마우스 움직임 생성

        Args:
            count: 생성할 마우스 움직임 수
        """
        try:
            # 화면 사이즈 가져오기
            width = self.driver.execute_script("return window.innerWidth")
            height = self.driver.execute_script("return window.innerHeight")

            # 초기 위치로 마우스 이동
            ActionChains(self.driver).move_to_element(
                self.driver.find_element(By.TAG_NAME, "body")
            ).perform()
            time.sleep(0.5)  # 초기 위치 안정화

            successful_moves = 0
            attempts = 0
            max_attempts = count * 2  # 최대 시도 횟수는 요청한 움직임 수의 2배

            # 요청한 수만큼 움직임 생성 시도
            while successful_moves < count and attempts < max_attempts:
                attempts += 1

                try:
                    # 1. 중요 요소로 이동 시도 (70% 확률)
                    if random.random() > 0.3:
                        # 상호작용 가능한 요소들 필터링
                        interactable_elements = []

                        # 중요 요소들 가져오기
                        potential_elements = (
                            self.driver.find_elements(By.TAG_NAME, "input")[:5]
                            + self.driver.find_elements(By.TAG_NAME, "a")[:5]
                            + self.driver.find_elements(By.TAG_NAME, "button")[:3]
                            + self.driver.find_elements(
                                By.CSS_SELECTOR, ".button, .btn"
                            )[:3]
                        )

                        # 상호작용 가능한 요소만 필터링
                        for element in potential_elements:
                            try:
                                if (
                                    element
                                    and element.is_displayed()
                                    and element.is_enabled()
                                ):
                                    # 요소의 크기와 위치 확인 (크기가 0인 요소 제외)
                                    size = element.size
                                    location = element.location

                                    if (
                                        size["width"] > 0
                                        and size["height"] > 0
                                        and location["x"] >= 0
                                        and location["y"] >= 0
                                        and location["x"] < width
                                        and location["y"] < height
                                    ):

                                        # 실제로 화면에 표시되고 상호작용 가능한 요소만 추가
                                        interactable_elements.append(element)
                            except SeleniumExceptionType as e:
                                # 요소 분석 중 오류 발생 시 해당 요소는 건너뜀
                                continue

                        if interactable_elements:
                            # 랜덤하게 상호작용 가능한 요소 선택
                            element = random.choice(interactable_elements)

                            # 스크롤이 필요한지 확인
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                element,
                            )
                            time.sleep(random.uniform(0.3, 0.7))  # 스크롤 대기

                            # 요소로 이동 - 클릭 없이 마우스만 이동
                            try:
                                # 마우스를 요소 위로 이동시키되 클릭하지 않음
                                # 먼저 마우스를 body로 이동시켜 초기화
                                body = self.driver.find_element(By.TAG_NAME, "body")
                                actions = ActionChains(self.driver)
                                actions.move_to_element(body).perform()
                                time.sleep(random.uniform(0.1, 0.3))

                                # 이제 타겟 요소로 부드럽게 이동 (클릭 없음)
                                actions = ActionChains(self.driver)
                                actions.move_to_element(element).pause(
                                    random.uniform(0.2, 0.5)
                                ).perform()

                                # 요소 위에서 약간의 랜덤 움직임 추가 (보다 자연스러움)
                                small_offset_x = random.randint(-5, 5)
                                small_offset_y = random.randint(-3, 3)
                                ActionChains(self.driver).move_by_offset(
                                    small_offset_x, small_offset_y
                                ).perform()

                            except SeleniumExceptionType as e:
                                self.logger.warning(
                                    f"세밀한 마우스 이동 실패, 기본 방식 사용: {e}"
                                )
                                # 실패시에도 클릭을 방지하기 위해 단순히 이동만 수행
                                actions = ActionChains(self.driver)
                                actions.move_to_element(element).perform()

                            self.logger.info(
                                f"랜덤 요소로 마우스 이동 (#{successful_moves+1})"
                            )
                        else:
                            # 상호작용 가능한 요소가 없으면 안전한 좌표 이동으로 대체
                            raise NoSuchElementException("상호작용 가능한 요소 없음")
                    else:
                        # 2. 또는 랜덤한 좌표로 이동 (30% 확률)
                        # 화면의 안전한 영역 내에서 랜덤 위치 선택
                        safe_margin = 100  # 화면 가장자리에서 100px 안쪽으로 제한
                        x_pos = random.randint(
                            safe_margin, max(width - safe_margin, safe_margin + 1)
                        )
                        y_pos = random.randint(
                            safe_margin, max(height - safe_margin, safe_margin + 1)
                        )

                        # 현재 위치 기준 상대적 이동으로 변환
                        current_x = self.driver.execute_script(
                            "return window.innerWidth/2"
                        )
                        current_y = self.driver.execute_script(
                            "return window.innerHeight/2"
                        )

                        x_offset = x_pos - current_x
                        y_offset = y_pos - current_y

                        # 움직임 크기를 제한하여 자연스럽게 만들기
                        if abs(x_offset) > 300:
                            x_offset = 300 if x_offset > 0 else -300
                        if abs(y_offset) > 300:
                            y_offset = 300 if y_offset > 0 else -300

                        ActionChains(self.driver).move_by_offset(
                            x_offset, y_offset
                        ).perform()
                        self.logger.info(
                            f"안전 범위 내 마우스 이동: ({x_offset}, {y_offset})"
                        )

                    # 움직임 성공 카운트 증가
                    successful_moves += 1

                    # 사람처럼 잠시 대기
                    time.sleep(random.uniform(0.3, 1.2))

                except Exception as e:
                    # 예외 타입에 따라 다른 처리
                    self.logger.warning(f"마우스 이동 #{attempts} 실패: {e}")

                    # 오류 발생 시 초기 위치로 재설정 시도
                    try:
                        # 마우스를 페이지 중앙으로 초기화
                        ActionChains(self.driver).move_to_element(
                            self.driver.find_element(By.TAG_NAME, "body")
                        ).perform()
                        time.sleep(0.5)
                    except SeleniumExceptionType:
                        # 복구 실패 시 포기하고 다음 시도로 진행
                        pass

            self.logger.info(f"{successful_moves}/{count} 마우스 움직임 생성 완료")

        except SeleniumExceptionType as e:
            self.logger.warning(f"마우스 움직임 초기화 중 오류: {e}")

    def move_to_element_and_click(self, element) -> bool:
        """WebElement 객체로 마우스 이동 후 클릭

        Args:
            element: 클릭할 WebElement 객체

        Returns:
            클릭 성공 여부
        """
        try:
            if element and element.is_displayed():
                # 사람처럼 먼저 요소로 이동한 후 잠시 대기 후 클릭
                ActionChains(self.driver).move_to_element(element).pause(
                    random.uniform(0.3, 0.7)
                ).click().perform()
                self.logger.info(f"WebElement 객체 클릭")
                return True
            return False
        except SeleniumExceptionType as e:
            # 예외 타입에 따른 특정 처리
            if isinstance(e, StaleElementReferenceException):
                self.logger.warning(f"요소가 지금은 이용할 수 없음")
            else:
                self.logger.error(f"요소 클릭 중 오류: {e}")
            return False

    def click_element(self, selector: str) -> bool:
        """특정 요소 클릭

        Args:
            selector: 클릭할 요소의 CSS 선택자

        Returns:
            클릭 성공 여부
        """
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            if not element.is_displayed() or not element.is_enabled():
                self.logger.warning(f"요소가 보이지 않거나 활성화되지 않음: {selector}")
                return False

            # 요소가 보이는지 확인하고 필요시 스크롤
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element,
            )
            time.sleep(random.uniform(0.5, 1.0))

            # 자연스러운 마우스 움직임 후 클릭
            actions = ActionChains(self.driver)
            actions.move_to_element(element).pause(
                random.uniform(0.3, 0.7)
            ).click().perform()

            self.logger.info(f"요소 클릭 성공: {selector}")
            return True
        except SeleniumExceptionType as e:
            self.logger.error(f"요소 클릭 실패: {selector} - {e}")
            return False

    def click_and_go_back(self, selector: str, scroll_count: int = 2) -> bool:
        """요소 클릭 후 페이지 스크롤하고 뒤로가기

        Args:
            selector: 클릭할 요소의 CSS 선택자
            scroll_count: 수행할 스크롤 횟수

        Returns:
            성공 여부
        """
        try:
            # 요소 클릭
            if not self.click_element(selector):
                return False

            # 페이지 로딩 대기
            wait_time = random.uniform(1.0, 3.0)
            self.logger.info(f"페이지 로딩 대기: {wait_time:.1f}초")
            time.sleep(wait_time)

            # 페이지 스크롤 (자연스러움을 위해)
            for i in range(scroll_count):
                # 랜덤한 스크롤 거리
                scroll_amount = random.randint(300, 700)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.8, 2.0))

            # 추가 대기 시간 (페이지 읽는 시간 시뮬레이션)
            read_time = random.uniform(1.0, 5.0)
            self.logger.info(f"페이지 읽기 시뮬레이션: {read_time:.1f}초")
            time.sleep(read_time)

            # 뒤로 가기
            self.driver.back()
            self.logger.info("브라우저 뒤로가기 수행")

            # 검색 결과 페이지 로딩 대기
            time.sleep(random.uniform(1.0, 2.0))

            return True
        except SeleniumExceptionType as e:
            self.logger.error(f"클릭 및 뒤로가기 실패: {e}")
            return False
