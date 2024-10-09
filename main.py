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
from crawling.src.core.database.async_mongo import mongo_main

SeleniumCrawlingClass = (
    InvestingSeleniumMovingElementLocation
    | InvestingTargetSeleniumMovingElementLocation
)


async def crawl_and_insert(
    target: str, count: int, driver: Callable, source: str
) -> None:
    loop = asyncio.get_running_loop()

    def run_driver() -> UrlDictCollect:
        # 새 이벤트 루프를 생성하고 실행
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(
            driver(target=target, count=count).news_collector()
        )

    with ThreadPoolExecutor(max_workers=3) as executor:
        # run_in_executor를 통해 크롤링을 비동기적으로 실행
        data_list = await loop.run_in_executor(executor, run_driver)

    # 데이터가 있을 때만 처리
    if data_list:
        # MongoDB에 데이터 삽입
        for data in data_list:  # 각 항목을 반복
            await mongo_main(data, source)  # MongoDB에 개별 데이터 삽입


async def crawling_data_insert_db(target: str, count: int):
    tasks = [
        crawl_and_insert(target, count, AsyncNaverNewsParsingDriver, "naver"),
        crawl_and_insert(target, count, AsyncDaumNewsParsingDriver, "daum"),
        crawl_and_insert(target, count, AsyncGoogleNewsParsingDriver, "google"),
    ]

    await asyncio.gather(*tasks)  # 모든 크롤링 작업을 동시에 수행


# 비동기 함수 실행
asyncio.run(crawling_data_insert_db("BTC", 3))
