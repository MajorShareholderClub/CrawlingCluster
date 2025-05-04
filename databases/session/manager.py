import json
import time
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from fake_useragent import UserAgent
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException, TimeoutException

from databases.session.storage import SessionStorage
from databases.session.validator import SessionValidator
from databases.session.retry import RetryStrategy

# 로깅 설정
logger = logging.getLogger("session.manager")


class SessionError(Exception):
    """세션 관련 오류를 나타내는 예외 클래스"""
    pass


class CookieManager:
    """쿠키 기본 관리 기능을 담당하는 클래스"""

    def __init__(self, storage: SessionStorage):
        self.storage = storage
        self.user_agent_generator = UserAgent()
        self.min_session_age = 1800  # 30분 (초 단위)

    def is_session_expired(self, cookie_data: dict[str, Any]) -> bool:
        """세션 만료 여부 확인"""
        if not cookie_data or "last_updated" not in cookie_data:
            return True

        try:
            last_updated = datetime.fromisoformat(cookie_data["last_updated"])
            age = datetime.now() - last_updated
            return age.total_seconds() > self.min_session_age
        except (ValueError, TypeError):
            return True

    def save_cookies(
        self, domain: str, cookies: list[dict], user_agent: str | None = None
    ):
        """쿠키 저장 + 사용한 User-Agent 함께 저장"""
        data = {
            "cookies": cookies,
            "user_agent": user_agent,
            "last_updated": datetime.now().isoformat(),
        }
        self.storage.save("cookie", domain, data)

    def load_cookies(self, domain: str) -> dict[str, Any]:
        """도메인 쿠키 로드"""
        data = self.storage.load("cookie", domain)

        # 세션 만료 확인
        if self.is_session_expired(data):
            return {"cookies": []}

        return data

    def generate_new_session(self, domain: str) -> dict[str, Any]:
        """새로운 세션 생성"""
        new_session = {
            "cookies": [],
            "user_agent": self.user_agent_generator.random,
            "last_updated": datetime.now().isoformat(),
        }

        self.storage.save("cookie", domain, new_session)
        return new_session

    def get_or_create_session(self, domain: str) -> dict[str, Any]:
        """있는 세션을 가져오거나 없으면 새로 생성"""
        session = self.load_cookies(domain)

        if not session or not session.get("cookies"):
            session = self.generate_new_session(domain)

        return session

    def clear_cookies(self, domain: str) -> bool:
        """특정 도메인의 쿠키 삭제"""
        return self.storage.delete("cookie", domain)


class SessionStatusManager:
    """세션 상태 관리를 담당하는 클래스"""

    def __init__(self, storage: SessionStorage):
        self.storage = storage

    def update_status(self, domain: str, status: str):
        """도메인별 세션 상태 업데이트"""
        data = {"status": status, "updated_at": datetime.now().isoformat()}
        self.storage.save("status", domain, data)

    def record_error(self, domain: str, error_message: str):
        """세션 오류 정보 기록"""
        data = {"error": error_message, "timestamp": datetime.now().isoformat()}
        self.storage.add_to_list("errors", domain, data)

    def get_status(self, domain: str) -> dict[str, Any]:
        """도메인의 세션 상태 조회"""
        status_data = self.storage.load("status", domain)

        if not status_data:
            return {"status": "unknown", "info": "No session status recorded"}

        # 오류 이력 추가
        errors = self.storage.get_list("errors", domain)
        if errors:
            status_data["recent_errors"] = errors

        return status_data


