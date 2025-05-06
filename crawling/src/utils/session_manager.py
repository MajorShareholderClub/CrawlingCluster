from common.utils.logging_utils import EnhancedLogger
from config.setting import prefs
from databases.session.manager import SessionManager
from crawling.src.utils.search_util import ChromeDriver
from config.setting import chrome_option_setting


class SeleniumSessionManager:
    """셀레니움 세션 매니저

    셀레니움을 이용한 크롤링 작업을 위한 세션 관리 클래스입니다.
    이 클래스는 크롤링 작업을 위한 셀레니움 드라이버를 초기화하고,
    세션을 저장하고 불러오는 기능을 제공합니다.
    """

    def __init__(self, domain: str, target: str, count: int) -> None:
        """셀레니움 세션 매니저 초기화

        Args:
            domain: 크롤링 대상 도메인 (예: 'google.com', 'investing.com')
            target: 크롤링 대상 URL
            count: 크롤링할 페이지 수
        """
        self.domain = domain
        self.target = target
        self.count = count

        # 로거 초기화
        self.logger = EnhancedLogger(
            name=f"selenium_{domain}", file_name=f"selenium_{domain}.log"
        )

        # 세션 매니저 초기화
        self.session_manager = SessionManager()

        # 셀레니움 드라이버 초기화
        self.driver: ChromeDriver | None = None

    def init_driver(self, custom_prefs=None, use_session: bool = True) -> ChromeDriver:
        """셀레니움 드라이버 초기화

        Args:
            custom_prefs: 사용자 정의된 크롬 환경 설정 (기본값: config.setting.prefs)
            use_session: 세션을 사용할지 여부 (기본값: True)

        Returns:
            초기화된 셀레니움 드라이버
        """

        # 사용자 정의된 크롬 환경 설정을 사용
        chrome_prefs = custom_prefs if custom_prefs is not None else prefs
        self.driver = chrome_option_setting(chrome_prefs)

        if use_session:
            # 세션을 사용하여 드라이버를 초기화
            self.logger.info(f"{self.domain} 도메인에 대한 세션을 초기화합니다.")
            try:
                # 세션 적용 시도
                self.driver = self.session_manager.apply_cookies_and_session(
                    self.driver, self.domain
                )
                self.logger.info(
                    f"{self.domain} 도메인에 대한 세션이 초기화되었습니다."
                )

                # 세션 적용 후 캡차 확인 - 세션이 무효화되었는지 검증
                self.driver.get(f"https://{self.domain}")
                self.driver.implicitly_wait(5)

                # 캡차 감지 확인
                from crawling.src.utils.anti_bot_utils import HumanLikeInteraction

                human_like = HumanLikeInteraction(self.driver)

                if human_like.is_robot_page():
                    self.logger.warning(
                        f"{self.domain} 세션이 캡차로 차단되었습니다. 세션을 삭제합니다."
                    )
                    # 세션이 캡차로 차단된 경우, 해당 세션을 Redis에서 삭제
                    self.session_manager.clear_cookies(self.domain)
                    # 세션 없이 드라이버 재생성
                    self.driver.quit()
                    self.driver = chrome_option_setting(chrome_prefs)
                    return self.driver

                # 정상적으로 세션 로드됨
                self.logger.info(
                    f"{self.domain} 도메인에 대한 세션이 유효함을 확인했습니다."
                )
            except Exception as e:
                self.logger.warning(
                    f"{self.domain} 도메인에 대한 세션 초기화 실패: {e}. 세션을 사용하지 않습니다."
                )

        return self.driver

    def delete_session(self) -> None:
        """현재 도메인의 세션을 삭제

        캡차가 감지되었거나 세션이 더 이상 유효하지 않을 때 호출합니다.
        """
        try:
            # 수정: delete_cookies -> clear_cookies
            self.session_manager.clear_cookies(self.domain)
            self.logger.info(f"{self.domain} 도메인에 대한 세션이 삭제되었습니다.")
        except Exception as e:
            self.logger.error(f"{self.domain} 도메인에 대한 세션 삭제 실패: {e}")

    def save_session(self) -> None:
        """현재 세션을 저장

        현재 셀레니움 드라이버의 세션을 저장합니다.
        """
        if self.driver is None:
            self.logger.error(
                "드라이버가 초기화되지 않았습니다. 세션을 저장할 수 없습니다."
            )
            return

        try:
            # 현재 세션의 쿠키와 User-Agent를 저장
            cookies = self.driver.get_cookies()
            user_agent = self.driver.execute_script("return navigator.userAgent")

            self.session_manager.save_cookies(self.domain, cookies, user_agent)
            self.logger.info(
                f"{self.domain} 도메인에 대한 세션이 저장되었습니다. ({len(cookies)}개의 쿠키)"
            )
        except Exception as e:
            self.logger.error(f"{self.domain} 도메인에 대한 세션 저장 실패: {e}")

    def save_cookies(self) -> None:
        """현재 도메인의 쿠키를 저장

        성공적으로 로그인하거나 캡차를 우회한 후 호출하여 세션을 저장합니다.
        """
        try:
            self.session_manager.save_cookies(self.driver, self.domain)
            self.logger.info(f"{self.domain} 도메인에 대한 쿠키가 저장되었습니다.")
        except Exception as e:
            self.logger.error(f"{self.domain} 도메인에 대한 세션 저장 실패: {e}")

    def close_driver(self) -> None:
        """셀레니움 드라이버를 종료

        현재 셀레니움 드라이버를 종료하고, 세션을 저장합니다.
        """
        if self.driver is not None:
            # 세션을 저장
            self.save_session()
            try:
                self.driver.quit()
                self.logger.info("셀레니움 드라이버가 종료되었습니다.")
            except Exception as e:
                self.logger.warning(f"셀레니움 드라이버 종료 실패: {e}")
            finally:
                self.driver = None

    def __del__(self):
        """셀레니움 드라이버를 종료

        이 클래스가 삭제될 때, 셀레니움 드라이버를 종료합니다.
        """
        self.close_driver()
