import time
import random
import logging
import asyncio
from typing import Any, Callable, Dict

from selenium.common.exceptions import NoSuchElementException, WebDriverException
from config.setting import prefs
from crawling.src.core.types import UrlDictCollect
from crawling.src.driver.news_parsing import GoogleNewsDataSeleniumCrawling
from crawling.src.driver.api_req.api_news_driver import AsyncGoogleNewsParsingDriver
from crawling.src.utils.search_util import (
    PageScroller,
    web_element_clicker,
    ChromeDriver,
)
from crawling.src.utils.session_manager import SeleniumSessionManager


class GoogleSeleniumMovingElementLocation(GoogleNewsDataSeleniumCrawling, SeleniumSessionManager):
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
        
        # 세션 관리 드라이버 초기화
        self.driver = self.init_driver(custom_prefs=prefs, use_session=True)

    def scroll_through_pages(
        self, start: int, xpath: Callable[[int], str]
    ) -> Dict[str, UrlDictCollect]:
        """페이지 이동"""

        page_dict: Dict[str, UrlDictCollect] = {}
        for i in range(start, self.count + start):
            next_page_button: Any = web_element_clicker(xpath(i))
            message = f"{i-2}page로 이동합니다 --> {xpath(i)} 이용합니다"
            self.logger.info(message)

            data = self.extract_news_urls(self.driver.page_source)
            page_dict[str(i - 2)] = data
            next_page_button.click()
            self.driver.implicitly_wait(random.uniform(5.0, 10.0))
            PageScroller(self.driver).page_scroll(self.driver)

        self.logger.info(f"google 수집 종료")
        # 쿠키 저장 후 드라이버 종료
        self.close_driver()

        return page_dict

    # fmt: off
    def google_seleium_start(self) -> Dict[str, UrlDictCollect] | UrlDictCollect:
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
            self.logger.error(message)
            self.close_driver()
            time.sleep(3)
            rest = AsyncGoogleNewsParsingDriver(self.target, self.count)
            return asyncio.run(rest.news_collector())
