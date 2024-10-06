import tracemalloc

tracemalloc.start()

import time
import random
import logging
from typing import Any
from crawling.src.core.types import ChromeDriver

from crawling.config.setting import chrome_option_setting, WITH_TIME, prefs
from crawling.config.properties import (
    INVESTING_NEWS_BOTTEN,
    INVESTING_CATEGORY,
    INVESTING_NEWS_NEXT,
)

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from crawling.src.utils.logger import AsyncLogger
from crawling.src.utils.parsing_util import PageScroller
from crawling.src.parsing.news_parsing import (
    InvestingNewsDataSeleniumCrawling,
    InvestingNewsDataTargetSeleniumCrawling as InvestingTargetNews,
)


logging.basicConfig(level=logging.ERROR)


def web_element_clicker(driver: ChromeDriver, xpath: str):
    element = WebDriverWait(driver, WITH_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    return element


class InvestingSeleniumMovingElementLocation(InvestingNewsDataSeleniumCrawling):
    def __init__(self, target: str, count: int) -> None:
        self.url = "https://kr.investing.com"
        self.count = count
        self.target = target
        self.driver: ChromeDriver = chrome_option_setting(prefs)
        self.log = AsyncLogger(
            "investing", "selenium_investing_news.log"
        ).log_message_sync
        self.log(logging.INFO, f"종합 뉴스 시작합니다")

    def wait_and_click(self, driver: ChromeDriver, xpath: str) -> Any | str:
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

    def scroll_through_pages(self, x_path: str) -> None:
        self.driver.set_page_load_timeout(20.0)
        news_botton = self.wait_and_click(self.driver, INVESTING_NEWS_BOTTEN)[0]
        news_botton.click()

        category = self.wait_and_click(self.driver, x_path)
        category[0].click()

        self.log(logging.INFO, f"{category[1]}부분--{self.count} page 수집합니다")
        for i in range(1, self.count + 1):
            next_page = f"{INVESTING_NEWS_NEXT}/a[{i}]"
            element = self.wait_and_click(self.driver, next_page)

            self.log(logging.INFO, f"{category[1]} 부분 -- {i} page 이동합니다")
            element[0].click()

            PageScroller(self.driver).page_scroll()
            time.sleep(random.uniform(1, 2))

            page: str = self.driver.page_source
            data = len(self.extract_news_urls(page))
            self.log(logging.INFO, f"{category[1]} 뉴스 -- {data}개 수집")

    def crawling_main(self) -> None:
        self.driver.get(self.url)
        for i in range(4, 14):
            if i == 7 or i == 10 or i == 11:
                continue
            news_xpath = f"{INVESTING_CATEGORY}/li[{i}]"
            self.scroll_through_pages(x_path=news_xpath)
        self.driver.quit()


class InvestingTargetSeleniumMovingElementLocation(InvestingTargetNews):
    def __init__(self, target: str, count: int) -> None:
        self.url = f"https://kr.investing.com/search/?q={target}&tab=news"
        self.count = count
        self.target = target
        self.driver: ChromeDriver = chrome_option_setting()
        self.logging = AsyncLogger(
            "investing", f"selenium_coin_{target}_news.log"
        ).log_message_sync

        self.logging(
            logging.INFO,
            f"""{target} 뉴스 시작합니다 -- {target}뉴스 당 [{count}번 스크롤] 수집합니다""",
        )

    def crawling_main(self) -> None:
        self.driver.get(self.url)

        PageScroller(driver=self.driver, second_delay=True).page_scroll()

        data: str = self.driver.page_source
        d = self.extract_news_urls(html=data)
        self.logging(logging.INFO, f"{self.target} 뉴스 -- {len(d)}개 수집")

        self.driver.quit()


# class GoogleSeleniumMovingElementLocation(GoogleNewsDataSeleniumCrawling):
#     """구글 크롤링 셀레니움 location"""

#     def __init__(self, target: str, count: int) -> None:
#         """데이터를 크롤링할 타겟 선정"""
#         self.target = target
#         self.count = count
#         self.url = f"https://www.google.com/search?q={target}&tbm=nws&gl=ko&hl=kr"
#         self.driver: ChromeDriver = chrome_option_setting(prefs)
#         self.logging = AsyncLogger("google", "selenium_google.log").log_message_sync
#         self.google_hveid = {
#             "data-hveid": re.compile(r"CA|QHw|CA[0-9a-zA-Z]+|CB[0-9a-zA-Z]+")
#         }

#     def scroll_through_pages(
#         self, start: int, xpath: Callable[[int], str]
#     ) -> dict[str, str]:
#         """페이지 이동"""

#         page_dict: dict[str, str] = {}
#         for i in range(start, self.count + start):
#             next_page_button: Any = web_element_clicker(xpath(i))
#             message = f"{i-2}page로 이동합니다 --> {xpath(i)} 이용합니다"
#             self.logging(logging.INFO, message)

#             soup = BeautifulSoup(self.driver.page_source, "lxml")
#             data = (
#                 soup.find("div", {"id": "search"})
#                 .find("div", {"class": "MjjYud"})
#                 .find("div", self.google_hveid)
#             )
#             page_dict[str(i - 2)] = str(data)
#             next_page_button.click()
#             self.driver.implicitly_wait(random.uniform(5.0, 10.0))
#             PageScroller(self.driver).page_scroll(self.driver)

#         self.logging(logging.INFO, f"google 수집 종료")
#         self.driver.quit()

#         return page_dict

# fmt: off
# def begin_page_navigation(self) -> UrlDictCollect:
#     """페이지 수집 이동 본체"""

#     def mo_xpath_injection(start: int) -> str:
#         """google mobile xpath 경로 start는 a tag 기점 a -> a[2]"""
#         return f'//*[@id="wepR4d"]/div/span/a[{start-1}]'

#     def pa_xpath_injection(start: int) -> str:
#         """google site xpath 경로 start는 tr/td[3](page 2) ~ 기점"""
#         return f'//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[{start}]/a'

#     self.driver.get(self.url)
#     try:
#         return self.scroll_through_pages(3, pa_xpath_injection)
#     except NoSuchElementException:
#         return self.scroll_through_pages(2, mo_xpath_injection)
#     except WebDriverException as e:
#         message = f"다음과 같은 이유로 google 수집 종료 Rest 수집으로 전환합니다 --> {e}"
#         self.logging(logging.ERROR, message)
#         self.driver.quit()
#         time.sleep(3)
#         rest = AsyncGoogleNewsParsingDriver(self.target, self.count)
#         return asyncio.run(rest.news_collector())
#     finally:
#         self.driver.quit()
