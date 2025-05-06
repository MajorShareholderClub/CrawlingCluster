"""
============================================================================================ test session starts =============================================================================================
platform darwin -- Python 3.12.10, pytest-8.3.5, pluggy-1.5.0 -- /Users/imhaneul/Documents/project/JuJuClub/CrawlingCluster/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/imhaneul/Documents/project/JuJuClub/CrawlingCluster
configfile: pyproject.toml
plugins: anyio-4.9.0, Faker-37.1.0
collected 1 item

sele_driver_test.py::test_google_search[chrome] PASSED                                                                                                                                                 [100%]

============================================================================================= 1 passed in 9.39s ==============================================================================================
"""

import pytest
from selenium import webdriver
import logging
import time

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@pytest.fixture(params=["chrome"], scope="function")
def get_browser(request):
    if request.param == "chrome":
        log.info("Chrome Driver 생성 시작")

        # 옵션 객체 생성 및 인자 넘겨주기
        options = webdriver.ChromeOptions()
        options.add_argument(
            "--user-data-dir=/Users/imhaneul/Library/Application Support/Google/Chrome/Default"
        )
        options.add_argument("--profile-directory=Default")

        # 자동화 감지 회피
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 드라이버 객체 생성
        driver = webdriver.Chrome(options=options)
        log.info("Chrome Driver 생성 완료")

        # JavaScript를 실행하여 navigator 객체 마스킹
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        # 테스트에서 드라이버 사용 후 종료
        yield driver

        # 테스트 종료 후 드라이버 정리
        log.info("Chrome Driver 종료")
        driver.quit()


def test_google_search(get_browser):
    """구글 검색 테스트 및 로봇 감지 회피 확인"""
    driver = get_browser
    try:
        # 구글 접속
        log.info("구글 접속 시도")
        driver.get("https://www.google.com")
        time.sleep(3)

        # 페이지 타이틀 확인
        assert "Google" in driver.title
        log.info(f"페이지 타이틀: {driver.title}")

        # 로봇 감지 페이지인지 확인
        if (
            "recaptcha" in driver.page_source.lower()
            or "captcha" in driver.page_source.lower()
        ):
            log.error("캡차 감지됨! 로봇으로 인식됨")
            assert False, "로봇으로 감지됨"
        else:
            log.info("캡차 감지되지 않음, 정상 페이지 표시")

        # 검색어 입력
        search_box = driver.find_element("name", "q")
        search_box.send_keys("Python selenium test")
        time.sleep(1)  # 자연스러운 타이핑 딜레이

        # 검색 실행
        search_box.submit()
        time.sleep(3)  # 결과 로딩 대기

        # 검색 결과 확인
        assert "Python" in driver.page_source
        log.info("검색 결과 페이지 로드 성공")

        # 다시 로봇 감지 페이지인지 확인
        if (
            "recaptcha" in driver.page_source.lower()
            or "captcha" in driver.page_source.lower()
        ):
            log.error("검색 후 캡차 감지됨! 로봇으로 인식됨")
            assert False, "검색 후 로봇으로 감지됨"
        else:
            log.info("검색 성공, 로봇 감지되지 않음")

    except Exception as e:
        log.error(f"테스트 중 오류 발생: {e}")
        assert False, f"테스트 실패: {e}"


if __name__ == "__main__":
    # pytest 실행
    pytest.main(["-v", __file__])
