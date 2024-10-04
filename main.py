import asyncio
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

from crawling.src.driver.selenium_driver import (
    InvestingSeleniumMovingElementLocation,
    InvestingTargetSeleniumMovingElementLocation,
)
from crawling.src.driver.api_news_driver import (
    AsyncDaumrNewsParsingDriver,
    AsyncNaverNewsParsingDriver,
    AsyncGoogleNewsParsingDriver,
)

SeleniumCrawlingClass = (
    InvestingSeleniumMovingElementLocation
    | InvestingTargetSeleniumMovingElementLocation
)


# fmt: off
class Crawler:
    def __init__(self, query: str, count: int) -> None:
        self.query = query
        self.count = count
        self.thred = ThreadPoolExecutor(2)

    async def process_crawling(self, crawling_class: SeleniumCrawlingClass, crawling_method: str) -> None:
        """크롤링을 위한 공통 비동기 처리 함수"""
        loop = asyncio.get_event_loop()
        crawler: SeleniumCrawlingClass = crawling_class(self.query, self.count)
        method: Callable = getattr(crawler, crawling_method)
        await loop.run_in_executor(self.thred, method)

    async def process_all(self) -> list:
        tasks = []

        # 비동기 크롤러 클래스와 메서드의 매핑
        crawlers = [
            # (AsyncNaverNewsParsingDriver, "news_collector"),
            # (AsyncDaumrNewsParsingDriver, "news_collector"),
            # (AsyncGoogleNewsParsingDriver, "news_collector"),
            (InvestingSeleniumMovingElementLocation, "crawling_main"),
            (InvestingTargetSeleniumMovingElementLocation, "crawling_main"),
        ]
        for crawler_class, method_name in crawlers:
            if hasattr(crawler_class, method_name):
                if method_name == "news_collector":
                    tasks.append(asyncio.create_task(crawler_class(self.query, self.count).news_collector()))
                else:
                    tasks.append(asyncio.create_task(self.process_crawling(crawler_class, method_name)))
        return await asyncio.gather(*tasks)


# 사용 예
if __name__ == "__main__":
    crawler = Crawler("비트코인", 3)
    asyncio.run(crawler.process_all())
