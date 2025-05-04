import time
import logging
import random
from typing import Any

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains

from common.types import UrlDictCollect
from common.utils.logging_utils import EnhancedLogger
from config.setting import chrome_option_setting, prefs
from crawling.src.utils.search_util import (
    PageScroller,
    web_element_clicker,
    ChromeDriver,
)
from crawling.src.driver.news_parsing import (
    InvestingNewsDataSeleniumCrawling,
    InvestingNewsDataTargetSeleniumCrawling as InvestingTargetNews,
)


# Investing 관련 상수
INVESTING_URL = "https://www.investing.com/"
INVESTING_NEWS_BUTTON = "//li[@class='nav_news']"
INVESTING_CATEGORY = (
    "//div[contains(@class, 'sidebar')]/ul[@class='categoryList newsCat']"
)
INVESTING_NEWS_NEXT = "//div[contains(@class, 'pagination')]"


class InvestingSeleniumMovingElementLocation(InvestingNewsDataSeleniumCrawling):
    def __init__(self, target: str, count: int) -> None:
        """인베스팅 생성자

        Args:
            count (int): 얼마나 긁을것인지
        """
        self.url = "https://kr.investing.com"
        self.count = count
        self.target = target
        self.driver: ChromeDriver = chrome_option_setting(prefs)
        self.log = EnhancedLogger(
            "investing", "selenium_investing_news.log"
        ).log_message_sync
        self.log(logging.INFO, f"종합 뉴스 시작합니다")

    def wait_and_click(self, driver: ChromeDriver, xpath: str) -> Any | str:
        """웹 클릭 하는 함수"""
        # Any --> WebElement
        try:
            element = web_element_clicker(driver, xpath=xpath)
            return element, element.text
        except (ElementClickInterceptedException, TimeoutException) as error:
            self.log(logging.ERROR, f"접근할 수 없습니다 --> {error} 조정합니다")
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
                self.log(logging.ERROR, f"접근할 수 없습니다 --> {error} 기다립니다")
                return False

    def scroll_through_pages(self, x_path: str) -> dict[str, UrlDictCollect]:
        """클릭하고 페이지 이동할 때 쓰는 함수"""
        self.driver.set_page_load_timeout(20.0)

        # 뉴스 버튼 클릭
        news_button = self.wait_and_click(self.driver, INVESTING_NEWS_BUTTON)
        ActionChains(self.driver).move_to_element(news_button[0]).click().perform()

        # 카테고리 클릭
        category = self.wait_and_click(self.driver, x_path)
        ActionChains(self.driver).move_to_element(category[0]).click().perform()

        self.log(logging.INFO, f"{category[1]} 부분 -- {self.count} 페이지 수집합니다")

        page_data = {}
        for i in range(1, self.count + 1):
            next_page = f"{INVESTING_NEWS_NEXT}/a[{i}]"
            element = self.wait_and_click(self.driver, next_page)

            self.log(logging.INFO, f"{category[1]} 부분 -- {i} 페이지 이동합니다")
            ActionChains(self.driver).move_to_element(element[0]).click().perform()

            PageScroller(self.driver).page_scroll()
            time.sleep(random.uniform(1, 2))

            page: str = self.driver.page_source
            data = len(self.extract_news_urls(page))
            page_data[category[1]] = self.extract_news_urls(page)
            self.log(logging.INFO, f"{category[1]} 뉴스 -- {data}개 수집")

        return page_data

    def investing_news_selenium_start(self) -> None:
        """카테고리 별 뉴스 크롤링 시작"""
        self.driver.get(self.url)
        for i in range(4, 14):
            if i == 7 or i == 10 or i == 11:
                continue
            news_xpath = f"{INVESTING_CATEGORY}/li[{i}]"
            self.scroll_through_pages(x_path=news_xpath)
        self.driver.quit()


class InvestingTargetSeleniumMovingElementLocation(InvestingTargetNews):
    def __init__(self, target: str, count: int) -> None:
        """

        Args:
            target (str): 어떤걸 긁을것인지
            count (int): 얼마나 긁을것인지
        """
        self.url = f"https://kr.investing.com/search/?q={target}&tab=news"
        self.count = count
        self.target = target
        self.driver: ChromeDriver = chrome_option_setting()
        self.logging = EnhancedLogger(
            "investing", f"selenium_coin_{target}_news.log"
        ).log_message_sync

        self.logging(
            logging.INFO,
            f"""{target} 뉴스 시작합니다 -- {target}뉴스 당 [{count}번 스크롤] 수집합니다""",
        )

    def investing_target_news_selenium_start(self) -> None:
        """긁을 타겟"""
        self.driver.get(self.url)

        # page 스크롤
        PageScroller(driver=self.driver, second_delay=True).page_scroll()

        data: str = self.driver.page_source
        page_data: UrlDictCollect = self.extract_news_urls(html=data)
        self.logging(logging.INFO, f"{self.target} 뉴스 -- {len(page_data)}개 수집")

        self.driver.quit()
