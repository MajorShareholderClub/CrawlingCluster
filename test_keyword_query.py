import asyncio


from databases.services.keyword_generator import load_countries_from_yaml
from databases.services.question_manager import QuestionManager
from databases.cache.redis_singleton import RedisSingleton


async def generate_and_store_investing_keywords():
    """
    investing.com용 키워드 생성 및 Redis 저장
    """
    # 국가 데이터 로드
    countries = load_countries_from_yaml()

    # Redis 클라이언트 초기화
    redis_client = RedisSingleton().client
    question_manager = QuestionManager(redis_client)

    # 금융 관련 키워드 추출 (영어)
    en_finance = countries.get("EN")
    if not en_finance:
        print("영어 금융 데이터를 찾을 수 없습니다.")
        return

    # investing.com용 코어 키워드 추출
    investing_keywords = en_finance.core_keywords

    # Redis에 키워드 저장 (investing 카테고리로)
    count = question_manager.store_keywords(investing_keywords, "investing", 24)
    print(f"investing.com용 키워드 {count}개 저장 완료")
    print(f"키워드: {investing_keywords}")

    # 저장된 키워드 검증
    stored_keywords = question_manager.get_keywords("investing")
    print(f"Redis에 저장된 키워드 {len(stored_keywords)}개: {stored_keywords}")

    return investing_keywords


async def generate_and_store_google_queries():
    """
    Google 검색용 질의어 생성 및 Redis 저장
    """
    # 국가 데이터 로드
    countries = load_countries_from_yaml()

    # Redis 클라이언트 초기화
    redis_client = RedisSingleton().client
    question_manager = QuestionManager(redis_client)

    # 한국어 및 영어 금융 데이터 사용
    kr_finance = countries.get("KR")
    en_finance = countries.get("EN")

    all_queries = []

    # 한국어 질의어 생성
    if kr_finance:
        # 키워드 조합 생성
        kr_queries = kr_finance.generate_search_queries()
        # 템플릿 적용
        kr_questions = kr_finance.apply_question_templates(kr_queries)

        # Redis에 저장
        kr_count = question_manager.store_questions(
            list(kr_questions), country_code="KR", domain="Finance", expiry_hours=24
        )

        print(f"한국어 질의어 {kr_count}개 생성 및 저장 완료")
        all_queries.extend(kr_questions)

    # 영어 질의어 생성
    if en_finance:
        # 키워드 조합 생성
        en_queries = en_finance.generate_search_queries()
        # 템플릿 적용
        en_questions = en_finance.apply_question_templates(en_queries)

        # Redis에 저장
        en_count = question_manager.store_questions(
            list(en_questions), country_code="EN", domain="Finance", expiry_hours=24
        )

        print(f"영어 질의어 {en_count}개 생성 및 저장 완료")
        all_queries.extend(en_questions)

    # 생성된 질의어 샘플 출력
    sample_size = min(10, len(all_queries))
    print(f"\n=== 생성된 질의어 샘플({sample_size}개) ===")
    for idx, query in enumerate(list(all_queries)[:sample_size], 1):
        print(f"{idx}. {query}")

    # Google 검색용 키워드로 저장
    question_manager.store_keywords(list(all_queries), "google", 24)

    return all_queries


async def retrieve_and_print_data():
    """
    Redis에 저장된 데이터 조회 및 출력
    """
    # Redis 클라이언트 초기화
    redis_client = RedisSingleton().client
    question_manager = QuestionManager(redis_client)

    # Investing 키워드 조회
    investing_keywords = question_manager.get_keywords("investing")
    print(f"\n=== Investing.com 키워드({len(investing_keywords)}개) ===")
    for idx, kw in enumerate(investing_keywords, 1):
        print(f"{idx}. {kw}")

    # Google 질의어 조회
    google_queries = question_manager.get_keywords("google")
    print(f"\n=== Google 질의어({len(google_queries)}개) ===")
    samples = list(google_queries)[:10]  # 처음 10개만 출력
    for idx, query in enumerate(samples, 1):
        print(f"{idx}. {query}")

    # 질문 데이터 조회
    kr_questions = question_manager.get_questions("KR", "Finance", limit=5)
    en_questions = question_manager.get_questions("EN", "Finance", limit=5)

    print(f"\n=== 한국어 질문 데이터({len(kr_questions)}개) ===")
    for idx, q in enumerate(kr_questions, 1):
        print(f"{idx}. {q['text']}")

    print(f"\n=== 영어 질문 데이터({len(en_questions)}개) ===")
    for idx, q in enumerate(en_questions, 1):
        print(f"{idx}. {q['text']}")


async def main():
    # 1. Investing.com용 키워드 생성 및 저장
    print("\n=== Investing.com용 키워드 생성 및 저장 시작 ===\n")
    await generate_and_store_investing_keywords()

    # 2. Google 검색용 질의어 생성 및 저장
    print("\n=== Google 검색용 질의어 생성 및 저장 시작 ===\n")
    await generate_and_store_google_queries()

    # 3. Redis에 저장된 데이터 조회 및 출력
    print("\n=== Redis에 저장된 데이터 조회 ===\n")
    await retrieve_and_print_data()


if __name__ == "__main__":
    asyncio.run(main())
