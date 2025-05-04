"""싱글 redis 사용할때 사용하는 클래스"""

import aioredis
import yaml
import json
import logging
from pathlib import Path
from common.utils.error_handling import handle_redis_exceptions

# 로깅 설정
logging.basicConfig(
    filename="redis_cluster.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# YAML 설정 파일 로드
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs/cy/database.yaml"
with open(CONFIG_PATH, "r") as file:
    config: list[dict[str, str | int]] = yaml.safe_load(file)["redis_clusters"]


# Redis 클러스터 비동기 관리자
class RedisManager:
    """
    Redis 클러스터를 비동기적으로 관리하는 클래스
    """

    def __init__(self):
        """
        Redis 클라이언트 초기화
        """
        self.startup_nodes: list[dict[str, str | int]] = config

    async def get_client(self, port: int) -> aioredis.Redis:
        """
        특정 노드에 연결하는 비동기 클라이언트 생성
        Args:
            port (int): 노드의 포트 번호
        Returns:
            aioredis.Redis: 비동기 Redis 클라이언트
        """
        node = next((n for n in self.startup_nodes if n["port"] == port), None)
        if not node:
            raise ValueError(f"❌ 포트 {port}에 해당하는 노드가 없습니다.")
        return await aioredis.from_url(f"redis://{node['host']}:{node['port']}")

    @handle_redis_exceptions
    async def store_data(self, port: int, key: str, value: str | dict):
        """
        비동기적으로 데이터를 특정 Redis 노드에 저장
        Args:
            port (int): 저장할 노드의 포트 번호
            key (str): 저장할 키
            value (str | dict): 저장할 값 (문자열 또는 딕셔너리)
        """
        try:
            client = await self.get_client(port)
            serialized_value = json.dumps(value) if isinstance(value, dict) else value
            await client.set(key, serialized_value)
            logging.info(f"✅ {key} → {port}번 노드에 저장됨.")
        finally:
            await client.close()

    @handle_redis_exceptions
    async def fetch_data(self, port: int, key: str):
        """
        비동기적으로 데이터를 특정 Redis 노드에서 조회
        Args:
            port (int): 조회할 노드의 포트 번호
            key (str): 조회할 키
        Returns:
            str | dict | None: 조회된 값
        """
        try:
            client = await self.get_client(port)
            value = await client.get(key)
            return json.loads(value)  # JSON 직렬화된 값을 딕셔너리로 반환
        finally:
            await client.close()
