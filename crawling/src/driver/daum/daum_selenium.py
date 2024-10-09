import time
import random
import logging
import asyncio

from selenium.common.exceptions import NoSuchElementException, WebDriverException
from crawling.config.setting import chrome_option_setting, prefs
from crawling.src.core.types import UrlDictCollect
from crawling.src.utils.logger import AsyncLogger
from crawling.src.utils.search_util import PageScroller
from crawling.src.utils.search_util import (
    PageScroller,
    web_element_clicker,
    ChromeDriver,
)
from crawling.src.driver.news_parsing import DaumNewsDataCrawling
from crawling.src.driver.api_req.api_news_driver import AsyncDaumNewsParsingDriver


class DaumSeleniumMovingElementsLocation(DaumNewsDataCrawling):
    def __init__(self, target: str, count: int) -> None:
        """
        Args:
            target (str): 검색 타겟
            count (int): 얼마나 수집할껀지
        """
        self.target = target
        self.url = f"https://search.daum.net/search?w=news&nil_search=btn&DA=NTB&enc=utf8&cluster=y&cluster_page=1&q={target}"
        self.driver: ChromeDriver = chrome_option_setting(prefs=prefs)
        self.count = count if count - 3 <= 0 else count - 3
        self.logging = AsyncLogger(
            target="Daum", log_file="Daum_selenium.log"
        ).log_message_sync

    def page_injection(self) -> UrlDictCollect:
        """
        //*[@id="dnsColl"]/div[2]/div/div/a[1] 2
        //*[@id="dnsColl"]/div[2]/div/div/a[2] 3
        //*[@id="dnsColl"]/div[2]/div/div/a[3] 4
        //*[@id="dnsColl"]/div[2]/div/div/a[4] 5
        """
        self.driver.get(self.url)
        self.logging(logging.INFO, "다음 크롤링 시작합니다")
        data = []
        if self.count <= 4:
            for i in range(1, self.count + 1):
                PageScroller(self.driver).page_scroll()
                self.driver.implicitly_wait(random.uniform(5.0, 10.0))
                time.sleep(1)
                next_page_button = web_element_clicker(
                    self.driver, f'//*[@id="dnsColl"]/div[2]/div/div/a[{i}]'
                )
                page = self.news_info_collect(self.driver.page_source)
                data.append(page)
                next_page_button.click()

        while self.count:
            PageScroller(self.driver).page_scroll()
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
            time.sleep(1)
            next_page_button = web_element_clicker(
                self.driver, f'//*[@id="dnsColl"]/div[2]/div/div/a[{3}]'
            )
            page = self.news_info_collect(self.driver.page_source)
            data.append(page)
            next_page_button.click()
            self.count -= 1

        self.logging(logging.INFO, "다음 크롤링 종료합니다")
        self.driver.quit()
        return data

    def daum_selenium_start(self) -> UrlDictCollect:
        try:
            self.page_injection()
        except (NoSuchElementException, WebDriverException) as error:
            message = f"다음과 같은 에러로 진행하지못했습니다 --> {error} Api 호출로 대신합니다"
            self.logging(logging.ERROR, message)
            return asyncio.run(
                AsyncDaumNewsParsingDriver(self.target, self.count).news_collector()
            )
