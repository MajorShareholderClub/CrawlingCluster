# CrawlingCluster

## 프로젝트 목적
이 프로젝트는 다양한 뉴스 웹사이트에서 정보를 수집하고, 이를 효율적으로 관리 및 저장하기 위한 웹 크롤러입니다. 다양한 데이터 소스를 통해 최신 뉴스와 정보를 자동으로 수집하여 사용자에게 제공하는 것을 목표로 합니다.

### 개요

- 크롤링: 여러 뉴스 사이트(예: Google, Investing 등)에서 정보를 수집합니다.
- 안티봇 기능: 로봇 감지를 우회하는 인간형 패턴 모방 시스템을 구현하여 안정적인 크롤링을 수행합니다.
- 데이터 처리: 수집된 데이터를 정제하고 필요한 형식으로 변환합니다.
- 저장 및 활용: 처리된 데이터를 MongoDB와 같은 데이터베이스에 저장하여 쉽게 접근하고 활용할 수 있도록 합니다.
- 세션 관리: Redis를 통한 브라우저 세션 관리로 크롤링 효율성을 높입니다.

### 실행 방법 
```bash
# 환경 설정
poetry shell

# 프로그램 실행
python main.py

# 간단한 테스트 실행
python test_simple.py
```

### 파일 구조 
```
📦 Project Root
├── 📜 README.md                       # 📄 프로젝트에 대한 전반적인 설명과 사용 방법을 담은 파일
├── 📂 common                          # 🗂️ 공통 모듈
│   ├── 📂 types                      # 🏷️ 공통 타입 정의
│   └── 📂 utils                      # 🛠️ 유틸리티 함수
│       └── 🐍 error_handling.py      # 오류 처리 유틸리티
├── 📂 config                          # 🗂️ 설정 관련 파일을 모아둔 디렉토리
│   ├── 📂 cy                         # 사이프레스 설정
│   └── 🐍 setting.py                 # 전역 설정 및 크롬 드라이버 설정
├── 📂 crawling                        # 📡 크롤링 관련 코드와 리소스를 담고 있는 디렉토리
│   ├── 📂 config                     # 🛠️ 크롤링 설정 파일 모음
│   │   ├── 📜 keywords.csv           # 키워드 목록을 담고 있는 CSV 파일
│   │   ├── 🐍 properties.py          # 크롤링 관련 기본 속성 및 설정 값 관리 모듈
│   │   └── ⚙️ url.conf               # API 엔드포인트 URL 설정 파일 (숨김)
│   └── 📂 src                        # 🚀 크롤링 소스 코드
│       ├── 📂 core                   # ⚙️ 크롤링의 핵심 로직 및 구조
│       │   ├── 📂 abstract           # 📝 추상화된 클래스들을 모아둔 하위 디렉토리
│       │   │   └── 🐍 abstract_async_request.py  # 비동기 요청을 추상화한 클래스
│       │   ├── 📂 database           # 💾 데이터베이스 관련 모듈
│       │   │   └── 🐍 async_mongo.py  # 비동기 MongoDB 관련 모듈
│       │   ├── 📂 stubs              # 🛠️ 타입 힌트를 위한 스텁 파일
│       │   │   ├── 🐍 acquistion.pyi  # 데이터 수집 관련 스텁
│       │   │   └── 🐍 logger.pyi      # 로깅 관련 스텁
│       │   └── 📂 types              # 🗂️ 공통 데이터 타입 정의 모듈
│       │       ├── 🐍 __init__.py     # 타입 모듈 초기화 파일
│       │       └── 🐍 _typing.py      # 타입 힌트 정의 파일
│       ├── 📂 driver                 # 🐍 다양한 크롤링 드라이버 구현
│       │   ├── 🐍 __init__.py         # 드라이버 모듈 초기화 파일
│       │   ├── 📂 api_req            # 📡 API 요청 관련 드라이버
│       │   │   └── 🐍 api_news_driver.py # 뉴스 API 요청 드라이버
│       │   ├── 📂 google             # 🌐 구글 뉴스 관련 드라이버
│       │   │   ├── 🐍 google_parsing.py # 구글 뉴스 데이터 파싱 모듈
│       │   │   └── 🐍 google_selenium.py # Selenium을 이용한 구글 뉴스 크롤러
│       │   ├── 📂 investing           # 💰 Investing.com 관련 드라이버
│       │   │   ├── 🐍 investing_parsing.py # Investing.com 데이터 파싱 모듈
│       │   │   └── 🐍 investing_selenium.py # Selenium을 이용한 Investing.com 크롤러
│       │   ├── 🐍 news_parsing.py      # 일반 뉴스 데이터 파싱 모듈
│       │   └── 🐍 search.py            # 검색 관련 기능을 구현한 모듈
│       └── 📂 utils                  # 🛠️ 유틸리티 함수 모음
│           ├── 📂 anti               # 🛡️ 안티봇 시스템 모듈
│           │   ├── 🐍 __init__.py     # 모듈 초기화 파일
│           │   ├── 🐍 delay_controller.py # 지연 제어 모듈
│           │   ├── 🐍 detector.py     # 로봇 감지 탐지 모듈
│           │   ├── 🐍 human_like.py   # 인간형 상호작용 클래스
│           │   ├── 🐍 mouse_controller.py # 마우스 제어 모듈
│           │   ├── 🐍 typing_controller.py # 타이핑 제어 모듈
│           │   └── 📜 README.md      # 안티봇 시스템 설명서
│           ├── 🐍 acquisition.py       # 데이터 수집 관련 유틸리티 함수
│           ├── 🐍 anti_bot_utils.py    # 안티봇 유틸리티 함수
│           ├── 🐍 logger.py            # 로그 관리 모듈
│           ├── 🐍 parsing_util.py      # 데이터 파싱 관련 유틸리티 함수
│           ├── 🐍 search_util.py       # 검색 관련 유틸리티 함수
│           └── 🐍 session_manager.py   # 세션 관리 모듈
├── 📂 databases                       # 💾 데이터베이스 관련 모듈
│   ├── 📂 cache                      # 캐시 관련 모듈
│   ├── 📂 mongo                      # MongoDB 관련 모듈
│   ├── 📂 services                   # 데이터 서비스 모듈
│   │   └── 📂 data                   # 데이터 처리 서비스
│   └── 📂 session                    # 세션 관리 모듈
├── 📂 llm                            # 🧠 LLM 관련 모듈
│   ├── 📜 README.md                   # LLM 모듈 설명서
│   ├── 🐍 keyword_extractor.py        # 키워드 추출 모듈
│   ├── 🐍 keyword_gener.py            # 키워드 생성기 모듈
│   └── 🐍 query_generator.py          # 쿼리 생성기 모듈
├── 🐳 docker-compose.yml             # 도커 컴포즈 설정 파일
├── 📂 logs                           # 📝 로그 파일 디렉토리
├── 🐍 main.py                        # 메인 실행 스크립트
├── 🔧 poetry.lock                    # Poetry 패키지 종속성 관리 파일
├── 🔧 pyproject.toml                 # 프로젝트 메타데이터와 설정 파일
├── 🔧 requirements.txt               # 📝 Python 패키지 종속성 목록
├── 🐍 test_simple.py                 # 간단한 테스트 스크립트
├── 📂 tests                          # 🧪 테스트 코드 디렉토리
│   ├── 🐍 test_api_req.py            # API 요청 테스트 스크립트
│   └── 🐍 sele_driver_test.py        # 셀레니움 드라이버 테스트 스크립트

```

