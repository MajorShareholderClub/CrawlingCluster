import tracemalloc
import re

tracemalloc.start()

import time
import random
import logging
import asyncio
from typing import Any, Callable
from crawling.src.core.types import ChromeDriver

from crawling.config.selenium_setting import chrome_option_setting, WITH_TIME

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
    TimeoutException,
)

from crawling.src.utils.logger import AsyncLogger
from crawling.src.core.types import UrlDictCollect
from crawling.src.parsing.news_parsing import (
    GoogleNewsDataSeleniumCrawling,
    InvestingNewsDataSeleniumCrawling,
)
from crawling.src.driver.api_news_driver import AsyncGoogleNewsParsingDriver
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.ERROR)


def page_scroll(driver: ChromeDriver) -> None:
    """스크롤을 5번에 걸쳐서 내리기, 3가지 스크롤 케이스 포함"""

    # 각 스크롤에서 이동할 거리
    scroll_heights = [int(random.uniform(1000, 3000)) for _ in range(5)]

    def smooth_type_scroll(scroll: int, steps: int = 10, delay: float = 0.05) -> None:
        current_position = driver.execute_script("return window.pageYOffset;")
        step_size = scroll / steps
        for i in range(steps):
            driver.execute_script(
                f"window.scrollTo(0, {current_position + (step_size * (i + 1))})"
            )
            time.sleep(delay)

    def fast_scroll(scroll_cal: int) -> None:
        """빠르게 스크롤"""
        current_position = driver.execute_script("return window.pageYOffset;")
        driver.execute_script(f"window.scrollTo(0, {current_position + scroll_cal})")

    # 3가지 스크롤 케이스 실행
    for scroll_distance in scroll_heights:
        scroll_type = random.choice(["smooth", "fast", "slow"])  # 랜덤 스크롤 타입 선택
        if scroll_type == "smooth":
            print(f"부드러운 스크롤 실행 중: {scroll_distance}px")
            smooth_type_scroll(scroll_distance)
        elif scroll_type == "fast":
            print(f"빠른 스크롤 실행 중: {scroll_distance}px")
            fast_scroll(scroll_distance)
        else:
            print(f"느린 스크롤 실행 중: {scroll_distance}px")
            smooth_type_scroll(scroll_distance, steps=30, delay=0.1)


def web_element_clicker(driver: ChromeDriver, xpath: str):
    element = WebDriverWait(driver, WITH_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    return element


class GoogleSeleniumMovingElementLocation(GoogleNewsDataSeleniumCrawling):
    """구글 크롤링 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """데이터를 크롤링할 타겟 선정"""
        self.target = target
        self.count = count
        self.url = f"https://www.google.com/search?q={target}&tbm=nws&gl=ko&hl=kr"
        self.driver: ChromeDriver = chrome_option_setting()
        self.logging = AsyncLogger("google", "selenium_google.log").log_message_sync
        self.google_hveid = {
            "data-hveid": re.compile(r"CA|QHw|CA[0-9a-zA-Z]+|CB[0-9a-zA-Z]+")
        }

    # fmt: off
    def scroll_through_pages(self, start: int, xpath: Callable[[int], str]) -> dict[str, str]:
        """페이지 이동"""

        page_dict: dict[str, str] = {}
        for i in range(start, self.count + start):
            next_page_button: Any = web_element_clicker(xpath(i))
            self.logging(logging.INFO, f"{i-2}page로 이동합니다 --> {xpath(i)} 이용합니다")
            
            soup = BeautifulSoup(self.driver.page_source, "lxml")
            data = (
                soup.find("div", {"id": "search"})
                .find("div", {"class": "MjjYud"})
                .find("div", self.google_hveid)
            )
            page_dict[str(i-2)] = str(data)
            next_page_button.click()
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
            page_scroll(self.driver)
        
        self.logging(logging.INFO, f"google 수집 종료")
        self.driver.quit()

        return page_dict


    def begin_page_navigation(self) -> UrlDictCollect:
        """페이지 수집 이동 본체"""

        def mo_xpath_injection(start: int) -> str:
            """google mobile xpath 경로 start는 a tag 기점 a -> a[2]"""
            return f'//*[@id="wepR4d"]/div/span/a[{start-1}]'

        def pa_xpath_injection(start: int) -> str:
            """google site xpath 경로 start는 tr/td[3](page 2) ~ 기점"""
            return f'//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[{start}]/a'

        self.driver.get(self.url)
        try:
            return self.scroll_through_pages(3, pa_xpath_injection)
        except NoSuchElementException:
            return self.scroll_through_pages(2, mo_xpath_injection)
        except WebDriverException as e:
            self.logging(
                logging.ERROR,
                f"다음과 같은 이유로 google 수집 종료 Rest 수집으로 전환합니다 --> {e}",
            )
            self.driver.quit()
            time.sleep(3)
            rest = AsyncGoogleNewsParsingDriver(self.target, self.count)
            return asyncio.run(rest.news_collector())
        finally:
            self.driver.quit()


class InvestingSeleniumMovingElementLocation(InvestingNewsDataSeleniumCrawling):
    def __init__(self, count: int) -> None:
        self.url = "https://kr.investing.com"
        self.count = count
        self.driver: ChromeDriver = chrome_option_setting()
        self.logging = AsyncLogger("google", "selenium_investing.log").log_message_sync

    def wait_and_click(self, driver: ChromeDriver, xpath: str):
        driver.implicitly_wait(10)
        try:
            element = web_element_clicker(driver, xpath=xpath)
            element.click()

        except (ElementClickInterceptedException, TimeoutException) as error:
            print(
                f"다음과 같은 이유로 요소에 접근할 수 없습니다 --> {error} 조정합니다"
            )
            time.sleep(5)

            # 다시 요소를 클릭 가능하게 기다림
            element = web_element_clicker(driver, xpath=xpath)

            # 스크롤을 조정하고 다시 클릭 시도
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            driver.execute_script("window.scrollBy(0, -500);")

            element.click()

    def scroll_through_pages(self, x_path: str) -> None:
        x_path_data = '//*[@id="bottom-nav-row"]/div[1]/nav/ul/li[5]/div[1]/a'

        self.driver.set_page_load_timeout(30.0)
        self.driver.get(self.url)

        self.wait_and_click(self.driver, x_path_data)
        self.wait_and_click(self.driver, x_path)

        page = self.driver.page_source
        print(self.extract_news_urls(page))
        for i in range(1, self.count):
            next_page = (
                f'//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div/div[2]/div/a[{i}]'
            )
            self.wait_and_click(self.driver, next_page)
            time.sleep(1)
            page_scroll(self.driver)

    def crawling_main(self) -> None:
        for i in range(4, 14):
            if i == 7 or i == 10 or i == 11:
                continue
            economin_news_xpath = f'//*[@id="bottom-nav-row"]/div[2]/div/nav/ul/li[{i}]'
            self.scroll_through_pages(x_path=economin_news_xpath)

        self.driver.quit()
