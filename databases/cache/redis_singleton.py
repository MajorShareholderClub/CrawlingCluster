"""Redis 싱글 인스턴스 관리 모듈"""

import redis
import json
import logging
from typing import Any, Optional, Dict, Union
from common.utils.error_handling import handle_redis_exceptions

# 기본 Redis 설정
DEFAULT_REDIS_HOST = "127.0.0.1"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("redis_singleton")


class RedisSingleton:
    """싱글톤 패턴으로 구현된 Redis 관리 클래스"""

    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(RedisSingleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        host=DEFAULT_REDIS_HOST,
        port=DEFAULT_REDIS_PORT,
        db=DEFAULT_REDIS_DB,
        decode_responses=True,
    ):
        """Redis 클라이언트 초기화

        Args:
            host: Redis 서버 호스트 (기본값: "127.0.0.1")
            port: Redis 서버 포트 (기본값: 6379)
            db: Redis DB 번호 (기본값: 0)
            decode_responses: 응답을 문자열로 디코딩할지 여부 (기본값: True)
        """
        if not self._initialized:
            self.host = host
            self.port = port
            self.db = db
            self.decode_responses = decode_responses
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=self.decode_responses,
            )
            self._initialized = True
            logger.info(f"Redis 싱글턴 인스턴스 생성: {host}:{port}, DB={db}")

    @property
    def client(self) -> redis.Redis:
        """Redis 클라이언트 인스턴스 반환"""
        return self._client

    @classmethod
    def get_instance(
        cls, host=DEFAULT_REDIS_HOST, port=DEFAULT_REDIS_PORT, db=DEFAULT_REDIS_DB
    ) -> "RedisSingleton":
        """RedisSingleton 인스턴스 반환 (편의 메서드)"""
        return cls(host, port, db)

    @handle_redis_exceptions
    def set(
        self,
        key: str,
        value: Union[str, dict, list, int, float],
        expiry: Optional[int] = None,
    ) -> bool:
        """데이터 저장 (자동 직렬화 지원)

        Args:
            key: 저장할 키
            value: 저장할 값 (문자열, 딕셔너리, 리스트, 숫자 지원)
            expiry: 만료 시간(초) (기본값: None, 만료 없음)

        Returns:
            bool: 저장 성공 여부
        """
        # 객체인 경우 JSON으로 직렬화
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        # 값 저장
        if expiry:
            return self._client.setex(key, expiry, value)
        else:
            return self._client.set(key, value)

    @handle_redis_exceptions
    def get(self, key: str, default: Any = None) -> Any:
        """데이터 조회 (자동 역직렬화 시도)

        Args:
            key: 조회할 키
            default: 키가 없을 경우 반환할 기본값

        Returns:
            조회된 값 또는 기본값
        """
        value = self._client.get(key)

        if value is None:
            return default

        # JSON 역직렬화 시도
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # JSON이 아닌 경우 원본 값 반환
            return value

    @handle_redis_exceptions
    def delete(self, *keys) -> int:
        """키 삭제

        Args:
            *keys: 삭제할 키 목록

        Returns:
            int: 삭제된 키 수
        """
        return self._client.delete(*keys)

    @handle_redis_exceptions
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인

        Args:
            key: 확인할 키

        Returns:
            bool: 키 존재 여부
        """
        return bool(self._client.exists(key))

    @handle_redis_exceptions
    def keys(self, pattern: str) -> list[str]:
        """패턴에 맞는 키 목록 조회

        Args:
            pattern: 키 패턴 (예: "user:*")

        Returns:
            list[str]: 일치하는 키 목록
        """
        return [key for key in self._client.keys(pattern)]

    @handle_redis_exceptions
    def flush(self) -> bool:
        """현재 DB의 모든 키 삭제 (주의: 위험한 작업)

        Returns:
            bool: 성공 여부
        """
        return self._client.flushdb()

    @handle_redis_exceptions
    def hash_set(self, name: str, key: str, value: Any) -> bool:
        """해시에 필드 설정

        Args:
            name: 해시 이름
            key: 필드 이름
            value: 필드 값

        Returns:
            bool: 성공 여부
        """
        # 객체인 경우 JSON으로 직렬화
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        return self._client.hset(name, key, value)

    @handle_redis_exceptions
    def hash_get(self, name: str, key: str, default: Any = None) -> Any:
        """해시에서 필드 조회

        Args:
            name: 해시 이름
            key: 필드 이름
            default: 필드가 없을 경우 반환할 기본값

        Returns:
            필드 값 또는 기본값
        """
        value = self._client.hget(name, key)

        if value is None:
            return default

        # JSON 역직렬화 시도
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    @handle_redis_exceptions
    def hash_getall(self, name: str) -> Dict[str, Any]:
        """해시의 모든 필드 조회

        Args:
            name: 해시 이름

        Returns:
            Dict[str, Any]: 모든 필드와 값
        """
        result = {}
        hash_data = self._client.hgetall(name)

        for k, v in hash_data.items():
            # JSON 역직렬화 시도
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v

        return result

    def close(self) -> None:
        """Redis 연결 종료"""
        if self._client:
            self._client.close()
            logger.info("Redis 연결 종료")


# 기본 싱글톤 인스턴스 제공
default_redis = RedisSingleton()