class SessionManager:
    """모든 쿠키/세션 관리 컴포넌트를 통합한 상위 레벨 관리자"""

    def __init__(self, redis_manager=None):
        """세션 관리자 초기화"""
        self.storage = SessionStorage(redis_manager)
        self.cookie_manager = CookieManager(self.storage)
        self.validator = SessionValidator()
        self.status_manager = SessionStatusManager(self.storage)
        self.retry_strategy = RetryStrategy()

        # 직접 접근 편의를 위한 메서드 매핑
        self.save_cookies = self.cookie_manager.save_cookies
        self.load_cookies = self.cookie_manager.load_cookies
        self.generate_new_session = self.cookie_manager.generate_new_session
        self.get_or_create_session = self.cookie_manager.get_or_create_session
        self.clear_cookies = self.cookie_manager.clear_cookies
        self.get_session_status = self.status_manager.get_status

    def apply_cookies_and_session(
        self,
        driver: WebDriver,
        domain: str,
        max_retries: int | None = None,
        validation_url: str | None = None,
    ):
        """드라이버에 쿠키 적용 + 일관된 User-Agent 사용 (재시도 메커니즘 포함)"""
        if max_retries is None:
            max_retries = self.retry_strategy.max_retries

        if validation_url is None:
            validation_url = f"https://{domain}"

        retries = 0
        delay = self.retry_strategy.initial_delay
        success = False
        last_error = None

        while retries <= max_retries and not success:
            try:
                # 기존 세션 로드
                session_data = self.load_cookies(domain)

                # 세션이 없거나 만료된 경우 새로 생성
                if not session_data or not session_data.get("cookies"):
                    logger.info(
                        f"도메인 {domain}에 대한 유효한 세션이 없어 새로 생성합니다."
                    )
                    session_data = self.generate_new_session(domain)

                # User-Agent 설정
                if session_data.get("user_agent"):
                    script = f"Object.defineProperty(navigator, 'userAgent', {{get: function() {{return '{session_data['user_agent']}';}}}})"
                    driver.execute_script(script)

                # 도메인 페이지 방문
                current_url = driver.current_url
                if not current_url.startswith("http"):
                    logger.info(
                        f"드라이버 초기화를 위해 {validation_url}에 접속합니다."
                    )
                    driver.get(validation_url)

                # 쿠키 적용
                for cookie in session_data.get("cookies", []):
                    clean_cookie = {
                        k: v
                        for k, v in cookie.items()
                        if k
                        in [
                            "name",
                            "value",
                            "domain",
                            "path",
                            "secure",
                            "httpOnly",
                            "expiry",
                        ]
                    }

                    if "domain" not in clean_cookie:
                        clean_cookie["domain"] = domain

                    try:
                        driver.add_cookie(clean_cookie)
                    except Exception as e:
                        logger.warning(f"쿠키 적용 중 오류 발생 (무시됨): {e}")

                # 세션 유효성 검증
                if self.validator.validate(driver, validation_url):
                    success = True
                    self.status_manager.update_status(domain, "valid")
                    logger.info(
                        f"도메인 {domain}에 대한 세션이 성공적으로 적용되었습니다."
                    )
                else:
                    # 유효성 검증 실패 시 세션 재생성
                    raise SessionError(f"세션 유효성 검증 실패: {domain}")

            except (WebDriverException, SessionError, TimeoutException) as e:
                last_error = e
                retries += 1

                if retries <= max_retries:
                    logger.warning(
                        f"세션 적용 실패 ({retries}/{max_retries}): {e}. {delay}초 후 재시도합니다."
                    )

                    # 이전 세션 무효화
                    self.clear_cookies(domain)
                    self.status_manager.update_status(domain, "invalid")

                    # 지수 백오프 적용
                    time.sleep(delay)
                    delay *= self.retry_strategy.backoff_factor

                    # 새로운 User-Agent로 세션 초기화 시도
                    session_data = self.generate_new_session(domain)
                else:
                    logger.error(f"최대 재시도 횟수 초과. 세션 적용 실패: {e}")
                    self.status_manager.update_status(
                        domain, f"failed_after_{max_retries}_retries"
                    )

        if not success and last_error:
            logger.error(f"모든 재시도 후에도 세션 적용 실패: {last_error}")
            # 세션 오류 정보 저장
            self.status_manager.record_error(domain, str(last_error))

        return driver

    def with_session_retry(
        self,
        func: Callable,
        driver: WebDriver,
        domain: str,
        max_retries: int | None = None,
        **kwargs,
    ):
        """세션 재시도 메커니즘이 적용된 함수 실행 래퍼"""
        if max_retries is None:
            max_retries = self.retry_strategy.max_retries

        retries = 0
        delay = self.retry_strategy.initial_delay
        last_error = None

        while retries <= max_retries:
            try:
                # 세션 상태 확인 및 필요시 재설정
                if retries > 0:
                    logger.info(
                        f"함수 실행 재시도 {retries}/{max_retries}. 세션 재설정 시도..."
                    )
                    self.apply_cookies_and_session(driver, domain)

                # 실제 함수 실행
                result = func(driver=driver, **kwargs)

                # 성공 시 쿠키 저장
                self.save_cookies(
                    domain,
                    driver.get_cookies(),
                    driver.execute_script("return navigator.userAgent"),
                )

                return result

            except Exception as e:
                last_error = e
                retries += 1

                # 에러 로깅
                logger.warning(f"함수 실행 중 오류 발생 ({retries}/{max_retries}): {e}")

                if retries <= max_retries:
                    # 쿠키 초기화 및 세션 무효화
                    self.clear_cookies(domain)
                    self.status_manager.update_status(domain, "error_during_execution")

                    # 지수 백오프 적용
                    time.sleep(delay)
                    delay *= self.retry_strategy.backoff_factor
                else:
                    logger.error(f"최대 재시도 횟수 초과. 함수 실행 실패: {e}")
                    self.status_manager.record_error(domain, str(e))
                    raise

        if last_error:
            raise last_error

        return None

    def record_session(
        self, domain: str, session_data: dict[str, Any], duration_hours: int = 24
    ):
        """세션 정보 저장 (세션 ID, 토큰 등)"""
        self.storage.save("session", domain, session_data, int(duration_hours * 3600))

    def load_session(self, domain: str) -> dict[str, Any]:
        """세션 정보 로드"""
        return self.storage.load("session", domain)
