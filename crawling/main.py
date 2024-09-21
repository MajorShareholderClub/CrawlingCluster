import asyncio


from src.driver.selenium_driver import GoogleSeleniumMovingElementLocation
from src.driver.selenium_driver import BingSeleniumMovingElementLocation
from src.driver.selenium_driver import DaumSeleniumMovingElementsLocation
from src.driver.api_news_driver import (
    AsyncDaumrNewsParsingDriver,
    AsyncNaverNewsParsingDriver,
)


async def process_crawling(
    crawling_class, query: str, count: int, crawling_method: str
) -> None:
    """크롤링을 위한 공통 비동기 처리 함수"""
    loop = asyncio.get_event_loop()
    crawler = crawling_class(query, count)
    method = getattr(
        crawler, crawling_method
    )  # 문자열로 메서드 이름을 받아 해당 메서드 참조
    await loop.run_in_executor(None, method)


# async def process_google(query: str, count: int) -> None:
#     """Google 크롤링"""
#     loop = asyncio.get_event_loop()
#     g = GoogleSeleniumMovingElementLocation(query, count)
#     return await loop.run_in_executor(None, g.begin_page_navigation)


# def process_daum(query: str, count: int) -> None:
#     """Daum 크롤링"""
#     DaumSeleniumMovingElementsLocation(query, count).page_injection()


# def process_bing(query: str, count: int) -> None:
#     """Bing 크롤링"""
#     BingSeleniumMovingElementLocation(query, count).repeat_scroll()
# 개별 크롤링 함수
async def process_google(query: str, count: int) -> None:
    await process_crawling(
        GoogleSeleniumMovingElementLocation, query, count, "begin_page_navigation"
    )


async def process_daum(query: str, count: int) -> None:
    await process_crawling(
        DaumSeleniumMovingElementsLocation, query, count, "page_injection"
    )


async def process_bing(query: str, count: int) -> None:
    await process_crawling(
        BingSeleniumMovingElementLocation, query, count, "repeat_scroll"
    )


async def process_daum_naver(query: str, count: int) -> None:
    """Naver 크롤링"""
    tasks = [
        # asyncio.create_task(AsyncDaumrNewsParsingDriver(query, count).news_colletor()),
        # asyncio.create_task(process_google(query=query, count=count)),
        # asyncio.create_task(process_daum(query=query, count=count)),
        asyncio.create_task(process_bing(query=query, count=count)),
    ]
    return await asyncio.gather(*tasks)


asyncio.run(process_daum_naver("비트코인", 1))

# def main():
#     queries = ["비트코인"]  # 여기서 필요한 쿼리를 정의
#     count = 10  # 필요한 경우 카운트를 수정

#     functions: list[Callable[[str, int], None]] = [
#         asyncio.run(process_daum_naver),
#         # process_google,
#         # # process_bing,
#     ]

#     with ThreadPoolExecutor(max_workers=4) as executor:
#         # 각 함수와 인수를 매핑합니다.
#         futures = [executor.submit(fn, queries, count) for fn in functions]

#         # 모든 작업이 완료될 때까지 기다립니다.
#         for future in futures:
#             future.result()


# if __name__ == "__main__":
#     main()
