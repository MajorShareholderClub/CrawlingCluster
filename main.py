import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.driver.naver_news_driver import AsyncNaverNewsParsingDriver
from src.driver.selenium_driver import GoogleSeleniumMovingElementLocation
from src.driver.selenium_driver import BingSeleniumMovingElementLocation
from src.driver.selenium_driver import DaumSeleniumMovingElementsLocation


def process_naver():
    """Naver 크롤링"""
    asyncio.run(AsyncNaverNewsParsingDriver("비트코인", 10).extract_news_urls())


def process_google():
    """Google 크롤링"""
    GoogleSeleniumMovingElementLocation("비트코인", 1).begin_page_navigation()


def process_daum():
    """Daum 크롤링"""
    DaumSeleniumMovingElementsLocation("비트코인", 1).page_injection()


def process_bing():
    """Bing 크롤링"""
    BingSeleniumMovingElementLocation("비트코인", 1).repeat_scroll()


def main():
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_naver),
            executor.submit(process_google),
            executor.submit(process_daum),
            executor.submit(process_bing),
        ]
        # 모든 작업이 완료될 때까지 기다립니다.
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
