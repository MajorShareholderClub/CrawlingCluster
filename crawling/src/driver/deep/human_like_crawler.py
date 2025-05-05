import asyncio
import time
import random
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from crawling.src.utils.session_manager import SeleniumSessionManager
from crawling.src.driver.deep.relevant_crawler import RelevantAsyncWebCrawler
from crawling.src.core.types import UrlDictCollect


class HumanLikeAsyncWebCrawler(RelevantAsyncWebCrawler):
    """사람처럼 행동하는 비동기 웹 크롤러

    Selenium을 활용하여 사람처럼 행동하는 크롤러입니다.
    랜덤한 스크롤, 마우스 움직임, 지연 시간 등을 적용하여 봇 탐지를 우회합니다.
    세션 관리를 활용하여 쿠키와 세션을 유지합니다.

    Attributes:
        session_manager: 세션과 쿠키를 관리하는 객체
        driver: Selenium WebDriver 인스턴스
        custom_prefs: 브라우저 설정 매개변수
    """

    def __init__(
        self,
        start_url: str,
        max_pages: int,
        max_depth: int,
        keywords: list[str],
        relevance_threshold: float = 0.3,
        language: str = "english",
        custom_prefs: dict[str, Any] | None = None,
        domain: str = "",
    ) -> None:
        """생성자

        Args:
            start_url: 크롤링을 시작할 URL
            max_pages: 최대 크롤링할 페이지 수
            max_depth: 최대 탐색 깊이
            keywords: 관련성을 판단하는 데 사용될 키워드 목록
            relevance_threshold: 관련성 판단 임계값 (0-1 사이, 기본값: 0.3)
            language: NLTK 어휘 제거를 위한 언어 (기본값: 'english')
            custom_prefs: 드라이버 초기화를 위한 커스텀 설정
            domain: 세션 관리를 위한 도메인 이름
        """
        super().__init__(
            start_url, max_pages, max_depth, keywords, relevance_threshold, language
        )

        # 도메인이 지정되지 않은 경우 시작 URL에서 추출
        if not domain:
            domain = urlparse(start_url).netloc

        self.domain = domain
        self.custom_prefs = custom_prefs
        self.target = "deep_crawler"  # 크롤러 식별자

        # 세션 관리자 초기화
        self.session_manager = SeleniumSessionManager(
            self.domain, self.target, max_pages
        )
        self.driver: ChromeDriver | None = None

        # 방문 일정 관리를 위한 추가 변수
        self.last_visit_time: dict[str, float] = {}  # URL별 마지막 방문 시간
        self.min_visit_delay = 2.0  # 최소 방문 간격 (초)

    async def setup_driver(self) -> None:
        """드라이버 초기화

        드라이버가 없는 경우 새로 초기화합니다.
        """
        if not self.driver:
            self.driver = self.session_manager.init_driver(
                custom_prefs=self.custom_prefs, use_session=True
            )
            # 시간 초과 설정
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)

    async def close_driver(self) -> None:
        """드라이버 종료 및 세션 저장

        세션 관리자를 통해 드라이버를 안전하게 종료합니다.
        """
        if self.driver:
            # 세션 저장 후 드라이버 종료
            self.session_manager.close_driver()
            self.driver = None

    def human_like_scroll(self) -> None:
        """사람처럼 스크롤 동작 수행

        랜덤한 속도와 간격으로 스크롤하여 사람의 행동을 흉내냅니다.
        때로는 위로 스크롤하기도 합니다.
        """
        if not self.driver:
            return

        try:
            # 페이지 높이 가져오기
            total_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            # 랜덤한 간격으로 스크롤
            scroll_height = 0
            while scroll_height < total_height:
                # 랜덤한 스크롤 높이 (300-700px)
                scroll_step = random.randint(300, 700)
                scroll_height += scroll_step

                # 스크롤 다운
                self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")

                # 랜덤 딜레이 (0.5-2초)
                time.sleep(random.uniform(0.5, 2))

                # 가끔 약간 위로 스크롤 (사람같은 행동)
                if random.random() < 0.2:  # 20% 확률
                    back_scroll = random.randint(50, 200)
                    scroll_height -= back_scroll
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                    time.sleep(random.uniform(0.3, 1))
        except Exception as e:
            print(f"스크롤 오류: {e}")

    def random_mouse_movement(self) -> None:
        """랜덤한 마우스 움직임 (사람처럼 행동)

        랜덤하게 요소 위에 마우스를 올리거나 클릭하지 않고 호버링만 합니다.
        """
        if not self.driver:
            return

        try:
            if random.random() < 0.3:  # 30% 확률로 요소 위에 마우스 올리기
                # 랜덤한 링크 선택
                links = self.driver.find_elements(By.TAG_NAME, "a")
                if links:
                    random_link = random.choice(links)
                    ActionChains(self.driver).move_to_element(random_link).perform()
                    time.sleep(random.uniform(0.2, 1))
        except Exception as e:
            print(f"마우스 움직임 오류: {e}")

    async def get_page_with_selenium(self, url: str) -> str | None:
        """셀레니움을 사용하여 페이지 콘텐츠 가져오기

        사람처럼 행동하며 페이지를 로드하고 콘텐츠를 가져옵니다.

        Args:
            url: 가져올 페이지 URL

        Returns:
            페이지 콘텐츠 HTML 문자열 또는 오류 시 None
        """
        await self.setup_driver()

        # 마지막 방문 시간 확인 및 딜레이 적용
        current_time = time.time()
        if url in self.last_visit_time:
            time_since_last_visit = current_time - self.last_visit_time[url]
            if time_since_last_visit < self.min_visit_delay:
                # 최소 방문 간격 유지를 위한 딜레이
                await asyncio.sleep(self.min_visit_delay - time_since_last_visit)

        try:
            # 페이지 로드
            self.driver.get(url)

            # 페이지 로드 대기 (임의 시간)
            await asyncio.sleep(random.uniform(2, 5))

            # 사람처럼 스크롤
            self.human_like_scroll()

            # 랜덤 마우스 움직임
            self.random_mouse_movement()

            # 방문 시간 기록 업데이트
            self.last_visit_time[url] = time.time()

            # 페이지 콘텐츠 반환
            return self.driver.page_source
        except Exception as e:
            print(f"Selenium으로 페이지 로드 오류: {e}")
            return None

    async def crawl(self) -> None:
        """사람처럼 행동하는 크롤링 수행

        Selenium을 활용하여 사람처럼 행동하는 크롤링을 수행합니다.
        """
        await self.setup_driver()

        try:
            while (
                not self.url_queue.empty() and len(self.visited_urls) < self.max_pages
            ):
                current_url, depth = await self.url_queue.get()

                if current_url in self.visited_urls or depth > self.max_depth:
                    continue

                # URL 패턴 기반 필터링 (빠른 필터링)
                if not self.is_relevant_url(current_url) and depth > 0:
                    continue

                self.visited_urls.add(current_url)

                # 사람처럼 행동하기 위해 랜덤 지연
                await asyncio.sleep(random.uniform(1, 3))

                # Selenium으로 페이지 가져오기
                content = await self.get_page_with_selenium(current_url)

                if content:
                    # 콘텐츠 기반 필터링
                    soup = BeautifulSoup(content, "lxml")
                    title = soup.title.text if soup.title else ""

                    if (depth == 0) or self.is_relevant_content(content, title):
                        if depth < self.max_depth:
                            new_links, url_format = self.parse_links(
                                content, current_url
                            )
                            self.results[current_url] = url_format

                            # 가져온 링크들 무작위 셔플 (봇 패턴 방지)
                            new_links_list = list(new_links)
                            random.shuffle(new_links_list)

                            for link in new_links_list:
                                if link not in self.visited_urls:
                                    await self.url_queue.put((link, depth + 1))
        finally:
            # 크롤링 종료 시 드라이버 정리
            await self.close_driver()

    async def run(self, num_tasks: int = 1) -> dict[str, UrlDictCollect]:
        """크롤링 실행

        셀레니움을 사용하는 경우에는 하나의 태스크만 실행하는 것이 좋습니다.

        Args:
            num_tasks: 동시에 실행할 크롤링 태스크 수 (기본값: 1)

        Returns:
            results: 크롤링 결과 딕셔너리
        """
        tasks = [asyncio.create_task(self.crawl()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        return self.results
