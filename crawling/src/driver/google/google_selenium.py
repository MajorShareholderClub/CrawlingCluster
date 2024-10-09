import time
import random
import logging
import asyncio
from typing import Any, Callable

from selenium.common.exceptions import NoSuchElementException, WebDriverException
from crawling.config.setting import chrome_option_setting, prefs
from crawling.src.core.types import UrlDictCollect
from crawling.src.driver.news_parsing import GoogleNewsDataSeleniumCrawling
from crawling.src.driver.api_req.api_news_driver import AsyncGoogleNewsParsingDriver
from crawling.src.utils.logger import AsyncLogger
from crawling.src.utils.search_util import (
    PageScroller,
    web_element_clicker,
    ChromeDriver,
)


class GoogleSeleniumMovingElementLocation(GoogleNewsDataSeleniumCrawling):
    """구글 크롤링 셀레니움 location"""

    def __init__(self, target: str, count: int) -> None:
        """데이터를 크롤링할 타겟 선정"""
        self.target = target
        self.count = count
        self.url = f"https://www.google.com/search?q={target}&tbm=nws&gl=ko&hl=kr"
        self.driver: ChromeDriver = chrome_option_setting(prefs)
        self.logging = AsyncLogger("google", "selenium_google.log").log_message_sync

    def scroll_through_pages(
        self, start: int, xpath: Callable[[int], str]
    ) -> dict[str, UrlDictCollect]:
        """페이지 이동"""

        page_dict: dict[str, UrlDictCollect] = {}
        for i in range(start, self.count + start):
            next_page_button: Any = web_element_clicker(xpath(i))
            message = f"{i-2}page로 이동합니다 --> {xpath(i)} 이용합니다"
            self.logging(logging.INFO, message)

            data = self.extract_news_urls(self.driver.page_source)
            page_dict[str(i - 2)] = data
            next_page_button.click()
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
            PageScroller(self.driver).page_scroll(self.driver)

        self.logging(logging.INFO, f"google 수집 종료")
        self.driver.quit()

        return page_dict

    # fmt: off
    def google_seleium_start(self) -> dict[str, UrlDictCollect] | UrlDictCollect:
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
            message = (
                f"다음과 같은 이유로 google 수집 종료 Rest 수집으로 전환합니다 --> {e}"
            )
            self.logging(logging.ERROR, message)
            self.driver.quit()
            time.sleep(3)
            rest = AsyncGoogleNewsParsingDriver(self.target, self.count)
            return asyncio.run(rest.news_collector())
        finally:
            self.driver.quit()
