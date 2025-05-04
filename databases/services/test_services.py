#!/usr/bin/env python
"""
키워드 생성기 및 질문 관리자 테스트 스크립트

이 스크립트는 BaseCountry와 QuestionManager 클래스를 테스트합니다.
실제 Redis 서버가 필요하며, 키워드 생성부터 질문 저장 및 결과 캐싱까지의
전체 흐름을 테스트합니다.
"""
import time
from pprint import pprint

# Redis 싱글톤 임포트
try:
    from databases.cache.redis_singleton import default_redis
except ImportError:
    print("Redis 싱글톤 모듈을 임포트할 수 없습니다.")
    import redis

    default_redis = type("DummyRedis", (), {"client": redis.Redis()})

from databases.services.keyword_generator import load_countries_from_yaml
from databases.services.question_manager import QuestionManager


def test_keyword_generator():
    """BaseCountry 클래스를 사용한 키워드 및 질문 생성 테스트"""
    print("\n===== 키워드 생성기 테스트 =====")

    # 테스트용 국가 정보 설정
    korea = load_countries_from_yaml()["KR"]

    # 키워드 조합 생성
    queries = korea.generate_search_queries()
    print(f"생성된 키워드 조합 수: {len(queries)}")
    print("샘플 키워드 조합:")
    for query in queries[:5]:  # 처음 5개만 출력
        print(f"  - {query[0]} + {query[1]}")

    # 질문 템플릿 적용
    questions = korea.apply_question_templates(queries)
    print(f"\n생성된 질문 수: {len(questions)}")
    print("샘플 질문:")
    sample_questions = list(questions)[:5]  # 처음 5개만 출력
    for q in sample_questions:
        print(f"  - {q}")

    return sample_questions


def test_question_manager(questions):
    """QuestionManager 클래스를 사용한 질문 관리 테스트"""
    print("\n===== 질문 관리자 테스트 =====")

    # Redis 클라이언트 및 질문 관리자 초기화
    redis_client = default_redis.client
    question_manager = QuestionManager(redis_client, prefix="test_crawler")

    # 질문 저장 테스트
    country_code = "KR"
    domain = "crypto"
    stored_count = question_manager.store_questions(
        questions, country_code, domain, expiry_hours=1
    )
    print(f"저장된 질문 수: {stored_count}")

    # 질문 조회 테스트
    retrieved_questions = question_manager.get_questions(country_code, domain, limit=10)
    print("\n조회된 질문:")
    for i, q in enumerate(retrieved_questions[:3], 1):  # 처음 3개만 출력
        print(f"  {i}. {q['text']}")

    # 질문 크롤링 완료 표시 테스트
    if retrieved_questions:
        first_question = retrieved_questions[0]["text"]
        marked = question_manager.mark_question_crawled(
            first_question, country_code, domain
        )
        print(f"\n첫 번째 질문 크롤링 완료 표시: {'성공' if marked else '실패'}")

    # 키워드 저장 테스트
    keywords = ["비트코인", "이더리움", "리플", "블록체인", "NFT", "DeFi"]
    added = question_manager.store_keywords(keywords, "crypto_terms")
    print(f"\n저장된 키워드 수: {added}")

    # 키워드 조회 테스트
    retrieved_keywords = question_manager.get_keywords("crypto_terms")
    print(f"조회된 키워드: {retrieved_keywords}")

    # 크롤링 결과 캐싱 테스트
    mock_results = [
        {"title": "비트코인 가격 전망 2023년", "url": "https://example.com/1"},
        {"title": "이더리움 투자 가이드", "url": "https://example.com/2"},
        {"title": "가상화폐 시장 분석", "url": "https://example.com/3"},
    ]
    query = "비트코인 투자 전략"
    source = "naver"

    cached = question_manager.cache_crawl_result(
        query, source, mock_results, expiry_hours=1
    )
    print(f"\n결과 캐싱: {'성공' if cached else '실패'}")

    # 캐시된 결과 조회 테스트
    time.sleep(1)  # 짧은 대기 시간
    cached_results = question_manager.get_cached_result(query, source)
    print("\n캐시된 크롤링 결과:")
    pprint(cached_results)

    return True


def cleanup_test_data():
    """테스트 데이터 정리"""
    print("\n===== 테스트 데이터 정리 =====")
    redis_client = default_redis.client

    # 테스트 키 삭제
    test_keys = redis_client.keys("test_crawler:*")
    if test_keys:
        redis_client.delete(*test_keys)
        print(f"{len(test_keys)}개의 테스트 키 삭제 완료")
    else:
        print("삭제할 테스트 키가 없습니다.")


def main():
    """메인 테스트 실행 함수"""
    print("\n키워드 생성 및 질문 관리 테스트 시작...")

    # 키워드 생성기 테스트
    questions = test_keyword_generator()

    # 질문 관리자 테스트
    if questions:
        test_question_manager(questions)

    # 테스트 데이터 정리
    cleanup_test_data()

    print("\n테스트 완료!")


if __name__ == "__main__":
    main()
