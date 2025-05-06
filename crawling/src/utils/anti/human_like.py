import logging
import time
import random
from typing import List, Optional, Union

from common.utils.error_handling import SeleniumExceptionType
from crawling.src.core.types import ChromeDriver
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
)

# 내부 컨트롤러 임포트
from crawling.src.utils.anti.mouse_controller import MouseController
from crawling.src.utils.anti.typing_controller import TypingController
from crawling.src.utils.anti.delay_controller import DelayController
from crawling.src.utils.anti.detector import RobotDetector


class HumanLikeInteraction:
    """사람처럼 웹사이트와 상호작용하는 기능을 통합 제공하는 파사드 클래스

    이 클래스는 마우스 동작, 타이핑, 지연 등의 개별 컨트롤러를 통합적으로 관리합니다.
    외부에서는 이 클래스만 사용하면 모든 안티봇 기능에 접근할 수 있습니다.
    """

    def __init__(self, driver: ChromeDriver) -> None:
        """HumanLikeInteraction 파사드 초기화

        Args:
            driver: 셀레니움 웹드라이버 인스턴스
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)

        # 개별 컨트롤러 초기화
        self.mouse = MouseController(driver)
        self.keyboard = TypingController(driver)
        self.delay = DelayController(driver)
        self.detector = RobotDetector(driver)

    def is_robot_page(self) -> bool:
        """로봇 감지 페이지인지 확인

        Returns:
            로봇 감지 페이지 여부
        """
        return self.detector.is_robot_page()

    def get_detected_robot_type(self) -> Optional[str]:
        """감지된 로봇 방지 메커니즘 타입 확인

        Returns:
            감지된 로봇 방지 타입 또는 None
        """
        return self.detector.get_detected_type()

    def mask_navigator(self) -> None:
        """웹드라이버 감지 방지를 위한 navigator 객체 마스킹"""
        self.detector.mask_navigator()

    def human_like_search(
        self, keyword: str, search_selectors: Optional[List[str]] = None
    ) -> bool:
        """사람처럼 검색어 입력 및 검색 실행

        Args:
            keyword: 검색할 키워드
            search_selectors: 검색창을 찾기 위한 CSS 선택자 목록

        Returns:
            검색 성공 여부
        """
        return self.keyboard.human_like_search(keyword, search_selectors)

    def random_mouse_movements(self, count: int = 3) -> None:
        """랜덤한 마우스 움직임 생성

        Args:
            count: 움직임 횟수
        """
        self.mouse.random_mouse_movements(count)

    def natural_scroll_and_read(self, max_scrolls: int = 3) -> None:
        """자연스럽게 스크롤하고 콘텐츠 읽기

        Args:
            max_scrolls: 최대 스크롤 횟수
        """
        self.delay.natural_scroll(max_scrolls)
        self.delay.read_content_elements()

    def smart_delay(self) -> float:
        """상황에 맞는 지능적 대기 시간 적용

        Returns:
            적용된 대기 시간(초)
        """
        return self.delay.smart_delay()

    def simulate_reading(self) -> None:
        """콘텐츠 읽기 행동 시뮬레이션"""
        self.delay.read_content_elements()

    def click_element(self, selector: str) -> bool:
        """특정 요소 클릭

        Args:
            selector: 클릭할 요소의 CSS 선택자

        Returns:
            클릭 성공 여부
        """
        return self.mouse.click_element(selector)

    def click_and_browse_then_back(self, element: WebElement) -> bool:
        """요소 클릭, 페이지 탐색 후 뒤로가기

        Args:
            element: 클릭할 웹 요소

        Returns:
            성공 여부
        """
        try:
            # 요소가 화면에 보이도록 스크롤
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element,
            )
            time.sleep(random.uniform(0.5, 1.0))

            # 요소 클릭
            element.click()
            self.logger.info("검색 결과 클릭 완료")

            # 페이지 로딩 대기
            wait_time = random.uniform(1.0, 3.0)
            self.logger.info(f"페이지 로딩 대기: {wait_time:.1f}초")
            time.sleep(wait_time)

            # 자연스러운 스크롤 동작
            scroll_count = random.randint(1, 3)
            for i in range(scroll_count):
                # 랜덤 스크롤 거리
                scroll_amount = random.randint(300, 700)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.8, 2.0))

            # 추가 대기 (읽는 시간 시뮬레이션)
            read_time = random.uniform(2.0, 6.0)
            self.logger.info(f"컨텐츠 읽기 시뮬레이션: {read_time:.1f}초")
            time.sleep(read_time)

            # 뒤로 가기
            self.driver.back()
            self.logger.info("브라우저 뒤로가기 수행")

            # 이전 페이지 로딩 대기
            time.sleep(random.uniform(1.0, 2.0))

            return True
        except SeleniumExceptionType as e:
            self.logger.error(f"페이지 탐색 중 오류: {e}")
            return False

    def handle_robot_detection(self) -> bool:
        """로봇 감지 상황 처리 시도

        Returns:
            처리 성공 여부
        """
        detected_type = self.get_detected_robot_type()
        if not detected_type:
            return True  # 로봇 감지 없음

        self.logger.warning(f"로봇 감지 발생: {detected_type}")

        # 타입별 대응 전략
        if detected_type == "ip_block":
            self.logger.info("IP 차단 감지. 프록시 전환 시도 필요.")
            return False  # 프록시 변경은 상위 레벨에서 처리

        if detected_type == "captcha":
            self.logger.info("CAPTCHA 감지. 우회 시도...")
            # CAPTCHA 우회 로직 (성공 가능성 낮음)
            self.random_mouse_movements()
            self.smart_delay()
            return False  # 실패로 간주하고 세션 재시작 유도

        # 일반적인 로봇 감지 대응
        self.logger.info("일반 로봇 감지. 자연스러운 행동으로 우회 시도...")
        self.mask_navigator()
        self.random_mouse_movements()
        self.natural_scroll_and_read()
        self.smart_delay()

        # 우회 결과 확인
        if self.is_robot_page():
            self.logger.warning("로봇 감지 우회 실패")
            return False
        else:
            self.logger.info("로봇 감지 우회 성공")
            return True


class AntiRobotSearch:
    """로봇 감지를 우회하는 검색 기능 제공 클래스

    이 클래스는 세션 관리 및 검색 로직을 담당하며, 로봇 감지 시 대응 전략을 구현합니다.
    """

    def __init__(self, driver: ChromeDriver) -> None:
        """Anti-Robot 검색 관리자 초기화

        Args:
            driver: 셀레니움 웹드라이버 인스턴스
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.human_like = HumanLikeInteraction(driver)

    def restart_session(self, wait_time: int = 10) -> bool:
        """세션을 재시작하여 차단을 우회

        Args:
            wait_time: 세션 재시작 전 대기 시간(초)

        Returns:
            세션 재시작 성공 여부
        """
        try:
            self.logger.info(f"세션 재시작 중... ({wait_time}초 대기)")
            time.sleep(wait_time)  # 재시작 전 대기

            # 현재 URL 저장
            current_url = self.driver.current_url

            # 드라이버 재시작
            try:
                # 이전 드라이버 종료
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"이전 드라이버 종료 중 오류 (무시됨): {e}")

            # 새 드라이버 생성
            try:
                # 신규 옵션 생성
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--disable-notifications")
                options.add_argument("--start-maximized")

                # 새 사용자 프로필 사용
                options.add_argument("--user-data-dir=/tmp/temp_chrome_profile")
                options.add_argument("--profile-directory=ProfNew")

                # 바뀐 User-Agent 사용
                options.add_argument(
                    f"--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)} Safari/537.36"
                )

                # 새 드라이버 초기화
                import undetected_chromedriver as uc

                self.driver = uc.Chrome(options=options, headless=False)
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)

                # 마우스 및 키보드 컨트롤러 재초기화
                self.human_like = HumanLikeInteraction(self.driver)
                self.mouse = MouseController(self.driver)
                self.keyboard = TypingController(self.driver)
                self.delay = DelayController(self.driver)

                # Navigator 속성 마스킹 다시 적용
                self.human_like.mask_navigator()

                self.logger.info("세션 재시작 완료")
                return True
            except Exception as e:
                self.logger.error(f"새 드라이버 생성 실패: {e}")
                return False

        except Exception as e:
            self.logger.error(f"세션 재시작 실패: {e}")
            return False

    def search_with_anti_robot(self, url: str, keyword: str) -> bool:
        """로봇 감지를 우회하기 위한 사람형 검색 수행

        Args:
            url: 접속할 URL (검색 시작 페이지)
            keyword: 검색할 키워드

        Returns:
            검색 성공 여부
        """
        try:
            # URL 접속
            self.logger.info(f"URL 접속 중: {url}")
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))

            # 로봇 감지 확인 및 처리
            if self.human_like.is_robot_page():
                self.logger.warning("초기 접속 시 로봇 감지 발생!")

                # 세션 재시작 전략 적용
                if self.restart_session():
                    # 재시작 후 다시 URL 접속
                    self.driver.get(url)
                    time.sleep(random.uniform(3, 5))

                    # 여전히 로봇 감지 상태라면
                    if self.human_like.is_robot_page():
                        self.logger.error(
                            "세션 재시작 후에도 로봇 감지 발생. 검색 중단."
                        )
                        return False
                else:
                    # 세션 재시작 실패 시 기본 처리 시도
                    if not self.human_like.handle_robot_detection():
                        self.logger.error("로봇 감지 처리 실패. 검색 중단.")
                        return False

                    self.driver.get(url)
                    time.sleep(random.uniform(3, 5))

                    if self.human_like.is_robot_page():
                        self.logger.error("반복적인 로봇 감지 발생. 검색 중단.")
                        return False

            # 검색창 찾기 및 검색어 입력
            try:
                # 검색창을 찾기 위한 CSS 선택자 목록
                search_selectors = [
                    "input[name='q']",
                    "input[type='search']",
                    ".gLFyf",
                    "textarea[name='q']",  # 특정 사이트의 textarea 검색창
                    "input.search",
                    ".search-box",
                    ".searchbox",
                    "header input[type='text']",  # Google News 헤더의 검색창
                    ".Ax4B8.ZAGvjd",  # Google News 특정 클래스
                    "[aria-label='Search']",  # aria-label로 검색창 찾기
                    ".gb_2e",  # Google News 네비게이션 바 검색
                    ".YacQv",  # Google News 모바일 검색창
                ]

                search_element = None
                for selector in search_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                search_element = element
                                break
                        if search_element:
                            break
                    except Exception as e:
                        self.logger.warning(
                            f"'{selector}' 검색창 찾기 중 오류 (무시됨): {e}"
                        )
                        continue

                if not search_element:
                    self.logger.error("검색창 찾기 실패")
                    return False

                # 검색창 클리어 및 클릭
                search_element.clear()
                search_element.click()
                time.sleep(0.5)  # 검색창 클릭 후 대기

                # 검색어 입력
                for char in keyword:
                    search_element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))  # 검색어 입력 속도 제어

                # 검색어 입력 완료 후 대기
                time.sleep(random.uniform(0.5, 1.0))  # 검색어 입력 완료 후 대기

                # 엔터키 입력
                search_element.send_keys(Keys.RETURN)

                # 검색 결과 로딩 대기
                time.sleep(random.uniform(2.0, 3.0))  # 검색 결과 로딩 대기

                # 로봇 감지 확인
                if self.human_like.is_robot_page():
                    self.logger.warning("검색 결과 로딩 후 로봇 감지 발생!")
                    # 세션 재시작 전략 적용
                    if self.restart_session():
                        return self.search_with_anti_robot(
                            url, keyword
                        )  # 재시작 후 재검색
                    return False

                self.logger.info(f"'{keyword}' 검색 성공")
                return True

            except Exception as e:
                self.logger.error(f"검색 중 오류: {e}")
                return False

            # 자연스러운 스크롤 동작
            # self.human_like.natural_scroll_and_read()

            return True

        except Exception as e:
            self.logger.error(f"검색 중 오류: {e}")
            return False

    def news_search_with_anti_robot(self, keyword: str) -> bool:
        """
        뉴스 검색 페이지에서 로봇 감지 우회

        Args:
            keyword: 검색할 키워드

        Returns:
            검색 성공 여부
        """
        # 구글 뉴스 검색 URL 사용 (news.google.com이 아닌 google.com의 뉴스 탭을 사용)
        news_url = f"https://www.google.com/search?q={keyword}&tbm=nws&gl=ko&hl=kr"

        try:
            self.logger.info(f"구글 뉴스 URL 접속 중: {news_url}")
            self.driver.get(news_url)
            time.sleep(random.uniform(3, 5))

            # 로봇 감지 확인
            if self.human_like.is_robot_page():
                self.logger.warning("구글 뉴스 접속 시 로봇 감지 발생!")
                if not self.restart_session():
                    self.logger.error("세션 재시작 실패")
                    return False

                # 다시 URL 접속 시도
                self.driver.get(news_url)
                time.sleep(random.uniform(3, 5))

                if self.human_like.is_robot_page():
                    self.logger.error("세션 재시작 후에도 로봇 감지 발생")
                    return False

            # 페이지가 완전히 로드될 때까지 대기
            time.sleep(random.uniform(1, 2))

            # 이미 검색 결과 페이지에 있으므로 추가 검색 필요 없음
            self.logger.info(f"'{keyword}' 뉴스 검색 페이지 접속 성공")
            return True

        except Exception as e:
            self.logger.error(f"뉴스 검색 중 오류: {e}")
            return False
