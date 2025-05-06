import time
import random
import logging
from typing import List, Optional, Tuple

from selenium.webdriver.common.by import By
from common.utils.error_handling import SeleniumExceptionType
from crawling.src.core.types import ChromeDriver


class DelayController:
    """사람처럼 보이는 지연 행동을 시뮬레이션하는 클래스
    
    이 클래스는 페이지 스크롤, 콘텐츠 읽기, 로딩 대기 등 사람이 웹사이트와 상호작용할 때 자연스러운 지연을 제공합니다.
    """

    def __init__(self, driver: ChromeDriver) -> None:
        """지연 컨트롤러 초기화
        
        Args:
            driver: 셀레니움 웹드라이버 인스턴스
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)
    
    def smart_delay(self) -> float:
        """상황에 따라 지능적인 대기 시간 적용
        
        Returns:
            적용된 대기 시간(초)
        """
        # 페이지 복잡도에 따라 대기 시간 결정
        try:
            # 페이지의 콘텐츠 복잡도 추정 요소 수집
            total_elements = len(self.driver.find_elements(By.CSS_SELECTOR, "*"))
            images = len(self.driver.find_elements(By.TAG_NAME, "img"))
            links = len(self.driver.find_elements(By.TAG_NAME, "a"))
            
            # 복잡도 점수 계산 (0-100)
            complexity_score = min(100, (total_elements // 20) + (images // 5) + (links // 10))
            
            # 복잡도에 따라 기본 대기 시간 결정 (1-5초)
            base_delay = 1 + (complexity_score / 25)
            
            # 랜덤성 추가 (+/-30%)
            delay = base_delay * random.uniform(0.7, 1.3)
            
            self.logger.info(f"페이지 복잡도({complexity_score}/100)에 따라 {delay:.1f}초 대기")
            time.sleep(delay)
            return delay
            
        except SeleniumExceptionType as e:
            # 오류 발생 시 기본 랜덤 대기 적용
            fallback_delay = random.uniform(1.0, 3.0)
            self.logger.warning(f"지능적 대기 계산 중 오류, 기본값 {fallback_delay:.1f}초 사용: {e}")
            time.sleep(fallback_delay)
            return fallback_delay
    
    def natural_scroll(self, max_scrolls: int = 3) -> None:
        """사람처럼 자연스러운 스크롤 동작 시뮬레이션
        
        Args:
            max_scrolls: 최대 스크롤 수
        """
        try:
            # 페이지 길이 확인
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # 사용자 패턴에 따라 스크롤 개수 결정 (1-max_scrolls)
            actual_scrolls = random.randint(1, max_scrolls)
            
            # 페이지가 너무 짧으면 스크롤 수 조정
            if total_height <= viewport_height * 2:
                actual_scrolls = min(actual_scrolls, 1)
            
            self.logger.info(f"자연스러운 스크롤 시작 (${actual_scrolls}회)")
            
            current_position = 0
            for i in range(actual_scrolls):
                # 다음 스크롤 위치 계산 (한 화면 높이의 70-120% 사이)
                scroll_amount = int(viewport_height * random.uniform(0.7, 1.2))
                
                # 최대 스크롤 위치 제한
                next_position = min(current_position + scroll_amount, total_height - viewport_height)
                if next_position <= current_position:
                    break  # 더 이상 스크롤할 수 없음
                
                # 스크롤 실행
                self.driver.execute_script(f"window.scrollTo({{top: {next_position}, behavior: 'smooth'}})")                
                current_position = next_position
                
                # 스크롤 후 텍스트 확인 및 읽는 시간 시뮬레이션
                read_time = random.uniform(1.0, 4.0)  # 1-4초 동안 콘텐츠 확인
                self.logger.info(f"스크롤 {i+1}/{actual_scrolls} 후 {read_time:.1f}초 동안 콘텐츠 확인")
                time.sleep(read_time)
        
        except SeleniumExceptionType as e:
            self.logger.warning(f"자연스러운 스크롤 중 오류: {e}")
    
    def read_content_elements(self) -> None:
        """페이지의 콘텐츠 요소를 읽는 것처럼 시뮬레이션"""
        # 콘텐츠 요소 선택자 목록
        content_selectors = [
            "p", "article", ".content", "#content", ".post", ".article", ".news",
            "h1", "h2", "h3", ".headline", ".title"
        ]
        
        for selector in content_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    selected = elements[: min(3, len(elements))]  # 최대 3개 요소만 선택
                    for element in selected:
                        if element.is_displayed():
                            # 요소로 스크롤
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                            time.sleep(random.uniform(0.5, 1.0))
                            
                            # 텍스트 길이에 비례한 시간 동안 '읽기' 시뮬레이션
                            text_length = len(element.text)
                            if text_length > 0:
                                # 읽기 속도: 평균 200-300자/분 (3.3-5자/초)
                                read_time = min(
                                    text_length / random.uniform(3.3, 5.0), 10
                                )  # 최대 10초
                                self.logger.info(
                                    f"{text_length}자 분량의 텍스트를 {read_time:.1f}초 동안 읽는 중..."
                                )
                                time.sleep(read_time)
                            return  # 콘텐츠 요소를 찾았으면 반복 중단
            except SeleniumExceptionType as e:
                self.logger.warning(f"콘텐츠 요소 처리 중 오류: {e}")
                continue
    
    def wait_for_loading(self, selector: str, timeout: float = 10.0) -> bool:
        """특정 요소가 로드될 때까지 사람처럼 기다리기
        
        Args:
            selector: 기다릴 요소의 CSS 선택자
            timeout: 최대 대기 시간(초)
            
        Returns:
            요소 로드 성공 여부
        """
        start_time = time.time()
        check_interval = 0.5  # 0.5초마다 확인
        
        # 처음 몇 회는 짧게 확인
        initial_checks = [0.1, 0.2, 0.3]
        
        for delay in initial_checks:
            time.sleep(delay)
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].is_displayed():
                    elapsed = time.time() - start_time
                    self.logger.info(f"요소 {selector} 로드 완료 ({elapsed:.1f}초)")
                    return True
            except SeleniumExceptionType:
                pass
        
        # 로딩 중 동작 시뮬레이션 (50% 확률로 약간의 스크롤)
        if random.random() < 0.5:
            self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.2)")
        
        # 남은 시간 동안 일정 간격으로 확인
        while (time.time() - start_time) < timeout:
            time.sleep(check_interval)
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].is_displayed():
                    elapsed = time.time() - start_time
                    self.logger.info(f"요소 {selector} 로드 완료 ({elapsed:.1f}초)")
                    return True
            except SeleniumExceptionType:
                pass
        
        self.logger.warning(f"요소 {selector} 로드 시간 초과 ({timeout}초)")
        return False
    
    def natural_wait_with_activity(self, base_wait: float = 3.0, activity: bool = True) -> float:
        """사람이 상호작용하는 것처럼 기다리면서 간헐적 활동하기
        
        Args:
            base_wait: 기본 대기 시간(초)
            activity: 대기 중 활동 여부
            
        Returns:
            실제 대기 시간(초)
        """
        # 기본 대기 시간에 랜덤성 추가 (-20% ~ +30%)
        wait_time = base_wait * random.uniform(0.8, 1.3)
        
        if not activity:
            # 활동이 없는 경우 그냥 대기
            time.sleep(wait_time)
            return wait_time
        
        # 대기 시간을 작은 구간으로 나누어 활동 시뮬레이션
        segments = random.randint(2, 4)  # 2-4개 구간으로 나누기
        segment_duration = wait_time / segments
        
        for i in range(segments):
            # 각 구간마다 다른 동작 시뮬레이션
            segment_activity = random.choice(["scroll", "move", "wait"])
            
            if segment_activity == "scroll" and i != segments-1:  # 마지막 구간은 스크롤하지 않음
                # 약간의 스크롤
                scroll_amount = random.randint(50, 200) * random.choice([1, -1])
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
                self.logger.info(f"{segment_duration:.1f}초 대기 중 약간 스크롤 ({scroll_amount}px)")
            elif segment_activity == "move":
                # 마우스 약간 움직임
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    x_offset = random.randint(-50, 50)
                    y_offset = random.randint(-50, 50)
                    self.driver.execute_script(f"""
                        var event = new MouseEvent('mousemove', {{
                            'view': window,
                            'bubbles': true,
                            'cancelable': true,
                            'clientX': {x_offset},
                            'clientY': {y_offset}
                        }});
                        document.body.dispatchEvent(event);
                    """)
                except SeleniumExceptionType:
                    pass
            
            # 구간 대기 시간
            time.sleep(segment_duration)
        
        return wait_time