## 주요 기능

### 1. 안티봇 시스템

최신 웹 크롤링 방지 기술을 우회하기 위한 고급 안티봇 시스템을 구현했습니다. 인간의 행동 패턴을 모방하여 로봇 감지를 효과적으로 회피합니다.

- **단일 책임 원칙(SRP)** 기반의 모듈화된 설계
- **마우스/키보드 제어**, **지연 시간 조절**, **로봇 감지 회피** 등 세분화된 컨트롤러
- **Facade 패턴**을 적용한 HumanLikeInteraction 클래스로 통합 인터페이스 제공

### 2. 다중 소스 크롤링

다양한 뉴스 사이트에서 효율적으로 데이터를 수집할 수 있는 유연한 크롤링 아키텍처를 제공합니다.

- **구글 뉴스**: 인공지능 기술 및 비트코인 관련 최신 뉴스 수집
- **Investing.com**: 금융 및 투자 관련 뉴스 및 데이터 수집

### 3. 세션 관리 및 캐싱

Redis를 활용한 세션 관리 시스템을 통해 크롤링 효율성을 높이고, 불필요한 재요청을 방지합니다.

### 4. 비동기 데이터 처리

asyncio를 활용한 비동기 처리로 크롤링 및 데이터 처리 성능을 최적화했습니다.

## 기술 스택

- **언어**: Python 3.12+
- **웹 자동화**: Selenium, undetected-chromedriver
- **데이터베이스**: MongoDB, Redis
- **비동기 처리**: asyncio
- **기타 라이브러리**: BeautifulSoup4, requests, aiohttp