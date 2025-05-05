import json
import logging
from typing import Any

# Redis 싱글톤 임포트
from databases.cache.redis_singleton import default_redis

# 로깅 설정
logger = logging.getLogger("session.storage")


class SessionStorage:
    """Redis를 사용한 세션 및 쿠키 스토리지 관리"""

    def __init__(self, redis_client=None):
        """스토리지 초기화"""
        self.redis = redis_client if redis_client is not None else default_redis.client
        self.cookie_base_key = "crawler:cookies:{}"
        self.session_base_key = "crawler:sessions:{}"
        self.status_base_key = "crawler:status:{}"
        self.default_expiry = 86400  # 24시간 (초 단위)

    def save(
        self,
        key_type: str,
        domain: str,
        data: dict[str, Any],
        expiry: int | None = None,
    ) -> bool:
        """데이터 저장"""
        if key_type == "cookie":
            key = self.cookie_base_key.format(domain)
        elif key_type == "session":
            key = self.session_base_key.format(domain)
        elif key_type == "status":
            key = self.status_base_key.format(domain)
        else:
            logger.error(f"Unknown key type: {key_type}")
            return False

        try:
            self.redis.set(key, json.dumps(data))
            self.redis.expire(key, expiry or self.default_expiry)
            return True
        except Exception as e:
            logger.error(f"Redis save error: {e}")
            return False

    def load(self, key_type: str, domain: str) -> dict[str, Any]:
        """데이터 로드"""
        if key_type == "cookie":
            key = self.cookie_base_key.format(domain)
        elif key_type == "session":
            key = self.session_base_key.format(domain)
        elif key_type == "status":
            key = self.status_base_key.format(domain)
        else:
            logger.error(f"Unknown key type: {key_type}")
            return {}

        try:
            data_json = self.redis.get(key)
            if not data_json:
                return {}
            return json.loads(data_json)
        except Exception as e:
            logger.error(f"Redis load error: {e}")
            return {}

    def delete(self, key_type: str, domain: str) -> bool:
        """데이터 삭제"""
        if key_type == "cookie":
            key = self.cookie_base_key.format(domain)
        elif key_type == "session":
            key = self.session_base_key.format(domain)
        elif key_type == "status":
            key = self.status_base_key.format(domain)
        else:
            logger.error(f"Unknown key type: {key_type}")
            return False

        try:
            return self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def add_to_list(
        self, key_type: str, domain: str, data: Any, max_items: int = 10
    ) -> bool:
        """리스트에 데이터 추가"""
        if key_type == "errors":
            key = f"{self.status_base_key.format(domain)}:errors"
        else:
            logger.error(f"Unknown list key type: {key_type}")
            return False

        try:
            self.redis.lpush(key, json.dumps(data))
            if max_items > 0:
                self.redis.ltrim(key, 0, max_items - 1)
            return True
        except Exception as e:
            logger.error(f"Redis list add error: {e}")
            return False

    def get_list(self, key_type: str, domain: str) -> list[Any]:
        """리스트 데이터 조회"""
        if key_type == "errors":
            key = f"{self.status_base_key.format(domain)}:errors"
        else:
            logger.error(f"Unknown list key type: {key_type}")
            return []

        try:
            items = self.redis.lrange(key, 0, -1)
            return [json.loads(item) for item in items] if items else []
        except Exception as e:
            logger.error(f"Redis list get error: {e}")
            return []
