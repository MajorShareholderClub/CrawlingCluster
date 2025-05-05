import asyncio
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

from crawling.src.core.types import UrlDictCollect
from crawling.src.driver.investing.investing_selenium import (
    InvestingSeleniumMovingElementLocation,
    InvestingTargetSeleniumMovingElementLocation,
)
from crawling.src.driver.api_req.api_news_driver import (
    AsyncDaumNewsParsingDriver,
    AsyncNaverNewsParsingDriver,
    AsyncGoogleNewsParsingDriver,
)

SeleniumCrawlingClass = (
    InvestingSeleniumMovingElementLocation
    | InvestingTargetSeleniumMovingElementLocation
)


async def run_investing_crawler(
    target: str, count: int, crawler_class: SeleniumCrawlingClass
) -> None:
    loop = asyncio.get_running_loop()

    def execute_selenium():
        instance = crawler_class(target, count)
        if isinstance(instance, InvestingTargetSeleniumMovingElementLocation):
            return instance.investing_target_news_selenium_start()
        return instance.investing_news_selenium_start()

    with ThreadPoolExecutor(max_workers=1) as executor:
        # Selenium 작업을 별도 스레드에서 실행
        data_list = await loop.run_in_executor(executor, execute_selenium)


async def crawl_and_insert(target: str, count: int, driver: Callable) -> None:
    loop = asyncio.get_running_loop()

    def run_driver() -> UrlDictCollect:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(
            driver(target=target, count=count).news_collector()
        )

    with ThreadPoolExecutor(max_workers=3) as executor:
        data_list = await loop.run_in_executor(executor, run_driver)


async def crawling_data_insert_db(target: str, count: int):
    tasks = [
        # API 기반 크롤러 태스크
        crawl_and_insert(target, count, AsyncNaverNewsParsingDriver, "naver"),
        crawl_and_insert(target, count, AsyncDaumNewsParsingDriver, "daum"),
        crawl_and_insert(target, count, AsyncGoogleNewsParsingDriver, "google"),
        # 셀레니움
        run_investing_crawler(target, count, InvestingSeleniumMovingElementLocation),
        run_investing_crawler(
            target, count, InvestingTargetSeleniumMovingElementLocation
        ),
    ]

    await asyncio.gather(*tasks)  # 모든 크롤링 작업을 동시에 수행


if __name__ == "__main__":
    asyncio.run(crawling_data_insert_db("BTC", 3))
