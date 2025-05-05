from common.utils.logging_utils import EnhancedLogger
from config.setting import prefs
from databases.session.manager import SessionManager
from crawling.src.utils.search_util import ChromeDriver
from config.setting import chrome_option_setting


class SeleniumSessionManager:
    """셀레니움 드라이버와 세션 관리를 결합한 기반 클래스

    이 클래스는 셀레니움 웹 드라이버의 초기화와 세션 관리(쿠키 저장/로드)를
    자동화하여 블록 방지 및 효율적인 웹 크롤링을 지원합니다.
    """

    def __init__(self, domain: str, target: str, count: int):
        """셀레니움 세션 관리자 초기화

        Args:
            domain: 크롤링할 도메인 (예: 'google.com', 'investing.com')
            target: 검색 타겟 또는 크롤링 키워드
            count: 크롤링할 페이지 수
        """
        self.domain = domain
        self.target = target
        self.count = count

        # 로깅 설정
        self.logger = EnhancedLogger(
            name=f"selenium_{domain}", file_name=f"selenium_{domain}.log"
        )

        # 세션 관리자 초기화
        self.session_manager = SessionManager()

        # 드라이버 초기화는 하위 클래스에서 필요할 때 init_driver 호출
        self.driver: ChromeDriver | None = None

    def init_driver(self, custom_prefs=None, use_session: bool = True) -> ChromeDriver:
        """세션 관리 기능이 포함된 크롬 드라이버 초기화

        Args:
            custom_prefs: 사용자 정의 크롬 설정 (기본값: config.setting.prefs)
            use_session: 세션 재사용 여부 (기본값: True)

        Returns:
            초기화된 ChromeDriver 인스턴스
        """

        # 크롬 드라이버 기본 초기화
        chrome_prefs = custom_prefs if custom_prefs is not None else prefs
        self.driver = chrome_option_setting(chrome_prefs)

        if use_session:
            # 세션을 로드하여 쿠키 및 User-Agent 적용
            self.logger.info(f"{self.domain} 도메인에 대한 세션 로드 시도")
            try:
                self.driver = self.session_manager.apply_cookies_and_session(
                    self.driver, self.domain
                )
                self.logger.info(f"{self.domain} 세션 로드 성공")
            except Exception as e:
                self.logger.warning(
                    f"{self.domain} 세션 로드 실패: {e}. 새 세션으로 진행합니다."
                )

        return self.driver

    def save_session(self) -> None:
        """현재 브라우저 세션(쿠키)을 Redis에 저장"""
        if self.driver is None:
            self.logger.error("드라이버가 초기화되지 않아 세션을 저장할 수 없습니다.")
            return

        try:
            # 현재 쿠키와 User-Agent 저장
            cookies = self.driver.get_cookies()
            user_agent = self.driver.execute_script("return navigator.userAgent")

            self.session_manager.save_cookies(self.domain, cookies, user_agent)
            self.logger.info(f"{self.domain} 세션 저장 완료 (쿠키 {len(cookies)}개)")
        except Exception as e:
            self.logger.error(f"{self.domain} 세션 저장 실패: {e}")

    def close_driver(self) -> None:
        """드라이버 종료 및 세션 저장"""
        if self.driver is not None:
            # 세션 저장 후 드라이버 종료
            self.save_session()
            try:
                self.driver.quit()
                self.logger.info("웹 드라이버 정상 종료")
            except Exception as e:
                self.logger.warning(f"웹 드라이버 종료 중 오류: {e}")
            finally:
                self.driver = None

    def __del__(self):
        """소멸자에서 드라이버 정리"""
        self.close_driver()
