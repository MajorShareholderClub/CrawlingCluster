# import asyncio
# from typing import Callable

from crawling.src.driver.selenium_driver import (
    GoogleSeleniumMovingElementLocation,
    InvestingSeleniumMovingElementLocation,
)

# from crawling.src.driver.api_news_driver import (
#     AsyncDaumrNewsParsingDriver,
#     AsyncNaverNewsParsingDriver,
#     AsyncGoogleNewsParsingDriver,
# )

# SeleniumCrawlingClass = (
#     GoogleSeleniumMovingElementLocation | BingSeleniumMovingElementLocation
# )


# # fmt: off
# class Crawler:
#     def __init__(self, query: str, count: int) -> None:
#         self.query = query
#         self.count = count

#     async def process_crawling(self, crawling_class: SeleniumCrawlingClass, crawling_method: str) -> None:
#         """크롤링을 위한 공통 비동기 처리 함수"""
#         loop = asyncio.get_event_loop()
#         crawler: SeleniumCrawlingClass = crawling_class(self.query, self.count)
#         method: Callable = getattr(crawler, crawling_method)
#         await loop.run_in_executor(None, method)

#     # async def process_google(self) -> None:
#     #     await self.process_crawling(GoogleSeleniumMovingElementLocation, "begin_page_navigation")

#     # async def process_google(self) -> None:
#     #     await self.process_crawling(AsyncGoogleNewsParsingDriver, "news_info_collect")

#     # async def process_bing(self) -> None:
#     #     await self.process_crawling(BingSeleniumMovingElementLocation, "repeat_scroll")

#     async def process_all(self) -> list:
#         tasks = []

#         # 비동기 크롤러 클래스와 메서드의 매핑
#         crawlers = [
#             (AsyncNaverNewsParsingDriver, "news_collector"),
#             (AsyncDaumrNewsParsingDriver, "news_collector"),
#             # (AsyncGoogleNewsParsingDriver, "news_collector")
#             # (GoogleSeleniumMovingElementLocation, "begin_page_navigation"),
#             # (BingSeleniumMovingElementLocation, "repeat_scroll"),
#         ]
#         for crawler_class, method_name in crawlers:
#             if hasattr(crawler_class, method_name):
#                 if method_name == "news_collector":
#                     tasks.append(asyncio.create_task(crawler_class(self.query, self.count).news_collector()))
#                 else:
#                     tasks.append(asyncio.create_task(self.process_crawling(crawler_class, method_name)))
#         return await asyncio.gather(*tasks)


# # 사용 예
# if __name__ == "__main__":
#     for i in range(1, 3):
#         crawler = Crawler("비트코인", 2)
#         asyncio.run(crawler.process_all())

InvestingSeleniumMovingElementLocation(3).crawling_main()
