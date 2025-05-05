"""투자 관련 키워드 및 질의어 생성 모듈"""

import random
from typing import list, dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from databases.cache.redis_singleton import RedisSingleton

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("query_generator")

# Redis 키 상수
REDIS_KEY_PREFIX = "query:"
REDIS_KEY_INVESTING = f"{REDIS_KEY_PREFIX}investing"
REDIS_KEY_GOOGLE = f"{REDIS_KEY_PREFIX}google"
REDIS_KEY_TIMESTAMP = f"{REDIS_KEY_PREFIX}last_update"

# 기본 만료 시간 (24시간)
DEFAULT_EXPIRY = 24 * 60 * 60


class QueryGenerator:
    """투자 관련 키워드 및 질의어 생성기
    
    Attributes:
        redis_client: Redis 클라이언트 인스턴스
        base_keywords: 기본 키워드 목록
    """
    
    def __init__(self, redis_db: int = 0):
        """초기화
        
        Args:
            redis_db: Redis DB 번호 (기본값: 0)
        """
        self.redis = RedisSingleton(db=redis_db)
        
        # 기본 키워드 설정
        self.base_keywords = {
            # 주식 관련 키워드
            "stock": ["주식", "주가", "증시", "코스피", "코스닥", "나스닥", "S&P500", "다우존스"],
            
            # 가상화폐 관련 키워드
            "crypto": ["비트코인", "이더리움", "리플", "코인", "가상화폐", "암호화폐", "블록체인"],
            
            # 경제 관련 키워드
            "economy": ["경제", "경기", "금리", "인플레이션", "디플레이션", "재정", "통화정책", "연준", "중앙은행"],
            
            # 투자 관련 키워드
            "investment": ["투자", "수익률", "배당", "자산", "포트폴리오", "분산투자", "가치투자"],
        }
        
        # 질의어 템플릿
        self.query_templates = [
            "{keyword} 전망",
            "{keyword} 투자 방법",
            "{keyword} 최근 동향",
            "{keyword} 뉴스",
            "{keyword} 분석",
            "최근 {keyword} 이슈",
            "{keyword} 전문가 의견",
            "{keyword} 시장 상황",
            "{keyword} 투자 전략",
            "{keyword} 미래",
        ]
    
    def generate_investing_keywords(self, asset_type: str, count: int = 10) -> list[str]:
        """Investing.com 검색용 키워드 생성
        
        Args:
            asset_type: 자산 유형 (stock, crypto, economy, investment)
            count: 생성할 키워드 수 (기본값: 10)
            
        Returns:
            list[str]: 생성된 키워드 목록
        """
        if asset_type not in self.base_keywords:
            asset_type = random.choice(list(self.base_keywords.keys()))
        
        # 기본 키워드에서 무작위로 선택
        keywords = random.sample(
            self.base_keywords[asset_type], 
            min(count, len(self.base_keywords[asset_type]))
        )
        
        logger.info(f"Investing.com 검색용 키워드 {len(keywords)}개 생성: {keywords}")
        return keywords
    
    def generate_google_queries(self, asset_type: str, count: int = 10) -> list[str]:
        """Google 검색용 질의어 생성
        
        Args:
            asset_type: 자산 유형 (stock, crypto, economy, investment)
            count: 생성할 질의어 수 (기본값: 10)
            
        Returns:
            list[str]: 생성된 질의어 목록
        """
        if asset_type not in self.base_keywords:
            asset_type = random.choice(list(self.base_keywords.keys()))
        
        # 기본 키워드에서 무작위로 선택
        base_keywords = self.base_keywords[asset_type]
        
        # 키워드와 템플릿을 조합하여 질의어 생성
        queries = []
        while len(queries) < count:
            keyword = random.choice(base_keywords)
            template = random.choice(self.query_templates)
            query = template.format(keyword=keyword)
            
            # 중복 제거
            if query not in queries:
                queries.append(query)
        
        logger.info(f"Google 검색용 질의어 {len(queries)}개 생성: {queries}")
        return queries
    
    def save_to_redis(self, investing_keywords: list[str], google_queries: list[str], expiry: int = DEFAULT_EXPIRY) -> bool:
        """생성된 키워드와 질의어를 Redis에 저장
        
        Args:
            investing_keywords: Investing.com 검색용 키워드 목록
            google_queries: Google 검색용 질의어 목록
            expiry: 만료 시간(초) (기본값: 24시간)
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 현재 시간
            now = datetime.now().isoformat()
            
            # 데이터 저장
            self.redis.set(REDIS_KEY_INVESTING, investing_keywords, expiry)
            self.redis.set(REDIS_KEY_GOOGLE, google_queries, expiry)
            self.redis.set(REDIS_KEY_TIMESTAMP, now, expiry)
            
            logger.info(f"Redis에 키워드 및 질의어 저장 완료 (만료: {expiry}초)")
            return True
        except Exception as e:
            logger.error(f"Redis 저장 오류: {e}")
            return False
    
    def get_from_redis(self) -> dict[str, Any]:
        """Redis에서 키워드 및 질의어 조회
        
        Returns:
            dict: 키워드 및 질의어 데이터
        """
        # 데이터 조회
        investing_keywords = self.redis.get(REDIS_KEY_INVESTING, [])
        google_queries = self.redis.get(REDIS_KEY_GOOGLE, [])
        last_update = self.redis.get(REDIS_KEY_TIMESTAMP, "")
        
        # 최종 데이터 구성
        data = {
            "investing_keywords": investing_keywords,
            "google_queries": google_queries,
            "last_update": last_update,
            "has_data": bool(investing_keywords and google_queries),
        }
        
        if data["has_data"]:
            logger.info(f"Redis에서 키워드 및 질의어 조회 성공")
        else:
            logger.warning(f"Redis에 저장된 키워드 및 질의어가 없음")
        
        return data
    
    def generate_and_save(self, asset_type: str = "", keyword_count: int = 10, query_count: int = 10) -> dict[str, Any]:
        """키워드 및 질의어 생성 후 Redis에 저장
        
        Args:
            asset_type: 자산 유형 (stock, crypto, economy, investment)
            keyword_count: 생성할 키워드 수 (기본값: 10)
            query_count: 생성할 질의어 수 (기본값: 10)
            
        Returns:
            dict: 생성된 키워드 및 질의어 데이터
        """
        # 자산 유형이 지정되지 않은 경우 무작위 선택
        if not asset_type or asset_type not in self.base_keywords:
            asset_type = random.choice(list(self.base_keywords.keys()))
        
        # 키워드 및 질의어 생성
        investing_keywords = self.generate_investing_keywords(asset_type, keyword_count)
        google_queries = self.generate_google_queries(asset_type, query_count)
        
        # Redis에 저장
        self.save_to_redis(investing_keywords, google_queries)
        
        # 데이터 반환
        return {
            "asset_type": asset_type,
            "investing_keywords": investing_keywords,
            "google_queries": google_queries,
            "timestamp": datetime.now().isoformat(),
        }


# 비동기 래퍼 함수
async def async_generate_queries(asset_type: str = "", keyword_count: int = 10, query_count: int = 10) -> dict[str, Any]:
    """비동기 방식으로 키워드 및 질의어 생성 후 Redis에 저장
    
    Args:
        asset_type: 자산 유형 (stock, crypto, economy, investment)
        keyword_count: 생성할 키워드 수 (기본값: 10)
        query_count: 생성할 질의어 수 (기본값: 10)
        
    Returns:
        dict: 생성된 키워드 및 질의어 데이터
    """
    # 동기 함수를 별도 스레드에서 실행
    loop = asyncio.get_event_loop()
    generator = QueryGenerator()
    
    return await loop.run_in_executor(
        None,
        lambda: generator.generate_and_save(asset_type, keyword_count, query_count)
    )


async def async_get_queries() -> dict[str, Any]:
    """비동기 방식으로 Redis에서 키워드 및 질의어 조회
    
    Returns:
        dict: 키워드 및 질의어 데이터
    """
    # 동기 함수를 별도 스레드에서 실행
    loop = asyncio.get_event_loop()
    generator = QueryGenerator()
    
    return await loop.run_in_executor(
        None,
        generator.get_from_redis
    )


# 직접 실행 시 테스트
if __name__ == "__main__":
    # 키워드 및 질의어 생성 테스트
    generator = QueryGenerator()
    
    # 주식 관련 키워드 및 질의어 생성
    stock_data = generator.generate_and_save("stock", 5, 8)
    print("\n=== 주식 관련 키워드 및 질의어 ===\n")
    print(f"Investing.com 키워드: {stock_data['investing_keywords']}")
    print(f"Google 질의어: {stock_data['google_queries']}")
    
    # 가상화폐 관련 키워드 및 질의어 생성
    crypto_data = generator.generate_and_save("crypto", 5, 8)
    print("\n=== 가상화폐 관련 키워드 및 질의어 ===\n")
    print(f"Investing.com 키워드: {crypto_data['investing_keywords']}")
    print(f"Google 질의어: {crypto_data['google_queries']}")
    
    # Redis에서 데이터 조회
    redis_data = generator.get_from_redis()
    print("\n=== Redis에서 조회한 데이터 ===\n")
    print(f"데이터 존재 여부: {redis_data['has_data']}")
    print(f"마지막 업데이트: {redis_data['last_update']}")
