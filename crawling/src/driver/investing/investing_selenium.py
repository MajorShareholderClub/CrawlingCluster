import time
import logging
import random
from typing import Any, Dict

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains

from common.types import UrlDictCollect
from config.setting import prefs
from crawling.src.utils.search_util import (
    PageScroller,
    web_element_clicker,
    ChromeDriver,
)
from crawling.src.driver.news_parsing import (
    InvestingNewsDataSeleniumCrawling,
    InvestingNewsDataTargetSeleniumCrawling as InvestingTargetNews,
)
from crawling.src.utils.session_manager import SeleniumSessionManager
from crawling.src.utils.anti.human_like import AntiRobotSearch, HumanLikeInteraction
from common.utils.error_handling import SeleniumExceptionType

# Investing 관련 상수
INVESTING_URL = "https://www.investing.com/"
INVESTING_NEWS_BUTTON = "//li[@class='nav_news']"
INVESTING_CATEGORY = (
    "//div[contains(@class, 'sidebar')]/ul[@class='categoryList newsCat']"
)
INVESTING_NEWS_NEXT = "//div[contains(@class, 'pagination')]"


class InvestingSeleniumMovingElementLocation(
    InvestingNewsDataSeleniumCrawling, SeleniumSessionManager
):
    """인베스팅 크롤링 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """인베스팅 생성자

        Args:
            target: 키워드 검색 또는 뉴스
            count: 스크롤 회수
        """
        # SeleniumSessionManager 초기화
        SeleniumSessionManager.__init__(self, "investing.com", target, count)
        # InvestingNewsDataSeleniumCrawling 초기화 - 상속 순서에 따라 부모 클래스의 __init__이 호출되지 않으므로 명시적 호출
        InvestingNewsDataSeleniumCrawling.__init__(self)

        self.target = target
        self.count = count
        self.url = f"https://kr.investing.com/search/?q={target}&tab=news"

        # 세션 관리 드라이버 초기화
        self.driver = self.init_driver(custom_prefs=prefs, use_session=True)
        self.logger.info(f"종합 뉴스 시작합니다")

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

    def wait_and_click(self, driver: ChromeDriver, xpath: str) -> Any | str:
        """웹 클릭 하는 함수"""
        # Any --> WebElement
        try:
            element = web_element_clicker(driver, xpath=xpath)
            return element, element.text
        except (ElementClickInterceptedException, TimeoutException) as error:
            self.logger.error(f"접근할 수 없습니다 --> {error} 조정합니다")
            time.sleep(3)

            # 다시 요소를 클릭 가능하게 기다림
            try:
                element = web_element_clicker(driver, xpath=xpath)

                # 스크롤을 조정하고 다시 클릭 시도
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                driver.execute_script("window.scrollBy(0, -500);")
                return element
            except TimeoutException:
                time.sleep(3)
                self.logger.error(f"접근할 수 없습니다 --> {error} 기다립니다")
                return False

    def scroll_through_pages(self, x_path: str) -> Dict[str, UrlDictCollect]:
        """클릭하고 페이지 이동할 때 쓰는 함수"""
        self.driver.set_page_load_timeout(20.0)

        # 뉴스 버튼 클릭
        news_button = self.wait_and_click(self.driver, INVESTING_NEWS_BUTTON)
        ActionChains(self.driver).move_to_element(news_button[0]).click().perform()

        # 카테고리 클릭
        category = self.wait_and_click(self.driver, x_path)
        ActionChains(self.driver).move_to_element(category[0]).click().perform()

        self.logger.info(f"{category[1]} 부분 -- {self.count} 페이지 수집합니다")

        page_data = {}
        for i in range(1, self.count + 1):
            next_page = f"{INVESTING_NEWS_NEXT}/a[{i}]"
            element = self.wait_and_click(self.driver, next_page)

            self.logger.info(f"{category[1]} 부분 -- {i} 페이지 이동합니다")
            ActionChains(self.driver).move_to_element(element[0]).click().perform()

            PageScroller(self.driver).page_scroll()
            time.sleep(random.uniform(1, 2))

            page: str = self.driver.page_source
            data = len(self.extract_news_urls(page))
            page_data[category[1]] = self.extract_news_urls(page)
            self.logger.info(f"{category[1]} 뉴스 -- {data}개 수집")

        return page_data

    def investing_news_selenium_start(self) -> None:
        """카테고리 별 뉴스 크롤링 시작"""
        self.driver.get(self.url)
        for i in range(4, 14):
            if i == 7 or i == 10 or i == 11:
                continue
            news_xpath = f"{INVESTING_CATEGORY}/li[{i}]"
            self.scroll_through_pages(x_path=news_xpath)

        # 세션 저장 및 드라이버 종료
        self.close_driver()


class InvestingTargetSeleniumMovingElementLocation(
    InvestingTargetNews, SeleniumSessionManager
):
    """인베스팅 크롤링 타겟 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """

        Args:
            target: 전송 필드가 필드 페이지 타겟
            count: 스크롤 몇번 돌릴지 필드
        """
        # SeleniumSessionManager 초기화
        SeleniumSessionManager.__init__(self, "investing.com", target, count)
        # InvestingTargetNews 초기화 - 상속 순서에 따라 부모 클래스의 __init__이 호출되지 않으므로 명시적 호출
        InvestingTargetNews.__init__(self)

        self.target = target
        self.count = count
        self.url = f"https://kr.investing.com/equities/{target}"

        # 세션 관리 드라이버 초기화
        self.driver = self.init_driver(custom_prefs=prefs, use_session=True)

        self.logger.info(
            f"{target} 뉴스 시작합니다 -- {target}뉴스 당 [{count}번 스크롤] 수집합니다"
        )

    def investing_target_news_selenium_start(self) -> None:
        """uae08uc744 ud0c0uac9f"""
        self.driver.get(self.url)

        # page uc2a4ud06cub864
        PageScroller(driver=self.driver, second_delay=True).page_scroll()

        data: str = self.driver.page_source
        page_data: UrlDictCollect = self.extract_news_urls(html=data)
        self.logger.info(
            f"{self.target} ub274uc2a4 -- {len(page_data)}uac1c uc218uc9d1"
        )

        # uc138uc158 uc800uc7a5 ubc0f ub4dcub77cuc774ubc84 uc885ub8cc
        self.close_driver()
