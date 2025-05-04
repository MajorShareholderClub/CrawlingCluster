import logging
import functools
import time
from typing import TypeVar, Callable, ParamSpec, Union, Any, Type, cast

from redis.exceptions import RedisError, ConnectionError, ResponseError, TimeoutError
from redis.cluster import ClusterError

from bs4 import BeautifulSoup, FeatureNotFound, ParserRejectedMarkup
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    JavascriptException,
)
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError as RequestsConnectionError,
)

# 로깅 설정
logger = logging.getLogger(__name__)

# Type Annotations을 위한 정의
T = TypeVar("T")  # 반환 타입
P = ParamSpec("P")  # 파라미터 사양

# Redis 관련 예외 타입 정의
RedisExceptionType = (
    RedisError | ConnectionError | TimeoutError | ResponseError | ClusterError
)

# BeautifulSoup 관련 예외 타입 정의
ParserExceptionType = (
    FeatureNotFound | ParserRejectedMarkup | ValueError | AttributeError | IndexError
)  # ValueError: BeautifulSoup 관련 값 오류, AttributeError: 요소 속성 접근 오류, IndexError: 인덱스 접근 오류

# Selenium 관련 예외 타입 정의
SeleniumExceptionType = (
    WebDriverException
    | TimeoutException
    | NoSuchElementException
    | ElementNotInteractableException
    | StaleElementReferenceException
    | ElementClickInterceptedException
    | JavascriptException
)

# HTTP 요청 관련 예외 타입 정의
RequestExceptionType = (
    RequestException | Timeout | RequestsConnectionError | ValueError | UnicodeError
)  # ValueError: JSON 파싱 오류 등, UnicodeError: 인코딩 관련 오류

# 모든 크롤링 관련 예외 타입 정의 (위 모든 예외 포함)
CrawlingExceptionType = (
    RedisExceptionType
    | ParserExceptionType
    | SeleniumExceptionType
    | RequestExceptionType
)


def handle_redis_exceptions(
    retries: int = 3, delay: float = 1.0
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Redis 작업 중 발생하는 모든 예외를 처리하는 데코레이터

    Args:
        retries: 재시도 횟수 (기본값: 3)
        delay: 재시도 간 지연 시간(초) (기본값: 1.0)

    Returns:
        데코레이팅된 함수

    Example:
        @handle_redis_exceptㄴions
        def fetch_data(key):
            return redis_client.get(key)

        # 재시도 횟수와 지연 시간 지정
        @handle_redis_exceptions(retries=5, delay=2.0)
        def set_data(key, value):
            return redis_client.set(key, value)
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except RedisExceptionType as e:
                    last_exception = e
                    logger.warning(
                        f"Redis 작업 중 오류 발생 (시도 {attempt+1}/{retries}): {str(e)}"
                    )
                    if attempt < retries - 1:
                        time.sleep(delay)

            # 모든 재시도 실패 시 마지막 예외를 다시 발생
            if last_exception:
                logger.error(
                    f"Redis 작업 실패 (최대 재시도 횟수 초과): {str(last_exception)}"
                )
                raise last_exception

            # 이 코드는 실행되지 않아야 함 (타입 검사용)
            return cast(T, None)

        return wrapper

    return decorator


def handle_parser_exceptions(
    default_return: Any = None, log_level: str = "error"
) -> Callable[[Callable[P, T]], Callable[P, Union[T, Any]]]:
    """
    HTML 파싱 작업 중 발생하는 모든 예외를 처리하는 데코레이터

    Args:
        default_return: 예외 발생 시 반환할 기본값 (기본값: None)
        log_level: 로깅 레벨 (기본값: "error")

    Returns:
        데코레이팅된 함수

    Example:
        @handle_parser_exceptions(default_return=[])
        def parse_news_items(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            return [item.text for item in soup.select('div.news-item')]
    """

    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except ParserExceptionType as e:
                # 로깅 레벨에 따라 다른 로깅 메서드 사용
                if log_level == "warning":
                    logger.warning(f"파싱 중 오류 발생: {str(e)}")
                elif log_level == "info":
                    logger.info(f"파싱 중 오류 발생: {str(e)}")
                else:  # 기본값은 error
                    logger.error(f"파싱 중 오류 발생: {str(e)}")

                return default_return

        return wrapper

    return decorator


def handle_selenium_exceptions(
    retries: int = 3, delay: float = 1.0, default_return: Any = None
) -> Callable[[Callable[P, T]], Callable[P, Union[T, Any]]]:
    """
    Selenium 작업 중 발생하는 모든 예외를 처리하는 데코레이터

    Args:
        retries: 재시도 횟수 (기본값: 3)
        delay: 재시도 간 지연 시간(초) (기본값: 1.0)
        default_return: 모든 재시도 실패 시 반환할 기본값 (기본값: None)

    Returns:
        데코레이팅된 함수

    Example:
        @handle_selenium_exceptions(retries=2, delay=0.5)
        def click_element(driver, selector):
            element = driver.find_element_by_css_selector(selector)
            element.click()
            return True
    """

    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Any]:
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except SeleniumExceptionType as e:
                    last_exception = e
                    logger.warning(
                        f"Selenium 작업 중 오류 발생 (시도 {attempt+1}/{retries}): {str(e)}"
                    )
                    if attempt < retries - 1:
                        time.sleep(delay)

            # 모든 재시도 실패 시 로깅하고 기본값 반환
            if last_exception:
                logger.error(
                    f"Selenium 작업 실패 (최대 재시도 횟수 초과): {str(last_exception)}"
                )

            return default_return

        return wrapper

    return decorator


def handle_request_exceptions(
    retries: int = 3, delay: float = 1.0, default_return: Any = None
) -> Callable[[Callable[P, T]], Callable[P, Union[T, Any]]]:
    """
    HTTP 요청 중 발생하는 모든 예외를 처리하는 데코레이터

    Args:
        retries: 재시도 횟수 (기본값: 3)
        delay: 재시도 간 지연 시간(초) (기본값: 1.0)
        default_return: 모든 재시도 실패 시 반환할 기본값 (기본값: None)

    Returns:
        데코레이팅된 함수

    Example:
        @handle_request_exceptions(retries=3, delay=2.0, default_return={'error': True})
        def fetch_api_data(url):
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """

    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Any]:
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except RequestExceptionType as e:
                    last_exception = e
                    logger.warning(
                        f"HTTP 요청 중 오류 발생 (시도 {attempt+1}/{retries}): {str(e)}"
                    )
                    if attempt < retries - 1:
                        time.sleep(delay)

            # 모든 재시도 실패 시 로깅하고 기본값 반환
            if last_exception:
                logger.error(
                    f"HTTP 요청 실패 (최대 재시도 횟수 초과): {str(last_exception)}"
                )

            return default_return

        return wrapper

    return decorator
