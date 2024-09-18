import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium_stealth import stealth

# from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


ua = UserAgent()
# xpath 와 셀레니움 관련 설정
PAGE_LOAD_DELEY = 2
WITH_TIME = 5
SCORLL_ITERATION = 5


def chrome_option_setting() -> uc.Chrome:
    option_chrome = uc.ChromeOptions()
    option_chrome.add_argument("headless")
    option_chrome.add_argument("--disable-gpu")
    option_chrome.add_argument("--disable-infobars")
    option_chrome.add_argument("--disable-extensions")
    option_chrome.add_argument("--no-sandbox")
    option_chrome.add_argument("--disable-dev-shm-usage")
    option_chrome.add_argument("--disable-logging")  # 로깅 비활성화

    option_chrome.add_argument(f"user-agent={ua.random}")

    caps = DesiredCapabilities().CHROME

    # page loading 없애기
    caps["pageLoadStrategy"] = "none"

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
    option_chrome.add_experimental_option("prefs", prefs)
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService

    webdirver_chrome = uc.Chrome(
        options=option_chrome,
        enable_cdp_events=True,
        incognito=True,
        service=ChromeDriverManager(driver_version="129.0.6668.58").install(),
    )

    stealth(
        webdirver_chrome,
        vendor="Google Inc. ",
        platform="Win32",
        webgl_vendor="intel Inc. ",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return webdirver_chrome
