import time
import random
import asyncio
from typing import Any, Callable

from config.setting import prefs
from crawling.src.core.types import UrlDictCollect
from crawling.src.driver.news_parsing import GoogleNewsDataSeleniumCrawling
from crawling.src.driver.api_req.api_news_driver import AsyncGoogleNewsParsingDriver
from crawling.src.utils.search_util import PageScroller, web_element_clicker
from crawling.src.utils.session_manager import SeleniumSessionManager
from crawling.src.utils.anti.human_like import HumanLikeInteraction, AntiRobotSearch
from common.utils.error_handling import SeleniumExceptionType


class GoogleSeleniumMovingElementLocation(
    GoogleNewsDataSeleniumCrawling, SeleniumSessionManager
):
    """구글 크롤링 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """데이터를 크롤링할 타겟 선정"""
        # SeleniumSessionManager 초기화
        SeleniumSessionManager.__init__(self, "google.com", target, count)
        # GoogleNewsDataSeleniumCrawling 초기화 - 상속 순서에 따라 부모 클래스의 __init__이 호출되지 않으므로 명시적 호출
        GoogleNewsDataSeleniumCrawling.__init__(self)

        self.target = target
        self.count = count
        self.url = f"https://www.google.com/search?q={target}&tbm=nws&gl=ko&hl=kr"

        # 드라이버 초기화: 세션 사용 설정 (단, 최초 로드만 시도하고 재시도 없음)
        self.driver = self._init_driver_without_retry(custom_prefs=prefs)

        # 안티봇 기능을 통해 로봇 감지 우회 시도
        try:
            self.logger.info("안티봇 기능을 사용하여 드라이버 초기화 중...")
            self.anti_bot = AntiRobotSearch(self.driver)
            self.human_like = HumanLikeInteraction(
                self.driver
            )  # HumanLikeInteraction 직접 사용

            # 구글 뉴스 검색 결과 페이지로 이동하고 로봇 감지 우회 시도
            search_success = self.anti_bot.search_with_anti_robot(self.url, self.target)

            # 성공적으로 로봇 감지를 우회하고 검색에 성공한 경우에만 세션 저장
            if search_success:
                self.logger.info("로봇 감지 우회 성공! 유효한 세션 저장")
                self.save_cookies()
            else:
                self.logger.warning("로봇 감지 우회 실패. 세션 저장하지 않음")

        except SeleniumExceptionType as e:
            self.logger.error(f"안티봇 기능 초기화 중 오류: {e}")
            # 오류 발생 시 기본 URL 접속 시도
            try:
                self.driver.get(self.url)
                time.sleep(random.uniform(2, 4))
            except Exception as e2:
                self.logger.error(f"URL 접속 시도 중 추가 오류: {e2}")

    def _init_driver_without_retry(self, custom_prefs=None):
        """재시도 없이 드라이버 초기화

        세션 재시도를 하지 않고 Redis에 저장된 세션이 있으면 로드하고, 없으면 새로 시작합니다.

        Args:
            custom_prefs: 사용자 정의 브라우저 설정

        Returns:
            초기화된 셀레니움 드라이버
        """
        # 사용자 정의된 크롬 환경 설정을 사용
        chrome_prefs = custom_prefs if custom_prefs is not None else prefs
        from config.setting import chrome_option_setting

        self.driver = chrome_option_setting(chrome_prefs)

        # Redis에서 저장된 세션 확인 및 로드 시도 (단 1회만)
        try:
            self.logger.info(f"{self.domain} 도메인에 대한 저장된 세션 확인")
            # 쿠키 로드 시도
            cookies = self.session_manager.load_cookies(self.domain).get("cookies", [])

            if cookies:
                self.logger.info(
                    f"{self.domain} 도메인에 대한 저장된 세션 발견. 적용 시도"
                )
                # 먼저 도메인에 접속
                self.driver.get(f"https://{self.domain}")
                self.driver.implicitly_wait(5)

                # 쿠키 적용
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        self.logger.warning(f"쿠키 적용 중 오류: {e}")

                # 캡차 확인
                from crawling.src.utils.anti.detector import RobotDetector

                detector = RobotDetector(self.driver)
                if detector.is_robot_page():
                    self.logger.warning(
                        "저장된 세션에서 캡차 감지. 세션 삭제 후 새로 시작"
                    )
                    self.session_manager.clear_cookies(self.domain)
                    # 브라우저 재시작
                    self.driver.quit()
                    self.driver = chrome_option_setting(chrome_prefs)
                else:
                    self.logger.info(f"{self.domain} 세션 적용 성공")
            else:
                self.logger.info(
                    f"{self.domain} 도메인에 대한 저장된 세션 없음. 새로 시작"
                )

        except Exception as e:
            self.logger.warning(f"{self.domain} 세션 로드 실패: {e}. 세션 없이 진행")

        return self.driver

    def scroll_through_pages(
        self, start: int, xpath: Callable[[int], str]
    ) -> dict[str, UrlDictCollect]:
        """뉴스 기사 크롤링 실행

        Args:
            start: 시작 페이지 번호
            xpath: 페이지 번호에 해당하는 XPath

        Returns:
            페이지 번호를 키로 하는 뉴스 기사 URL 딕셔너리
        """
        page_dict: dict[str, UrlDictCollect] = {}

        for i in range(start, self.count + start):
            # 안티봇 기능으로 검색 실행
            self.human_like.delay.smart_delay()

            # 다음 페이지 버튼 클릭
            next_page_button: Any = web_element_clicker(self.driver, xpath(i))
            message = f"{i-2}페이지 --> {xpath(i)} 클릭 성공"
            self.logger.info(message)

            # 안티봇 기능으로 마우스 클릭
            self.human_like.mouse.move_to_element_and_click(next_page_button)

            # 뉴스 기사 URL 추출
            data = self.extract_news_urls(self.driver.page_source)
            page_dict[str(i - 2)] = data

            # 안티봇 기능으로 스크롤
            self.human_like.delay.natural_scroll()

            # 페이지 스크롤
            PageScroller(self.driver).page_scroll()

        self.logger.info(f"뉴스 기사 크롤링 완료")
        # 드라이버 종료
        self.close_driver()

        return page_dict

    # fmt: off
    def google_seleium_start(self) -> dict[str, UrlDictCollect] | UrlDictCollect:
        """구글 셀레니움 크롤링 시작"""

        def mo_xpath_injection(start: int) -> str:
            """모바일용 XPath"""
            return f'//*[@id="wepR4d"]/div/span/a[{start-1}]'
        

        def pa_xpath_injection(start: int) -> str:
            """PC용 XPath"""
            return f'//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[{start}]/a'

        try:
            # 안티봇 기능으로 검색 실행
            self.logger.info(f"안티봇 기능을 사용하여 '{self.target}' 뉴스 검색 시도 중...")
            
            # 검색 성공 여부 확인
            if self.anti_bot.news_search_with_anti_robot(self.target):
                self.logger.info("뉴스 검색 성공, 크롤링 시작")
                # 크롤링 시작
                try:
                    # PC용 크롤링
                    return self.scroll_through_pages(3, pa_xpath_injection)
                except SeleniumExceptionType:
                    # 모바일용 크롤링
                    return self.scroll_through_pages(2, mo_xpath_injection)
            else:
                # 검색 실패 시 API 사용
                self.logger.warning("뉴스 검색 실패, API 사용")
                self.close_driver()
                rest = AsyncGoogleNewsParsingDriver(self.target, self.count)
                return asyncio.run(rest.news_collector())
                
        except SeleniumExceptionType as e:
            # 오류 발생 시 기본 URL 접속 시도
            self.logger.error(f"셀레니움 오류: {e}, 기본 URL 접속 시도")
            
            # 기본 URL 접속
            self.driver.get(self.url)
            try:
                # 크롤링 시작
                return self.scroll_through_pages(3, pa_xpath_injection)
            except SeleniumExceptionType:
                # 모바일용 크롤링
                return self.scroll_through_pages(2, mo_xpath_injection)
            except SeleniumExceptionType as e:
                message = (
                    f"드라이버 오류 --> {e}"
                )
                self.logger.error(message)
                self.close_driver()
                time.sleep(3)
                rest = AsyncGoogleNewsParsingDriver(self.target, self.count)
                return asyncio.run(rest.news_collector())
                
    async def start_crawling(self) -> list[dict]:
        """비동기 크롤링 시작"""
        self.logger.info(f"'{self.target}' 검색어에 대한 크롤링 시작")
        results = []
        
        try:
            # 크롤링 시작
            data = self.google_seleium_start()
            
            # 데이터 처리
            if isinstance(data, dict):
                # 데이터 처리
                self.logger.info(f"{len(data)}페이지 뉴스 기사 크롤링 완료")
                processed_data = []
                for page_num, page_data in data.items():
                    processed_data.extend(page_data)
                data = processed_data
            
            if not data:
                self.logger.warning("크롤링 데이터가 없습니다.")
                return results
                
            # 비동기 API 호출을 통한 뉴스 파싱
            if isinstance(data, list):
                async_driver = AsyncGoogleNewsParsingDriver()
                self.logger.info(f"{len(data)}개 URL에 대한 비동기 파싱 시작")
                results = await async_driver.parsing_all(data)
                self.logger.info(f"{len(results)}개 뉴스 기사 파싱 완료")
            else:
                self.logger.error(f"예상치 못한 데이터 형식: {type(data)}")
            
        except Exception as e:
            self.logger.error(f"크롤링 과정 중 예상치 못한 오류: {e}")
        finally:
            # 자원 정리
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.quit()
                    self.logger.info("드라이버 종료 완료")
            except Exception as e:
                self.logger.error(f"드라이버 종료 중 오류: {e}")
            
        return results
