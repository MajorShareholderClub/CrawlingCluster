import asyncio
from typing import Callable, Union, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from crawling.src.core.types import UrlDictCollect
from crawling.src.driver.investing.investing_selenium import (
    InvestingSeleniumMovingElementLocation,
    InvestingTargetSeleniumMovingElementLocation,
)
from crawling.src.driver.google.google_selenium import (
    GoogleSeleniumMovingElementLocation,
)
from crawling.src.driver.daum.daum_selenium import DaumSeleniumMovingElementsLocation
from crawling.src.driver.api_req.api_news_driver import (
    AsyncDaumNewsParsingDriver,
    AsyncNaverNewsParsingDriver,
    AsyncGoogleNewsParsingDriver,
)
from databases.services.keyword_generator import BaseCountry, load_countries_from_yaml

# Selenium 크롤링 클래스 타입 정의
SeleniumCrawlingClass = Union[
    InvestingSeleniumMovingElementLocation,
    InvestingTargetSeleniumMovingElementLocation,
    GoogleSeleniumMovingElementLocation,
    DaumSeleniumMovingElementsLocation,
]


def run_investing_crawler(
    target: str, count: int, crawler_class: SeleniumCrawlingClass
) -> UrlDictCollect:
    """셀레니움 크롤러 실행 (동기 방식)

    셀레니움은 동기 작업이므로 비동기 컨텍스트 없이 직접 실행합니다.
    도메인별 세션 관리자를 통해 세션을 효율적으로 재사용합니다.
    """
    # 크롤링 클래스 이름에 따라 도메인 설정
    domain = None
    if "Investing" in crawler_class.__name__:
        domain = "investing.com"
    elif "Google" in crawler_class.__name__:
        domain = "google.com"
    elif "Daum" in crawler_class.__name__:
        domain = "daum.net"

    # 인스턴스 직접 생성 (타겟, 카운트)
    instance = crawler_class(target, count)

    match instance:
        case InvestingTargetSeleniumMovingElementLocation():
            return instance.investing_target_news_selenium_start()
        case InvestingSeleniumMovingElementLocation():
            return instance.investing_news_selenium_start()
        case GoogleSeleniumMovingElementLocation():
            return instance.google_seleium_start()
        case DaumSeleniumMovingElementsLocation():
            return instance.daum_selenium_start()


async def run_api_task(
    target: str, count: int, driver_class: Callable
) -> UrlDictCollect:
    """API 크롤러 단일 태스크 실행 (비동기)"""
    driver = driver_class(target=target, count=count)
    return await driver.news_collector()


def get_keywords_and_queries(base_keyword: str) -> Tuple[List[str], List[str]]:
    """키워드와 질의어를 생성"""
    # 국가별 키워드 데이터 로드
    countries = load_countries_from_yaml()

    # 한국어 데이터 사용 (최초는 'kr' 키 사용)
    kr_data = countries.get("KR", next(iter(countries.values())))

    # 기본 키워드와 함께 활용할 수 있는 키워드
    keywords = [base_keyword] + [
        f"{base_keyword} {context}" for context in kr_data.context_keywords[:5]
    ]

    # 키워드 조합 생성
    keyword_combinations = kr_data.generate_search_queries()

    # 질의 템플릿 적용
    queries = list(kr_data.apply_question_templates(keyword_combinations))[:10]

    return keywords, queries


async def run_api_crawlers(target: str, count: int) -> list[UrlDictCollect]:
    """API 기반 크롤러들을 병렬로 실행 (질의어 기반)"""
    # 키워드와 질의어 생성
    _, queries = get_keywords_and_queries(target)

    tasks = []
    # 각 질의어에 대해 API 크롤러 실행
    for query in queries[:3]:  # 최대 3개 질의어만 사용
        tasks.extend(
            [
                run_api_task(query, count, AsyncNaverNewsParsingDriver),
                run_api_task(query, count, AsyncDaumNewsParsingDriver),
                run_api_task(query, count, AsyncGoogleNewsParsingDriver),
            ]
        )

    # API 크롤러는 진짜 비동기로 병렬 실행
    return await asyncio.gather(*tasks)


async def run_selenium_crawlers(target: str, count: int) -> list[UrlDictCollect]:
    """Selenium 기반 크롤러들을 병렬로 실행 (ThreadPool 사용)"""
    # 키워드와 질의어 생성
    keywords, queries = get_keywords_and_queries(target)

    # 셀레니움 크롤러를 위한 작업 목록 생성
    crawlers = []

    # Investing.com 크롤러 - 키워드 기반
    for keyword in keywords[:2]:  # 최대 2개 키워드만 사용
        crawlers.extend(
            [
                (keyword, count, InvestingSeleniumMovingElementLocation),
                (keyword, count, InvestingTargetSeleniumMovingElementLocation),
            ]
        )

    # Google, Daum 크롤러 - 질의어 기반
    for query in queries[:2]:  # 최대 2개 질의어만 사용
        crawlers.extend(
            [
                (query, count, GoogleSeleniumMovingElementLocation),
                (query, count, DaumSeleniumMovingElementsLocation),
            ]
        )

    # 셀레니움 크롤러는 ThreadPool을 통해 병렬 실행 (4개 워커로 제한)
    loop = asyncio.get_running_loop()
    results = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 각 크롤러를 별도 스레드에서 실행
        futures = [
            loop.run_in_executor(executor, run_investing_crawler, *args)
            for args in crawlers
        ]

        # 모든 스레드의 결과 대기
        for future in futures:
            try:
                result = await future
                if result:
                    results.append(result)
            except Exception as e:
                print(f"셀레니움 크롤러 실행 중 오류: {e}")

    return results


async def crawling_data_insert_db(target: str, count: int):
    """메인 크롤링 함수: API와 Selenium 크롤러를 분리하여 실행"""
    # API 크롤러와 Selenium 크롤러를 동시에 시작하되, 내부적으로는 각각 그룹화
    api_results = await asyncio.gather(
        run_api_crawlers(target, count),
        # run_selenium_crawlers(target, count)
    )

    # 여기서 수집된 데이터를 처리할 수 있음
    # 예: 데이터베이스 저장, 분석 등
    print(f"API 크롤러 결과: {len(api_results)} 건의 데이터 수집")
    # print(f"Selenium 크롤러 결과: {len(selenium_results)} 건의 데이터 수집")

    return api_results


if __name__ == "__main__":
    a = asyncio.run(crawling_data_insert_db("BTC", 3))
    print(a)
