import asyncio
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

from src.driver.naver_news_driver import AsyncNaverNewsParsingDriver
from src.driver.selenium_driver import GoogleSeleniumMovingElementLocation
from src.driver.selenium_driver import BingSeleniumMovingElementLocation
from src.driver.selenium_driver import DaumSeleniumMovingElementsLocation


def process_naver(query: str, count: int) -> None:
    """Naver 크롤링"""
    asyncio.run(AsyncNaverNewsParsingDriver(query, count).extract_news_urls())


def process_google(query: str, count: int) -> None:
    """Google 크롤링"""
    GoogleSeleniumMovingElementLocation(query, count).begin_page_navigation()


def process_daum(query: str, count: int) -> None:
    """Daum 크롤링"""
    DaumSeleniumMovingElementsLocation(query, count).page_injection()


def process_bing(query: str, count: int) -> None:
    """Bing 크롤링"""
    BingSeleniumMovingElementLocation(query, count).repeat_scroll()


def main():
    queries = ["비트코인"]  # 여기서 필요한 쿼리를 정의
    count = 1  # 필요한 경우 카운트를 수정

    functions: list[Callable[[str, int], None]] = [
        process_naver,
        # process_google,
        # process_daum,
        # process_bing,
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 각 함수와 인수를 매핑합니다.
        futures = [executor.submit(fn, queries, count) for fn in functions]

        # 모든 작업이 완료될 때까지 기다립니다.
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
