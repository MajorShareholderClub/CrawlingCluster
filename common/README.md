# Common 디렉토리

## 개요
이 디렉토리는 CrawlingCluster 시스템 전체에서 공통적으로 사용되는 타입 정의, 유틸리티 함수, 공유 로직 등을 포함합니다. 코드의 재사용성을 높이고 일관된 구현을 보장하기 위한 핵심 컴포넌트들이 모여있습니다.

## 폴더 구조
```
common/
├── __init__.py
├── types/                        # 타입 정의 및 타입 힌트
│   ├── __init__.py
│   ├── _typing_crawling.py       # 크롤링 관련 타입 정의
│   ├── _typing_llm.py            # LLM 관련 타입 정의
│   └── type_aliases.py           # 타입 별칭 모음
└── utils/                        # 유틸리티 함수
    ├── __init__.py
    ├── error_handling.py         # 오류 처리 유틸리티
    └── logging_utils.py          # 로깅 유틸리티
```

## 모듈 설명

### types/

#### _typing_crawling.py
- **기능**: 크롤링 관련 타입 정의
- **주요 기능**:
  - 크롤링 결과 데이터 구조 정의
  - 웹페이지 파싱 관련 타입
  - 크롤링 설정 및 옵션 타입

#### _typing_llm.py
- **기능**: LLM 관련 타입 정의
- **주요 기능**:
  - `FunctionCallingMeta`: Function Calling 메타데이터 타입
  - `FunctionCallingParameter`: Function Calling 파라미터 타입
  - `FunctionParameter`: 함수 파라미터 정의 타입
  - `LLMComponent`: LLM 메시지 컴포넌트 타입

#### type_aliases.py
- **기능**: 자주 사용되는 타입에 대한 별칭 정의
- **주요 기능**:
  - 프로젝트 전반에서 일관되게 사용할 타입 별칭 제공
  - 복잡한 타입 구조 단순화

### utils/

#### error_handling.py
- **기능**: 오류 처리 및 예외 관리
- **주요 기능**:
  - 커스텀 예외 클래스
  - 오류 로깅 및 보고 기능
  - 리트라이 로직 구현

#### logging_utils.py
- **기능**: 로깅 유틸리티
- **주요 기능**:
  - 일관된 로그 포맷 제공
  - 로그 레벨 관리
  - 로그 파일 관리 및 로테이션

## 사용 예시

### 타입 정의 사용
```python
from common.types._typing_llm import FunctionCallingMeta, LLMComponent
from common.types._typing_crawling import CrawlResult

# LLM 컴포넌트 생성
message = LLMComponent(
    role="user",
    content="크롤링 결과를 분석해주세요."
)

# 크롤링 결과 타입 사용
def process_results(results: list[CrawlResult]) -> None:
    for result in results:
        print(f"URL: {result.url}, Title: {result.title}")
```

### 유틸리티 함수 사용
```python
from common.utils.logging_utils import get_logger
from common.utils.error_handling import retry_on_exception

# 로거 가져오기
logger = get_logger(__name__)

# 재시도 로직 사용
@retry_on_exception(max_retries=3, backoff_factor=1.5)
def fetch_data(url: str) -> dict:
    logger.info(f"Fetching data from {url}")
    # 데이터 가져오기 로직
    return {"status": "success", "data": "some data"}
```
