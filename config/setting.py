import random
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium_stealth import stealth
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from common.utils.logging_utils import EnhancedLogger
from dataclasses import dataclass, field
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

ua = UserAgent()
# xpath 와 셀레니움 관련 설정
PAGE_LOAD_DELEY = 2
WITH_TIME = 10
SCOROLL_ITERATION = 5
prefs = {
    "profile.default_content_setting_values": {
        "cookies": 2,
        "images": 2,
        "plugins": 2,
        "popups": 2,
        "geolocation": 2,
        "notifications": 2,
        "auto_select_certificate": 2,
        "fullscreen": 2,
        "mouselock": 2,
        "mixed_script": 2,
        "media_stream": 2,
        "media_stream_mic": 2,
        "media_stream_camera": 2,
        "protocol_handlers": 2,
        "ppapi_broker": 2,
        "automatic_downloads": 2,
        "midi_sysex": 2,
        "push_messaging": 2,
        "ssl_cert_decisions": 2,
        "metro_switch_to_desktop": 2,
        "protected_media_identifier": 2,
        "app_banner": 2,
        "site_engagement": 2,
        "durable_storage": 2,
    }
}


def chrome_option_setting(prefs: dict[str, dict[str, int]] = None) -> uc.Chrome:
    """
    크롬 드라이버 설정 및 초기화

    향상된 안티봇 기능을 포함한 크롬 드라이버 설정을 생성합니다.
    크롬 프로필을 사용하여 실제 사용자처럼 보이게 하고, 다양한 자동화 감지 회피 기법을 적용합니다.

    Args:
        prefs: 크롬 프로필 설정값 딕셔너리

    Returns:
        초기화된 undetected Chrome 드라이버 인스턴스
    """
    # 크롬 옵션 설정
    option_chrome = uc.ChromeOptions()

    # 기본 브라우저 설정
    option_chrome.add_argument("--disable-gpu")
    option_chrome.add_argument("--disable-infobars")
    option_chrome.add_argument("--disable-extensions")
    option_chrome.add_argument("--no-sandbox")
    option_chrome.add_argument("--disable-dev-shm-usage")
    option_chrome.add_argument("--disable-popup-blocking")

    # 자동화 감지 회피 설정 - undetected_chromedriver에서 지원하는 방식으로 변경
    option_chrome.add_argument("--disable-blink-features=AutomationControlled")
    # undetected_chromedriver와 호환되지 않는 옵션은 사용하지 않음
    # option_chrome.add_experimental_option("excludeSwitches", ["enable-automation"])
    # option_chrome.add_experimental_option("useAutomationExtension", False)

    # # 랜덤 User-Agent 설정
    # option_chrome.add_argument(f"--user-agent={ua.random}")

    # 캐시 관련 설정
    option_chrome.add_argument("--disable-application-cache")

    # 페이지 로딩 전략 설정
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"  # 안정성을 위해 normal 사용

    # prefs가 제공된 경우에만 설정
    if prefs is not None:
        option_chrome.add_experimental_option("prefs", prefs)

    # undetected_chromedriver 구성 (자동화 감지 회피 기능 내장)
    webdirver_chrome = uc.Chrome(
        options=option_chrome,
        incognito=False,  # 시크릿 모드 비활성화 (프로필 사용을 위해)
        headless=True,  # 헤드리스 모드 비활성화 (봇 감지 회피)
        service=Service(ChromeDriverManager().install()),
    )

    # 랜덤한 브라우저 지문(fingerprint) 설정
    navigator_platform = random.choice(["Win32", "MacIntel", "Linux x86_64"])
    vendor = random.choice(["Google Inc.", "Apple Computer, Inc."])
    renderer = random.choice(
        [
            "Intel Iris OpenGL Engine",
            "ANGLE (Intel, Mesa Intel(R) UHD Graphics 620 (CFL GT2), OpenGL 4.6)",
        ]
    )
    webgl_vendor = random.choice(["intel Inc.", "Apple Inc."])
    stealth(
        webdirver_chrome,
        languages=["ko-KR", "ko", "en-US", "en"],
        vendor=vendor,
        platform=navigator_platform,
        webgl_vendor=webgl_vendor,
        renderer=renderer,
        fix_hairline=True,
    )

    # JavaScript 실행하여 navigator.webdriver 속성 숨기기
    webdirver_chrome.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )

    return webdirver_chrome


@dataclass
class BasicAsyncNewsDataCrawling:
    target: str
    url: str
    home: str
    count: int | None = None
    header: dict[str, str] | None = None
    param: dict[str, str | int] | None = None
    logger: EnhancedLogger = field(init=False)

    def __post_init__(self) -> None:
        """EnhancedLogger 인스턴스 초기화"""
        self.logger = EnhancedLogger(
            name=self.home, log_level="INFO", file_name=f"{self.home}_crawling.log"
        )
