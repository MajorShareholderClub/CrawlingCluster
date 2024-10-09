# CrawlingCluster

## 프로젝트 목적
이 프로젝트는 다양한 뉴스 웹사이트에서 정보를 수집하고, 이를 효율적으로 관리 및 저장하기 위한 웹 크롤러입니다. 다양한 데이터 소스를 통해 최신 뉴스와 정보를 자동으로 수집하여 사용자에게 제공하는 것을 목표로 합니다.

### 개요

	•	크롤링: 여러 뉴스 사이트(예: Daum, Google, Investing 등)에서 정보를 수집합니다.
	•	데이터 처리: 수집된 데이터를 정제하고 필요한 형식으로 변환합니다.
	•	저장 및 활용: 처리된 데이터를 MongoDB와 같은 데이터베이스에 저장하여 쉽게 접근하고 활용할 수 있도록 합니다.

### 실행 방법 
```python3
poetry shell

python main.py
```

### 파일 구조 
```
📦 Project Root
├── 📜 README.md                       # 📄 프로젝트에 대한 전반적인 설명과 사용 방법을 담은 파일
├── 📂 config                          # 🗂️ 설정 관련 파일을 모아둔 디렉토리
├── 📂 crawling                        # 📡 크롤링 관련 코드와 리소스를 담고 있는 디렉토리
│   ├── 📂 config                     # 🛠️ 크롤링 설정 파일 모음
│   │   ├── 🐍 keywords.csv           # 키워드 목록을 담고 있는 CSV 파일
│   │   ├── 🐍 properties.py          # 크롤링 관련 기본 속성 및 설정 값 관리 모듈
│   │   ├── 🐍 setting.py             # 크롤링 설정 관련 모듈
│   │   └── 🐍 url.conf               # API 엔드포인트 URL 설정 파일
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
│       │   ├── 📂 daum               # 📅 다음 뉴스 관련 드라이버
│       │   │   ├── 🐍 daum_parsing.py  # 다음 뉴스 데이터 파싱 모듈
│       │   │   └── 🐍 daum_selenium.py  # Selenium을 이용한 다음 뉴스 크롤러
│       │   ├── 📂 google             # 🌐 구글 뉴스 관련 드라이버
│       │   │   ├── 🐍 google_parsing.py # 구글 뉴스 데이터 파싱 모듈
│       │   │   └── 🐍 google_selenium.py # Selenium을 이용한 구글 뉴스 크롤러
│       │   ├── 📂 investing           # 💰 Investing.com 관련 드라이버
│       │   │   ├── 🐍 investing_parsing.py # Investing.com 데이터 파싱 모듈
│       │   │   └── 🐍 investing_selenium.py # Selenium을 이용한 Investing.com 크롤러
│       │   ├── 🐍 news_parsing.py      # 일반 뉴스 데이터 파싱 모듈
│       │   └── 🐍 search.py            # 검색 관련 기능을 구현한 모듈
│       └── 📂 utils                  # 🛠️ 유틸리티 함수 모음
│           ├── 🐍 acquisition.py       # 데이터 수집 관련 유틸리티 함수
│           ├── 🐍 logger.py            # 로그 관리 모듈
│           ├── 🐍 parsing_util.py      # 데이터 파싱 관련 유틸리티 함수
│           └── 🐍 search_util.py       # 검색 관련 유틸리티 함수
├── 🐳 docker-compose.yml             # Docker 컴포즈 설정 파일
├── 📂 logs                           # 📝 로그 파일 디렉토리
├── 🐍 main.py                        # 메인 실행 스크립트
├── 🔧 poetry.lock                    # Poetry 패키지 종속성 관리 파일
├── 🔧 pyproject.toml                 # 프로젝트 메타데이터와 설정 파일
├── 🔧 requirements.txt               # 📝 Python 패키지 종속성 목록
└── 📂 tests                          # 🧪 테스트 코드 디렉토리
    └── 🐍 test_api_req.py            # API 요청 테스트 스크립트
```