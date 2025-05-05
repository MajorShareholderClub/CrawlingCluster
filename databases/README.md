# Databases 디렉토리

## 개요
이 디렉토리는 CrawlingCluster의 데이터베이스 연결 및 데이터 관리를 담당하는 모듈들을 포함합니다. MongoDB와 Redis를 사용하여 각각 영구 저장소와 캐시 저장소를 관리하며, 서비스와 세션 관리를 위한 다양한 기능을 제공합니다.

## 폴더 구조
```
databases/
├── cache/                       # Redis 캐시 관리 모듈
│   ├── redis_cluster_manager.py   # Redis 클러스터 관리
│   ├── redis_manager.py           # Redis 연결 및 작업 관리
│   └── redis_singleton.py         # Redis 단일 연결 싱글톤 패턴 구현
├── mongo/                       # MongoDB 데이터베이스 관리
│   ├── article_repository.py      # 기사 데이터 저장소
│   ├── keyword_repository.py      # 키워드 데이터 저장소
│   └── source_repository.py       # 출처 데이터 저장소
├── services/                     # 기타 데이터 관련 서비스
│   ├── data/                      # 정적 데이터 파일
│   │   ├── keyword.yaml            # 키워드 정의 데이터
│   │   └── keywords.csv            # CSV 형태의 키워드 목록
│   ├── keyword_generator.py       # 키워드 생성 서비스
│   ├── question_manager.py        # 질문 관리 서비스
│   └── test_services.py           # 서비스 테스트 코드
└── session/                      # 세션 관리
    ├── __init__.py
    ├── manager.py                 # 세션 관리 메인 코드
    ├── retry.py                   # 재시도 로직 관리
    ├── storage.py                 # 세션 저장소 관리
    └── validator.py              # 세션 데이터 유효성 검증
```

## 모듈 설명

### cache/

#### redis_singleton.py
- **기능**: Redis 연결을 싱글톤 패턴으로 관리
- **주요 기능**:
  - 단일 Redis 연결 인스턴스 관리
  - 연결 풀 관리
  - 자동 재연결 기능

#### redis_manager.py
- **기능**: Redis 데이터 조회 및 저장 함수 제공
- **주요 기능**:
  - 키-값 저장 및 조회
  - 리스트, 해시, 세트 데이터 구조 처리
  - 만료 시간 관리

#### redis_cluster_manager.py
- **기능**: Redis 클러스터 연결 및 관리
- **주요 기능**:
  - 다중 Redis 노드 관리
  - 샤딩 및 클러스터 이벤트 처리

### mongo/

#### article_repository.py
- **기능**: 크롤링된 기사 데이터 CRUD 작업
- **주요 기능**:
  - 기사 삽입, 업데이트, 조회, 삭제
  - 분석 결과 저장
  - 중복 검사 및 복합 쿼리

#### keyword_repository.py
- **기능**: 키워드 및 메타데이터 관리
- **주요 기능**:
  - 키워드 저장 및 조회
  - 키워드 비중 계산
  - 타겟 키워드 저장소

#### source_repository.py
- **기능**: 크롤링 소스 및 출처 정보 관리
- **주요 기능**:
  - 소스 등록 및 관리
  - 소스 신뢰도 점수 관리
  - 크롤링 상태 추적

### services/

#### keyword_generator.py
- **기능**: 키워드 생성 및 관리 서비스
- **주요 기능**:
  - 새로운 키워드 생성
  - 키워드 관련도 분석

#### question_manager.py
- **기능**: LLM 및 기타 서비스에 사용되는 질문 관리
- **주요 기능**:
  - 질문 템플릿 관리
  - 질문 생성 및 변환

### session/

#### manager.py
- **기능**: 세션 관리 역할
- **주요 기능**:
  - 데이터베이스 세션 관리
  - 세션 풀링 및 재사용

#### retry.py
- **기능**: 작업 재시도 로직
- **주요 기능**:
  - 재시도 전략 구현
  - 백오프 및 재연결 처리

#### storage.py
- **기능**: 세션 데이터 저장소
- **주요 기능**:
  - 세션 상태 저장 및 복원
  - 세션 만료 관리

#### validator.py
- **기능**: 세션 데이터 유효성 검증
- **주요 기능**:
  - 세션 데이터 검증
  - 에러 처리 및 유효성 검사

## 사용 예시

### Redis 캐시 사용
```python
from databases.cache.redis_singleton import RedisSingleton

# Redis 연결 가져오기
redis_client = RedisSingleton().get_client()

# 데이터 저장
redis_client.set("key", "value", ex=3600)  # 1시간 만료

# 데이터 조회
value = redis_client.get("key")
```

### MongoDB 저장소 사용
```python
from databases.mongo.article_repository import ArticleRepository

# 저장소 인스턴스 생성
repo = ArticleRepository()

# 기사 저장
article_id = repo.save_article({
    "title": "테스트 기사",
    "content": "테스트 내용",
    "source": "test.com",
    "keywords": ["AI", "크롤링"]
})

# 기사 조회
article = repo.find_by_id(article_id)
