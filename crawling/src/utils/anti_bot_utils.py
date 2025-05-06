import time
import random
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
    StaleElementReferenceException,
)
from common.utils.error_handling import SeleniumExceptionType
from config.setting import chrome_option_setting

from crawling.src.core.types import ChromeDriver
from crawling.src.utils.search_util import PageScroller


class HumanLikeInteraction:
    """사람과 유사한 브라우저 상호작용을 시뮬레이션하는 클래스"""

    def __init__(self, driver: ChromeDriver) -> None:
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.page_scroller = PageScroller(driver)
        # 요청 카운터 초기화
        self.request_count = 0

    def is_robot_page(self) -> bool:
        """로봇 감지 페이지인지 확인"""
        # 1. HTML 소스 코드 분석 (페이지 텍스트보다 더 빠르고 정확하게 캡차 감지 가능)
        try:
            page_source = self.driver.page_source.lower()
            robot_source_indicators = [
                "recaptcha",
                "captcha",
                "challenge",
                "g-recaptcha",
                "security check",
                "unusual traffic",
                "비정상적인 트래픽",
                "robotcheck",
                "bot detection",
                "automated query",
                "자동화된",
                "suspicious activity",
            ]

            if any(indicator in page_source for indicator in robot_source_indicators):
                self.logger.warning("HTML 소스에서 캡차/로봇 감지 발견!")
                return True

            # 2. 특정 캡차 요소 직접 확인
            captcha_selectors = [
                "#captcha",
                "#recaptcha",
                ".g-recaptcha",
                "iframe[title*='recaptcha']",
                "iframe[src*='recaptcha']",
                "form[action*='challenge']",
                "#robot",
            ]

            for selector in captcha_selectors:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    self.logger.warning(f"캡차 요소 발견: {selector}")
                    return True

            # 3. 페이지 텍스트 확인 (일반적인 방법)
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            robot_indicators = [
                "robot",
                "captcha",
                "automated",
                "unusual traffic",
                "비정상적인 트래픽",
                "suspicious activity",
                "보안 확인",
                "security check",
                "인증",
                "확인해 주세요",
                "자동화된",
            ]

            return any(indicator in page_text for indicator in robot_indicators)

        except SeleniumExceptionType as e:
            self.logger.warning(f"드라이버 오류로 로봇 페이지 확인 실패: {e}")
            return False

    def handle_robot_detection(self) -> bool:
        """로봇 감지 시 대응 전략 실행"""
        if self.is_robot_page():
            self.logger.warning("로봇 감지 페이지 발견! 대응 전략 실행...")

            # 1. 잠시 대기 (봇 탐지 시스템 회피)
            delay = random.uniform(20, 40)
            self.logger.info(f"{delay:.1f}초 동안 대기합니다...")
            time.sleep(delay)

            # 2. 브라우저 쿠키 초기화
            self.driver.delete_all_cookies()
            self.logger.info("브라우저 쿠키 초기화 완료")

            # 3. 자바스크립트 실행으로 webdriver 속성 숨기기
            self.mask_navigator()

            return True
        return False

    def mask_navigator(self):
        """자바스크립트를 사용하여 Navigator 속성 마스킹 (봇 감지 방지)"""
        # Navigator 객체 속성 마스킹을 통한 자동화 탐지 회피
        script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        """
        try:
            self.driver.execute_script(script)
            self.logger.info("Navigator 속성 마스킹 완료")
        except SeleniumExceptionType as e:
            self.logger.error(f"Navigator 마스킹 실패: {e}")

    def smart_delay(self) -> float:
        """요청 수에 따라 지능적으로 지연 시간 결정"""
        self.request_count += 1

        # 요청이 많을수록 더 긴 지연 적용
        if self.request_count < 5:
            delay = random.uniform(1, 3)  # 초기 몇 개 요청은 짧은 지연
        elif self.request_count < 15:
            delay = random.uniform(5, 15)  # 중간 요청은 중간 지연
        else:
            delay = random.uniform(15, 30)  # 많은 요청 후에는 긴 지연

        self.logger.info(f"요청 #{self.request_count} - {delay:.1f}초 지연 적용")
        time.sleep(delay)
        return delay

    def natural_scroll_and_read(self) -> None:
        """페이지 콘텐츠를 분석하고 사람처럼 읽는 행동 시뮬레이션"""
        # 기본 스크롤링 수행
        self.page_scroller.page_scroll()

        # 추가로 중요한 콘텐츠에 집중하는 행동 시뮬레이션
        self.focus_on_content()

    def focus_on_content(self) -> None:
        """콘텐츠에 집중하는 행동 시뮬레이션"""
        # 주요 콘텐츠 요소 찾기 시도
        content_selectors = [
            "article",
            "p",
            ".news-content",
            ".article-body",
            "#content",
            ".content",
            "div[role='main']",
            ".main-content",
        ]

        for selector in content_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    selected = elements[: min(3, len(elements))]  # 최대 3개 요소만 선택
                    for element in selected:
                        if element.is_displayed():
                            # 요소로 스크롤
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                element,
                            )

                            # 요소 위로 마우스 이동
                            ActionChains(self.driver).move_to_element(element).perform()

                            # 텍스트 길이에 비례한 시간 동안 '읽기' 시뮬레이션
                            text_length = len(element.text)
                            if text_length > 0:
                                read_time = min(
                                    text_length / 50, 10
                                )  # 50자당 1초, 최대 10초
                                self.logger.info(
                                    f"{text_length}자 분량의 텍스트를 {read_time:.1f}초 동안 읽는 중..."
                                )
                                time.sleep(read_time)
                    break  # 적절한 콘텐츠를 찾았으면 반복 중단
            except (StaleElementReferenceException, ElementNotVisibleException):
                # 요소 상태가 변경되었거나 보이지 않는 경우 다음 셀렉터로 진행
                continue
            except SeleniumExceptionType as e:
                self.logger.warning(f"콘텐츠 요소 처리 중 오류: {e}")

    def human_like_search(self, keyword: str) -> None:
        """사람처럼 검색어 입력 및 검색 동작 시뮬레이션"""
        try:
            # 1. 검색창 찾기
            search_box = None
            search_selectors = [
                "input[name='q']",
                "input[type='search']",
                "#search",
                ".search",
                "input.gLFyf",
            ]

            for selector in search_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].is_displayed():
                    search_box = elements[0]
                    break

            if not search_box:
                raise NoSuchElementException("검색창을 찾을 수 없음")

            # 2. 검색창 클릭 및 포커스
            action = ActionChains(self.driver)
            action.move_to_element(search_box).click().perform()
            time.sleep(random.uniform(0.5, 1.0))

            # 3. 기존 검색어가 있으면 삭제
            current_value = search_box.get_attribute("value")
            if current_value:
                if len(current_value) > 10:
                    # 긴 텍스트의 경우 전체 선택 후 삭제
                    if self.driver.capabilities["platformName"].lower() == "mac":
                        action.key_down(Keys.COMMAND).send_keys("a").key_up(
                            Keys.COMMAND
                        ).perform()
                    else:
                        action.key_down(Keys.CONTROL).send_keys("a").key_up(
                            Keys.CONTROL
                        ).perform()
                    time.sleep(random.uniform(0.3, 0.5))
                    action.send_keys(Keys.DELETE).perform()
                else:
                    # 짧은 텍스트의 경우 백스페이스로 한글자씩 삭제
                    for _ in range(len(current_value)):
                        action.send_keys(Keys.BACK_SPACE).perform()
                        time.sleep(random.uniform(0.05, 0.1))
                time.sleep(random.uniform(0.5, 0.8))

            # 4. 검색어 입력 (사람처럼 천천히)
            for char in keyword:
                search_box.send_keys(char)
                # 타이핑 딜레이 (무작위화)
                time.sleep(random.uniform(0.05, 0.2))

            # 5. 잠시 대기 (검색어 입력 완료 후 생각하는 시간)
            time.sleep(random.uniform(0.8, 1.5))

            # 6. 검색 실행
            search_box.send_keys(Keys.RETURN)

            # 7. 브라우저가 결과를 로드할 때까지 대기 (사람처럼)
            loading_wait = random.uniform(2.0, 4.0)
            self.logger.info(f"검색 결과 로딩 중... ({loading_wait:.1f}초)")
            time.sleep(loading_wait)

        except SeleniumExceptionType as e:
            self.logger.error(f"검색 과정 중 오류 발생: {e}")

    def random_mouse_movements(self, count: int = 3) -> None:
        """화면 내에서 랜덤한 마우스 움직임 생성"""
        # 화면 크기 가져오기
        width = self.driver.execute_script(
            "return Math.min(window.innerWidth, 1000);"
        )  # 최대 1000px로 제한
        height = self.driver.execute_script(
            "return Math.min(window.innerHeight, 800);"
        )  # 최대 800px로 제한

        # 시작 위치 중앙으로 설정
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(
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
                        # 페이지에서 상호작용 가능한 요소 찾기
                        elements = (
                            self.driver.find_elements(By.TAG_NAME, "input")[:3]
                            + self.driver.find_elements(By.TAG_NAME, "a")[:5]
                            + self.driver.find_elements(By.TAG_NAME, "button")[:3]
                        )

                        if elements:
                            element = random.choice(elements)
                            ActionChains(self.driver).move_to_element(element).perform()
                            self.logger.info(
                                f"랜덤 요소로 마우스 이동 (#{successful_moves+1})"
                            )
                        else:
                            # 요소가 없으면 안전한 좌표 이동으로 대체
                            raise NoSuchElementException("상호작용 가능한 요소가 없음")
                    else:
                        # 2. 안전한 범위 내에서 상대적 이동
                        x_offset = random.randint(10, min(200, width // 2))
                        y_offset = random.randint(10, min(150, height // 2))

                        # 방향 랜덤화
                        if random.random() > 0.5:
                            x_offset *= -1
                        if random.random() > 0.5:
                            y_offset *= -1

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

                except (NoSuchElementException, StaleElementReferenceException):
                    # 요소가 없거나 상태가 변경된 경우 다음 시도로 계속
                    continue
                except SeleniumExceptionType as e:
                    self.logger.warning(f"마우스 이동 #{attempts} 실패: {e}")
                    # 오류 발생 시 초기 위치로 재설정 시도
                    try:
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

    def read_content_elements(self) -> None:
        """콘텐츠 요소를 읽는 행동 시뮬레이션"""
        # 주요 콘텐츠 요소 찾기 시도
        content_selectors = [
            "p",
            "article",
            ".content",
            "#content",
            ".post",
            ".article",
            ".news",
            "h1",
            "h2",
            "h3",
            ".headline",
            ".title",
        ]

        for selector in content_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    selected = elements[: min(3, len(elements))]  # 최대 3개 요소만 선택
                    for element in selected:
                        if element.is_displayed():
                            # 요소로 스크롤
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                element,
                            )
                            time.sleep(random.uniform(0.5, 1.0))

                            # 요소의 텍스트 길이에 비례한 시간 동안 '읽기' 시뮬레이션
                            text_length = len(element.text)
                            if text_length > 0:
                                read_time = min(
                                    text_length / 50, 10
                                )  # 50자당 1초, 최대 10초
                                self.logger.info(
                                    f"{text_length}자 분량의 텍스트를 {read_time:.1f}초 동안 읽는 중..."
                                )
                                time.sleep(read_time)
                            return  # 콘텐츠 요소를 찾았으면 반복 중단
            except SeleniumExceptionType as e:
                self.logger.warning(f"콘텐츠 요소 처리 중 오류: {e}")


class AntiRobotGoogleSearch:
    """구글 검색 시 로봇 감지를 우회하는 클래스"""

    def __init__(self, driver: ChromeDriver) -> None:
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.human_like = HumanLikeInteraction(driver)

    def restart_session(self, wait_time: int = 30) -> bool:
        """세션을 완전히 닫고 새로 시작하여 캡차 우회"""
        # 현재 드라이버 상태 백업
        prefs = self.driver.desired_capabilities.get("prefs", {})

        try:
            self.logger.warning("캡차 감지로 인해 세션 재시작 중...")

            # 드라이버 종료
            self.logger.info("브라우저 인스턴스 종료 중...")
            self.driver.quit()

            # 일정 시간 대기 (IP 추적 초기화 위해)
            restart_delay = random.randint(
                wait_time, wait_time + 15
            )  # 30~45초 랜덤 대기
            self.logger.info(f"새 세션 시작 전 {restart_delay}초 대기 중...")
            time.sleep(restart_delay)

            # 새 드라이버 생성 및 설정
            self.logger.info("새 브라우저 인스턴스 생성 중...")
            self.driver = chrome_option_setting(prefs)

            # HumanLikeInteraction 객체 재생성
            self.human_like = HumanLikeInteraction(self.driver)

            self.logger.info("세션 재시작 완료")
            return True

        except SeleniumExceptionType as e:
            self.logger.error(f"세션 재시작 중 오류: {e}")
            return False

    def search_with_anti_robot(self, url: str, keyword: str) -> bool:
        """로봇 감지를 피하며 검색 수행"""
        try:
            # 원하는 URL 접속
            self.logger.info(f"URL 접속 중: {url}")
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))

            # 로봇 감지 확인 및 처리
            if self.human_like.is_robot_page():
                self.logger.warning("초기 접속 시 로봇 감지 발생!")

                # 새로운 방식: 세션 재시작 전략 적용
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
                    # 기존 방식 (세션 재시작 실패 시)
                    if not self.human_like.handle_robot_detection():
                        self.logger.error("로봇 감지 처리 실패. 검색 중단.")
                        return False

                    self.driver.get(url)
                    time.sleep(random.uniform(3, 5))

                    if self.human_like.is_robot_page():
                        self.logger.error("반복적인 로봇 감지 발생. 검색 중단.")
                        return False

            # 키워드 검색 (사람처럼 입력)
            self.human_like.human_like_search(keyword)

            # 검색 후 캡차 확인
            if self.human_like.is_robot_page():
                self.logger.warning("검색 후 로봇 감지 발생!")

                # 검색 후 캡차 발생 시 세션 재시작
                if self.restart_session():
                    # 재시작 후 다시 시도
                    self.driver.get(url)
                    time.sleep(random.uniform(3, 5))
                    self.human_like.human_like_search(keyword)

                    if self.human_like.is_robot_page():
                        self.logger.error("반복적인 로봇 감지 발생. 검색 중단.")
                        return False
                else:
                    # 세션 재시작 실패 시
                    return False

            self.logger.info(f"'{keyword}' 검색 완료 (로봇 감지 우회)")
            return True

        except SeleniumExceptionType as e:
            self.logger.error(f"검색 과정 중 오류: {e}")
            return False

    def news_search_with_anti_robot(self, keyword: str) -> bool:
        """뉴스 검색 페이지에서 로봇 감지 우회"""
        # 구글 뉴스 검색 URL 형식 사용
        news_url = "https://news.google.com/"  # 또는 "https://www.google.com/search?tbm=nws&q=dummy"
        return self.search_with_anti_robot(news_url, keyword)
