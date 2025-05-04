import logging
from selenium.webdriver.remote.webdriver import WebDriver

# 로깅 설정
logger = logging.getLogger("session.validator")


class SessionValidator:
    """세션 유효성 검증을 담당하는 클래스"""

    def __init__(self):
        self.block_indicators = [
            "access denied",
            "blocked",
            "captcha",
            "robot",
            "automated",
            "too many requests",
            "rate limit",
            "접근이 차단",
            "로봇",
        ]

    def validate(self, driver: WebDriver, url: str) -> bool:
        """세션 유효성 검증 - 페이지 접근 가능 여부 확인"""
        try:
            # 현재 URL 확인
            current_url = driver.current_url

            # 이미 해당 URL에 있으면 페이지 새로고침
            if current_url == url:
                driver.refresh()
            else:
                driver.get(url)

            # 페이지 로드 확인
            page_source = driver.page_source.lower()

            # 접근 차단/오류 키워드 확인
            for indicator in self.block_indicators:
                if indicator in page_source:
                    logger.warning(
                        f"세션 유효성 검증 실패: 차단 표시 발견 '{indicator}'"
                    )
                    return False

            # 정상 페이지로 판단
            return True

        except Exception as e:
            logger.error(f"세션 유효성 검증 중 오류 발생: {e}")
            return False
