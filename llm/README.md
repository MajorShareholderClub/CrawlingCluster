# LLM 디렉토리

## 개요
이 디렉토리는 CrawlingCluster 시스템에서 클러스터링된 데이터를 분석하고 키워드를 추출하기 위해 활용하는 대형 언어 모델(LLM) 관련 모듈을 포함합니다. OpenAI의 API를 활용하여 텍스트 분석, 키워드 추출, 특징지능 이상링크 픽업 등을 수행하는 기능을 제공합니다.

## 폴더 구조
```
llm/
├── keyword_extractor.py         # 키워드 추출 및 분석 기능
└── keyword_gener.py            # 키워드 생성 기능
```

## 모듈 설명

### keyword_extractor.py
- **기능**: LLM을 활용하여 텍스트에서 키워드를 추출하고 분석하는 기능
- **주요 클래스**:
  - `FunctionCallingMetaBuilder`: 함수 호출 메타데이터 생성 빌더 클래스
  - `LLMKeywordExtractor`: LLM을 사용하여 키워드를 추출하는 클래스

- **주요 기능**:
  - `async_calling_llm_gpt`: OpenAI API 비동기 호출 관리
  - `_get_keywords_prompt`: 키워드 추출 프롬프트 생성
  - `_get_evaluation_prompt`: 기사 평가 프롬프트 생성
  - `advanced_analysis`: Function Calling을 활용한 통합 분석

- **핵심 특징**:
  - Function Calling 기술 활용 (구조화된 응답 반환)
  - 비동기 호출 및 오류 처리
  - 프롬프트 추상화 및 모듈화

### keyword_gener.py
- **기능**: 새로운 키워드 생성 및 키워드 전략 관리
- **주요 기능**:
  - 화제/주제에 따른 키워드 생성
  - 현재 상황에 맞는 키워드 추천
  - 키워드 관련도 분석

## 사용 예시

### 기본 키워드 추출
```python
from llm.keyword_extractor import LLMKeywordExtractor
import asyncio

async def extract_keywords():
    extractor = LLMKeywordExtractor()
    article_text = "AI 기술의 발전으로 인해 더 많은 산업 분야에서 혁신이 일어나고 있습니다..."
    
    # 기본 키워드 추출
    keywords = await extractor.extract_keywords_from_article(article_text)
    print(f"Extracted keywords: {keywords}")

# 비동기 실행
asyncio.run(extract_keywords())
```

### Function Calling을 활용한 고급 분석
```python
from llm.keyword_extractor import LLMKeywordExtractor
import asyncio

async def analyze_article():
    extractor = LLMKeywordExtractor()
    article_text = "AI 기술의 발전으로 인해 더 많은 산업 분야에서 혁신이 일어나고 있습니다..."
    source = "tech_news.com"
    date = "2025-05-01"
    
    # 고급 분석 (키워드 추출, 평가, 요약, 엔티티 추출)
    result = await extractor.advanced_analysis(article_text, source, date)
    
    print(f"Keywords: {result['keywords']}")
    print(f"Evaluation: {result['evaluation']}")
    print(f"Summary: {result['summary']}")
    print(f"Entities: {result['entities']}")

# 비동기 실행
asyncio.run(analyze_article())
