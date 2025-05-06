import logging
from typing import List, Optional

from selenium.webdriver.common.by import By
from common.utils.error_handling import SeleniumExceptionType
from crawling.src.core.types import ChromeDriver


class RobotDetector:
    """로봇 감지 페이지를 탐지하고 분석하는 클래스

    이 클래스는 CAPTCHA, reCAPTCHA 등 봇 감지 메커니즘을 탐지하는 메서드를 제공합니다.
    """

    def __init__(self, driver: ChromeDriver) -> None:
        """로봇 감지기 초기화

        Args:
            driver: 셀레니움 웹드라이버 인스턴스
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def is_robot_page(self) -> bool:
        """현재 페이지가 로봇 감지(CAPTCHA) 페이지인지 확인

        Returns:
            로봇 감지 페이지 여부
        """
        try:
            # 1. HTML 소스에서 명확한 캡차 관련 단어만 확인 (테스트 코드와 일치)
            page_source = self.driver.page_source.lower()
            clear_robot_indicators = [
                "captcha",
                "recaptcha",
                "hcaptcha",
                "bot detection",
                "unusual traffic",
                "비정상적인 트래픽",
                "자동화된 쿼리",
                "automated query",
            ]

            if any(indicator in page_source for indicator in clear_robot_indicators):
                self.logger.warning("HTML 소스에서 명확한 캡차/로봇 감지 발견!")
                return True

            # 2. 특정 캡차 요소 직접 확인 (더 정확한 선택자)
            captcha_selectors = [
                "#captcha",
                "#recaptcha",
                ".g-recaptcha",
                "iframe[title*='recaptcha']",
                "iframe[src*='recaptcha']",
                "iframe[src*='captcha']",
                "form[action*='challenge']",
            ]

            for selector in captcha_selectors:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    self.logger.warning(f"캡차 요소 발견: {selector}")
                    return True

            # 3. 구글 특화 - 캡차/로봇 관련 URL 확인
            current_url = self.driver.current_url.lower()
            if "captcha" in current_url or "challenge" in current_url:
                self.logger.warning(f"캡차/로봇 감지 URL 발견: {current_url}")
                return True

            # 4. 구문 컨텍스트를 고려한 텍스트 확인 (오탐지 가능성 감소)
            try:
                # 정확한 캡차 관련 문구가 포함된 요소 찾기
                robot_phrases = [
                    "please verify you are a human",
                    "i'm not a robot",
                    "자동화된 요청으로부터",
                    "보안 확인",
                    "security check",
                    "automated system",
                ]

                # body 전체 텍스트가 아닌 중요 요소만 검색
                important_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "#main, #center_col, #captcha-form, #challenge-form, .error-code",
                )

                for element in important_elements:
                    element_text = element.text.lower()
                    if any(phrase in element_text for phrase in robot_phrases):
                        self.logger.warning(
                            f"로봇 감지 문구 발견: {element_text[:50]}..."
                        )
                        return True
            except:
                # 요소 찾기 실패시 무시
                pass

            # 로봇 감지 없음
            return False

        except SeleniumExceptionType as e:
            self.logger.warning(f"로봇 페이지 확인 중 오류 발생: {e}")
            return False

    def get_detected_type(self) -> Optional[str]:
        """감지된 로봇 방지 메커니즘의 종류 확인

        Returns:
            감지된 타입 (recaptcha, captcha, hcaptcha 등) 또는 None
        """
        try:
            # reCAPTCHA 확인
            if self.driver.find_elements(
                By.CSS_SELECTOR,
                ".g-recaptcha, iframe[title*='recaptcha'], iframe[src*='recaptcha']",
            ):
                return "recaptcha"

            # hCaptcha 확인
            if self.driver.find_elements(
                By.CSS_SELECTOR,
                ".h-captcha, iframe[title*='hcaptcha'], iframe[src*='hcaptcha']",
            ):
                return "hcaptcha"

            # 일반 CAPTCHA 확인
            if self.driver.find_elements(
                By.CSS_SELECTOR, "#captcha, form[action*='captcha']"
            ):
                return "captcha"

            # IP 기반 차단 또는 일반 로봇 감지 페이지
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if "unusual traffic" in page_text or "비정상적인 트래픽" in page_text:
                return "ip_block"

            # 감지되었지만 종류는 알 수 없음
            if self.is_robot_page():
                return "unknown"

            return None

        except SeleniumExceptionType as e:
            self.logger.warning(f"로봇 감지 타입 확인 중 오류: {e}")
            return None

    def mask_navigator(self) -> None:
        """자바스크립트를 사용하여 Navigator 속성 마스킹 (봇 감지 방지)"""
        # Navigator 객체 속성 마스킹을 통한 자동화 탐지 회피
        script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        """
        try:
            self.driver.execute_script(script)
            self.logger.info("Navigator 속성 마스킹 완료")
        except SeleniumExceptionType as e:
            self.logger.error(f"Navigator 마스킹 실패: {e}")
