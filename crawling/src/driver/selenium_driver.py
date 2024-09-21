import time
import random
import logging
from typing import Any, Callable
from src.core.types import ChromeDriver
from collections import deque

from config.selenium_setting import (
    chrome_option_setting,
    WITH_TIME,
    SCORLL_ITERATION,
    PAGE_LOAD_DELEY,
)

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from src.utils.logger import AsyncLogger
from src.core.types import UrlDictCollect
from src.parsing.news_parsing import (
    GoogleNewsDataCrawling,
    BingNewsDataCrawling,
    DaumNewsDataCrawling,
)

logging.basicConfig(level=logging.ERROR)


def page_scroll(driver: ChromeDriver, *scoll: tuple[int]) -> None:
    """스크롤 계산 5번 걸처서 내리기"""

    def scroll_page(scroll_cal: int, scoll: int, with_delay: bool) -> None:
        for i in range(int(scoll)):
            driver.execute_script(f"window.scrollTo(0, {i * scroll_cal})")
            if with_delay:
                time.sleep(1)

    prev_height = driver.execute_script("return document.body.scrollHeight")
    random_seleted_scroll: tuple[int] = random.choice(scoll)
    scroll_cal: float = prev_height / random_seleted_scroll

    # 랜덤으로 with_delay 값을 결정
    with_delay = random.choice([False, False])

    scroll_page(scroll_cal, random_seleted_scroll, with_delay)


class GoogleSeleniumMovingElementLocation(GoogleNewsDataCrawling):
    """구글 크롤링 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """데이터를 크롤링할 타겟 선정"""
        self.target = target
        self.count = count
        self.url = f"https://www.google.com/search?q={target}&tbm=nws&gl=ko&hl=kr"
        self.driver: ChromeDriver = chrome_option_setting()
        self.logging = AsyncLogger("google", "selenium_google.log").log_message_sync

    def finding_xpath(self, xpath: str) -> Any:
        """finding xpath location"""
        news_box: Any = WebDriverWait(self.driver, WITH_TIME).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return news_box

    def scroll_through_pages(
        self, start: int, xpath: Callable[[int], str]
    ) -> deque[UrlDictCollect]:
        """페이지 이동"""
        data = deque()

        for i in range(start, self.count + start):
            next_page_button: Any = self.finding_xpath(xpath(i))
            self.logging(
                logging.INFO, f"{i}page로 이동합니다 --> {xpath(i)} 이용합니다"
            )
            p: UrlDictCollect = self.news_info_collect(html=self.driver.page_source)
            next_page_button.click()
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
            page_scroll(self.driver, 2, 3, 4, SCORLL_ITERATION)
            data.append(p)
        else:
            self.logging(logging.INFO, f"google 수집 종료")
            self.driver.quit()
        return data

    def begin_page_navigation(self) -> UrlDictCollect:
        """페이지 수집 이동 본체"""

        def mo_xpath_injection(start: int) -> str:
            """google mobile xpath 경로 start는 a tag 기점 a -> a[2]"""
            if start == 2:
                return f'//*[@id="wepR4d"]/div/span/a'
            return f'//*[@id="wepR4d"]/div/span/a[{start-1}]'

        def pa_xpath_injection(start: int) -> str:
            """google site xpath 경로 start는 tr/td[3](page 2) ~ 기점"""
            if start == 1 or 2:
                return '//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[2]'
            return f'//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[{start}]/a'

        self.driver.get(self.url)
        try:
            return self.scroll_through_pages(1, pa_xpath_injection)
        except NoSuchElementException:
            return self.scroll_through_pages(2, mo_xpath_injection)
        except WebDriverException as e:
            self.logging(logging.ERROR, f"다음과 같은 이유로 google 수집 종료 --> {e}")
            self.driver.refresh()
        finally:
            self.driver.quit()


class BingSeleniumMovingElementLocation(BingNewsDataCrawling):
    """빙 크롤링 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """
        Args:
            target (str): 검색 타겟
            count (int): 얼마나 수집할껀지
        """
        self.url = f"https://www.bing.com/news/search?q={target}"
        self.count = count
        self.driver: ChromeDriver = chrome_option_setting()
        self.logging = AsyncLogger("bing", "selenium_bing.log").log_message_sync

    def repeat_scroll(self) -> UrlDictCollect:
        """Bing은 무한 스크롤이기에 횟수만큼 페이지를 내리도록 하였음"""
        data = deque()
        self.driver.get(self.url)

        # 스크롤 내리기 전 위치
        self.driver.execute_script("return document.body.scrollHeight")
        try:
            i = 0
            while i < self.count:
                # 현재 스크롤의 가장 아래로 내림
                self.driver.execute_script(
                    "window.scrollTo(0,document.body.scrollHeight)"
                )

                # 전체 스크롤이 늘어날 때까지 대기
                self.driver.implicitly_wait(random.uniform(5.0, 10.0))

                # 늘어난 스크롤 높이
                self.driver.execute_script("return document.body.scrollHeight")
                i += 1

                # page url
                url_element: list[str] = self.news_info_collect(self.driver.page_source)
                data.append(url_element)

                self.driver.execute_script("return document.body.scrollHeight")
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
        finally:
            self.logging(logging.INFO, "Bing 수집 종료")
            self.driver.quit()
        return data


class DaumSeleniumMovingElementsLocation(DaumNewsDataCrawling):
    def __init__(self, target: str, count: int) -> None:
        """
        Args:
            target (str): 검색 타겟
            count (int): 얼마나 수집할껀지
        """
        self.url = f"https://search.daum.net/search?w=news&nil_search=btn&DA=NTB&enc=utf8&cluster=y&cluster_page=1&q={target}"
        self.driver: ChromeDriver = chrome_option_setting()
        self.count = count if count - 3 <= 0 else count - 3
        self.logging = AsyncLogger(
            target="Daum", log_file="Daum_selenium.log"
        ).log_message_sync
        # self.count = count - 3

    def next_page_moving(self, xpath: str) -> Any:
        news_box_type: Any = WebDriverWait(self.driver, WITH_TIME).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return news_box_type

    def page_injection(self) -> deque[UrlDictCollect]:
        """
        //*[@id="dnsColl"]/div[2]/div/div/a[1] 2
        //*[@id="dnsColl"]/div[2]/div/div/a[2] 3
        //*[@id="dnsColl"]/div[2]/div/div/a[3] 4
        //*[@id="dnsColl"]/div[2]/div/div/a[4] 5
        """
        self.driver.get(self.url)
        data = deque()
        self.logging(logging.INFO, "다음 크롤링 시작합니다")
        if self.count <= 4:
            for i in range(1, self.count + 1):
                page_scroll(self.driver, int(random.uniform(10000, 10000)))
                self.driver.implicitly_wait(random.uniform(5.0, 10.0))
                time.sleep(1)
                next_page_button = self.next_page_moving(
                    f'//*[@id="dnsColl"]/div[2]/div/div/a[{i}]'
                )
                data.append(next_page_button)
                self.news_info_collect(self.driver.page_source)
                next_page_button.click()

        while self.count:
            page_scroll(self.driver, int(random.uniform(10000, 10000)))
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
            time.sleep(1)
            next_page_button = self.next_page_moving(
                f'//*[@id="dnsColl"]/div[2]/div/div/a[{3}]'
            )
            page = self.news_info_collect(self.driver.page_source)
            data.append(page)
            next_page_button.click()
            self.count -= 1
        else:
            self.logging(logging.INFO, "다음 크롤링 종료합니다")
            self.driver.quit()
        return data
