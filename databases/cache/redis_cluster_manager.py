from __future__ import annotations

import redis
import logging
from redis.cluster import ClusterNode
from dataclasses import dataclass
from common.utils.error_handling import handle_redis_exceptions
from config.properties import redis_clusters

# 로깅 설정
logging.basicConfig(
    filename="redis_cluster.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@dataclass
class RedisNode:
    """Redis 노드 정보를 담는 데이터 클래스"""

    host: str
    port: int
    client: redis.StrictRedis

    @classmethod
    def from_config(cls, node_config: dict) -> RedisNode:
        """설정에서 RedisNode 인스턴스 생성"""
        host: str | None = node_config.get("host")
        port: int | None = node_config.get("port")

        if not host or not port:
            raise ValueError(f"잘못된 노드 설정: {node_config}")

        client = redis.StrictRedis(
            host=host,
            port=port,
            decode_responses=True,
            socket_timeout=5.0,
        )
        return cls(host=host, port=port, client=client)


@dataclass
class RedisClusterManager:
    """Redis 클러스터 관리 데이터 클래스"""

    nodes: list[RedisNode]
    node_map: dict[tuple[str, int], RedisNode]
    cluster_client: redis.RedisCluster

    # fmt: off
    @classmethod
    @handle_redis_exceptions
    def from_config(cls) -> RedisClusterManager:
        """redis 설정 파일에서 RedisClusterManager 인스턴스 생성"""

        # 노드 생성, 클러스터 클라이언트 생성
        nodes: list[RedisNode] = [RedisNode.from_config(node) for node in redis_clusters["redis_clusters"]]
        startup_nodes: list[ClusterNode] = [ClusterNode(host=node.host, port=node.port) for node in nodes]
        cluster_client = redis.RedisCluster(startup_nodes=startup_nodes, decode_responses=True, socket_timeout=5.0)

        # 노드 맵 생성
        node_map: dict[tuple[str, int], RedisNode] = {(node.host, node.port): node for node in nodes}

        # 클러스터 연결 테스트
        cluster_client.ping()
        return cls(nodes=nodes, cluster_client=cluster_client, node_map=node_map)


    @handle_redis_exceptions
    def single_fetch_data(self, key: str, node_port: int | None = None) -> str | dict | None:
        """
        데이터를 Redis 클러스터에서 조회
        Args:
            key (str): 조회할 키
            node_port (Optional[int]): 특정 노드의 포트 번호
        Returns:
            str | dict | None: 조회된 값
        """
        if node_port:
            # 포트로 노드 찾기
            node = next((node for node in self.nodes if node.port == node_port), None)
            if not node:
                raise ValueError(f"❌ 지정된 포트 {node_port}에 해당하는 노드가 없습니다.")
            value = node.client.get(key)
        else:
            value = self.cluster_client.get(key)

        return value
