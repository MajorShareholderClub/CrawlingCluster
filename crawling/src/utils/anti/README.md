# 안티봇 시스템 (Anti-Robot System)

## 개요

이 모듈은 웹 크롤링 시 로봇 감지를 우회하기 위한 인간과 유사한 행동 패턴을 구현한 안티봇 시스템입니다. Single Responsibility Principle(단일 책임 원칙)에 따라 각 기능을 독립적인 컨트롤러로 분리하고, Facade 패턴을 사용하여 통합 관리합니다.

## 주요 구성 요소

### 컨트롤러

1. **MouseController** (`mouse_controller.py`)
   - 마우스 움직임, 클릭, 스크롤 등 자연스러운 마우스 동작 구현
   - 무작위 속도와 방향으로 마우스를 이동하여 봇이 아닌 인간의 행동 패턴 모방
   - `click_and_browse_then_back()` 메서드를 통해 요소 클릭, 읽기, 뒤로 가기 등의 복합 동작 제공

2. **TypingController** (`typing_controller.py`)
   - 인간처럼 자연스러운 타이핑 패턴 구현
   - 불규칙한 타이핑 속도와 오타 가능성을 포함한 현실적인 입력 방식 제공
   - 타이핑 속도, 지연 시간 등을 랜덤하게 적용하여 타이핑 패턴 다양화

3. **DelayController** (`delay_controller.py`)
   - 인간 행동을 모방하기 위한 지연 시간 관리
   - 웹 페이지 로딩, 콘텐츠 읽기, 생각하는 시간 등을 현실적으로 구현
   - 일관된 패턴을 피하기 위한 다양한 지연 시간 전략 제공

4. **RobotDetector** (`detector.py`)
   - 로봇 감지 페이지 확인 및 처리 로직
   - CAPTCHA, 로봇 확인 메시지 등 로봇 검사 페이지 감지
   - 봇 감지 우회를 위한 세션 관리 및 전략 구현

### 통합 클래스

1. **HumanLikeInteraction** (`human_like.py`)
   - Facade 패턴을 활용한 모든 컨트롤러의 통합 인터페이스
   - 컨트롤러 간 협력을 조정하여 일관된 사용자 경험 제공
   - 자연스러운 마우스 움직임, 타이핑, 페이지 스크롤 등 고수준 기능 제공

2. **AntiRobotSearch** (`human_like.py`)
   - 구글 검색 등을 위한 로봇 감지 우회 전용 기능 구현
   - 세션 재사용, 로그인 유지 등 다양한 안티봇 전략 적용
   - 검색, 뉴스 검색 등 특화된 기능 제공

## 사용 예제

```python
from selenium import webdriver
from crawling.src.utils.anti.human_like import HumanLikeInteraction, AntiRobotSearch

# 드라이버 초기화
driver = webdriver.Chrome()

# 안티봇 기능 인스턴스 생성
human_like = HumanLikeInteraction(driver)
anti_robot = AntiRobotSearch(driver)

# 구글 검색 예제
anti_robot.search_with_anti_robot("https://www.google.com", "비트코인 뉴스")

# 자연스러운 스크롤 및 읽기
human_like.natural_scroll_and_read()

# 마우스 무작위 움직임
human_like.random_mouse_movements()

# 특정 요소 인간처럼 클릭
element = driver.find_element(By.CSS_SELECTOR, ".some-button")
human_like.mouse_controller.click_element(element)
```

## 기술적 특징

- **타입 힌팅**: Python 3.12 스타일로 정적 타입 힌트 적용
- **예외 처리**: 모든 동작에 강력한 예외 처리 구현
- **로깅**: 상세한 정보를 제공하는 계층적 로깅 시스템
- **세션 관리**: 쿠키 및 세션 상태 유지를 통한 재사용성 향상
- **어댑터 패턴**: 다양한 웹사이트의 특성에 맞게 조정 가능한 유연한 설계

## 주의사항

- 웹사이트의 이용약관을 준수하여 사용하세요
- 과도한 크롤링은 웹 서버에 부담을 줄 수 있습니다
- 각 웹사이트마다 로봇 감지 메커니즘이 다를 수 있으므로 필요에 맞게 조정하세요
- 자동화된 브라우저 인스턴스는 기본 설정에서 환경 변수나 프록시 설정을 무시할 수 있습니다
