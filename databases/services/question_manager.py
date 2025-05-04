import json
from datetime import datetime

import redis


class QuestionManager:
    """
    질문 및 키워드를 Redis에 저장하고 관리하는 클래스.
    Redis를 사용하여 질문, 키워드, 그리고 크롤링 결과를 임시 저장합니다.
    """

    def __init__(self, redis_client: redis.Redis, prefix: str = "crawler") -> None:
        """
        QuestionManager 초기화

        Args:
            redis_client: Redis 클라이언트 인스턴스
            prefix: Redis 키 접두사 (기본값: "crawler")
        """
        self.redis = redis_client
        self.prefix = prefix

    def _build_key(self, key_type: str, identifier: str) -> str:
        """
        Redis 키 생성 헬퍼 메서드

        Args:
            key_type: 키 유형 (예: "question", "keyword")
            identifier: 고유 식별자 (예: 국가 코드, 도메인)

        Returns:
            형식화된 Redis 키
        """
        return f"{self.prefix}:{key_type}:{identifier}"

    def store_questions(
        self,
        questions: list[str],
        country_code: str,
        domain: str,
        expiry_hours: int = 24,
    ) -> int:
        """
        생성된 질문을 Redis에 저장

        Args:
            questions: 저장할 질문 목록
            country_code: 국가 코드 (예: "KR")
            domain: 도메인 (예: "Crypto")
            expiry_hours: 만료 시간(시간 단위)

        Returns:
            저장된 질문 수
        """
        key = self._build_key("questions", f"{country_code}:{domain}")
        # 기존 질문 삭제
        self.redis.delete(key)

        # 새 질문 저장
        timestamp = datetime.now().isoformat()
        count = 0

        for q in questions:
            question_data = json.dumps(
                {
                    "text": q,
                    "created_at": timestamp,
                    "country_code": country_code,
                    "domain": domain,
                    "crawled": False,
                }
            )
            self.redis.rpush(key, question_data)
            count += 1

        # 만료 시간 설정
        self.redis.expire(key, int(expiry_hours * 3600))
        return count

    def get_questions(
        self,
        country_code: str,
        domain: str,
        limit: int = 100,
        only_uncrawled: bool = True,
    ) -> list[dict]:
        """
        Redis에서 질문 검색

        Args:
            country_code: 국가 코드
            domain: 도메인
            limit: 반환할 최대 질문 수
            only_uncrawled: True인 경우 아직 크롤링되지 않은 질문만 반환

        Returns:
            질문 사전 목록
        """
        key = self._build_key("questions", f"{country_code}:{domain}")

        # 모든 질문 가져오기
        all_questions = []
        raw_questions = self.redis.lrange(key, 0, -1)

        for raw_q in raw_questions:
            try:
                q_data = json.loads(raw_q)
                # 아직 크롤링되지 않은 질문만 필터링(필요한 경우)
                if only_uncrawled and q_data.get("crawled", False):
                    continue
                all_questions.append(q_data)
            except json.JSONDecodeError:
                continue

            if len(all_questions) >= limit:
                break

        return all_questions

    def mark_question_crawled(
        self, question_text: str, country_code: str, domain: str
    ) -> bool:
        """
        질문을 크롤링 완료로 표시

        Args:
            question_text: 질문 텍스트
            country_code: 국가 코드
            domain: 도메인

        Returns:
            성공 여부
        """
        key = self._build_key("questions", f"{country_code}:{domain}")

        # 질문 찾기 및 업데이트
        idx = 0
        raw_questions = self.redis.lrange(key, 0, -1)

        for idx, raw_q in enumerate(raw_questions):
            try:
                q_data = json.loads(raw_q)
                if q_data["text"] == question_text:
                    # 크롤링 플래그 업데이트
                    q_data["crawled"] = True
                    q_data["crawled_at"] = datetime.now().isoformat()
                    self.redis.lset(key, idx, json.dumps(q_data))
                    return True
            except (json.JSONDecodeError, KeyError):
                continue

        return False

    def store_keywords(
        self, keywords: list[str], category: str, expiry_hours: int = 72
    ) -> int:
        """
        키워드를 Redis 집합에 저장

        Args:
            keywords: 키워드 목록
            category: 키워드 카테고리/유형
            expiry_hours: 만료 시간(시간 단위)

        Returns:
            새로 추가된 키워드 수
        """
        key = self._build_key("keywords", category)

        # 키워드를 세트에 추가
        added = 0
        for kw in keywords:
            if self.redis.sadd(key, kw) == 1:
                added += 1

        # 만료 시간 설정/갱신
        self.redis.expire(key, int(expiry_hours * 3600))
        return added

    def get_keywords(self, category: str) -> set[str]:
        """
        Redis에서 키워드 집합 검색

        Args:
            category: 키워드 카테고리/유형

        Returns:
            키워드 집합
        """
        key = self._build_key("keywords", category)

        # 바이트 문자열을 일반 문자열로 변환
        return {
            k.decode("utf-8") if isinstance(k, bytes) else k
            for k in self.redis.smembers(key)
        }

    def cache_crawl_result(
        self, query: str, source: str, results: list[dict], expiry_hours: int = 24
    ) -> bool:
        """
        크롤링 결과를 Redis에 캐싱

        Args:
            query: 검색 쿼리/질문
            source: 데이터 소스(예: "naver", "daum")
            results: 크롤링 결과 목록
            expiry_hours: 캐시 만료 시간(시간 단위)

        Returns:
            성공 여부
        """
        # 쿼리+소스 조합에 대한 고유 키 생성
        cache_key = self._build_key("cache", f"{source}:{hash(query)}")

        try:
            # 결과 저장
            self.redis.set(
                cache_key,
                json.dumps(
                    {
                        "query": query,
                        "source": source,
                        "results": results,
                        "cached_at": datetime.now().isoformat(),
                    }
                ),
            )

            # 만료 시간 설정
            self.redis.expire(cache_key, int(expiry_hours * 3600))
            return True
        except Exception as e:
            print(f"결과 캐싱 오류: {e}")
            return False

    def get_cached_result(self, query: str, source: str) -> list[dict] | None:
        """
        Redis에서 캐시된 크롤링 결과 검색

        Args:
            query: 검색 쿼리/질문
            source: 데이터 소스

        Returns:
            캐시된 결과 또는 None(캐시 미스)
        """
        cache_key = self._build_key("cache", f"{source}:{hash(query)}")

        # 캐시 확인
        cached = self.redis.get(cache_key)
        if not cached:
            return None

        try:
            data = json.loads(cached)
            return data.get("results")
        except json.JSONDecodeError:
            return None
