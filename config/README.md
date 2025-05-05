# Config 디렉토리

## 개요
이 디렉토리는 CrawlingCluster 애플리케이션의 설정 파일들을 관리합니다. 크롤링 시스템이 사용하는 다양한 환경 설정, API 키, 데이터베이스 연결 정보 등의 구성 정보를 포함합니다.

## 폴더 구조
```
config/
├── cy/                     # 보안 관련 구성 정보 (credentials)
│   ├── database.yaml      # 데이터베이스 연결 설정
│   ├── url.conf           # URL 설정 정보
│   └── .env               # 환경 변수 및 API 키 (git에 포함되지 않음)
├── properties.py          # 시스템 속성 및 글로벌 설정
└── setting.py             # 애플리케이션 설정 관리
```

## 모듈 설명

### cy/database.yaml
- **기능**: MongoDB 및 Redis와 같은 데이터베이스 연결 정보 설정
- **사용법**: 데이터베이스 세션 매니저에서 자동으로 로드되어 연결 설정

### cy/url.conf
- **기능**: 크롤링 대상 URL 및 API 엔드포인트 설정
- **사용법**: 크롤러가 요청을 보낼 URL 목록 및 패턴 정의

### properties.py
- **기능**: 크롤링 시스템의 글로벌 속성 정의
- **주요 기능**:
  - 타임아웃, 재시도 횟수 등의 네트워크 파라미터 설정
  - 크롤링 간격 및 병렬 처리 수준 정의
  - 로깅 레벨 및 포맷 설정

### setting.py
- **기능**: 환경별(개발, 테스트, 운영) 설정 관리
- **주요 기능**:
  - 환경에 따른 설정값 로드
  - 설정 파일을 Python 객체로 변환
  - 설정 유효성 검증

## 사용 예시
```python
from config.setting import Settings

# 설정 로드
settings = Settings.load()

# 데이터베이스 연결 문자열 사용
db_uri = settings.database.mongo.uri
```
