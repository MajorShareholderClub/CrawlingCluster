import logging
from typing import TypedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime

from databases.services.keyword_generator import BaseCountry, load_countries_from_yaml
from common.utils.error_handling import handle_redis_exceptions


# 상수 정의
REDIS_EXPIRY_DAYS = 30
REDIS_EXPIRY_SECONDS = 60 * 60 * 24 * REDIS_EXPIRY_DAYS
KEYWORD_TYPES = ("core_keywords", "context_keywords")

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class KeywordSet:
    """키워드 세트 데이터 클래스"""

    core_keywords: list[str] = field(default_factory=list)
    context_keywords: list[str] = field(default_factory=list)


class RedisTemplateInfo(TypedDict):
    """Redis 템플릿 정보 타입"""

    core_keyword: str
    context_keyword: str


TemplateInfo = list[str]


class KeywordGenerator:
    """키워드 생성 및 관리 클래스"""

    def __init__(self, country_code: str, redis_client=None) -> None:
        """KeywordGenerator 초기화

        Args:
            country_code: 국가 코드
            redis_client: Redis 클라이언트 (None일 경우 자동 생성)
        """
        # Redis 클라이언트 설정 - 싱글 인스턴스 사용
        import redis

        self.redis_client = redis_client or redis.Redis(
            host="127.0.0.1",  # 기본 설정
            port=7001,  # writer 노드 포트
            db=0,  # 기본 DB 번호
            decode_responses=True,
        )

        self.country_code = country_code
        self.countries: dict[str, BaseCountry] = load_countries_from_yaml()
        self.country: BaseCountry = self.countries[country_code]
        self.base_key: str = country_code

    def _build_key(self, category: str, date: str | None = None) -> str:
        """Redis 키 생성

        Args:
            category: 키워드 카테고리
            date: 날짜 (None일 경우 기본 키 사용)

        Returns:
            생성된 Redis 키
        """
        key_type = f"crawled:{date}" if date else "default"
        return f"{self.base_key}:{key_type}:{category}"

    @handle_redis_exceptions
    def _save_keywords(
        self, key: str, keywords: list[str], expire: bool = False
    ) -> None:
        """키워드 저장

        Args:
            key: 저장할 키
            keywords: 저장할 키워드 목록
            expire: 만료 설정 여부
        """
        if not keywords:
            return

        # 키워드 저장
        self.redis_client.delete(key)  # 기존 키 삭제
        self.redis_client.sadd(key, *keywords)  # 새 키워드 세트 추가

        # 만료 설정
        if expire:
            self.redis_client.expire(key, REDIS_EXPIRY_SECONDS)

    def save_redis_keywords(
        self,
        date: str | None = None,
        core_keywords: list[str] | None = None,
        context_keywords: list[str] | None = None,
    ) -> None:
        """키워드 저장

        Args:
            date: 저장할 날짜 (None일 경우 기본 키에 저장)
            core_keywords: 핵심 키워드 목록
            context_keywords: 컨텍스트 키워드 목록
        """
        logger.info(
            f"Saving {'crawled' if date else 'default'} keywords for country: {self.country_code}"
        )

        # 제공된 키워드 또는 기본 키워드 사용
        keyword_set = KeywordSet(
            core_keywords=core_keywords or self.country.core_keywords,
            context_keywords=context_keywords or self.country.context_keywords,
        )

        # 각 카테고리별 키워드 저장
        for category, keywords in asdict(keyword_set).items():
            self._save_keywords(
                key=self._build_key(category, date),
                keywords=keywords,
                expire=bool(date),
            )

    def _get_keywords_by_key(self, key: str) -> list[str]:
        """Redis 키로부터 키워드 가져오기

        Args:
            key: Redis 키

        Returns:
            키워드 목록
        """
        return list(self.redis_client.smembers(key))

    def get_keywords(self, date: str | None = None) -> tuple[list[str], list[str]]:
        """키워드 조회

        Args:
            date: 조회할 날짜 (None일 경우 기본 키에서 조회)

        Returns:
            (핵심 키워드 목록, 컨텍스트 키워드 목록) 튜플
        """
        keys: list[str] = [
            self._build_key(category, date) for category in KEYWORD_TYPES
        ]
        return tuple(self._get_keywords_by_key(key) for key in keys)

    def key_load_template(
        self, date: str | None = None
    ) -> tuple[RedisTemplateInfo, TemplateInfo]:
        """Redis에서 키워드를 가져와 템플릿 생성

        Args:
            date: 조회할 날짜 (None일 경우 기본 키에서 조회)

        Returns:
            (키워드 정보, 템플릿 정보) 튜플
        """
        # 키워드 가져오기
        core_keywords, context_keywords = self.get_keywords(date)

        # 템플릿 로드
        templates = asdict(self.countries["KR"])["templates"]

        # 키워드 정보 구성
        keywords_info = RedisTemplateInfo(
            core_keyword=" ".join(core_keywords) if core_keywords else "",
            context_keyword=" ".join(context_keywords) if context_keywords else "",
        )

        return keywords_info, templates
