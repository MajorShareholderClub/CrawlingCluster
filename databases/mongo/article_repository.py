import asyncio
from datetime import datetime
from typing import Any, Optional
from bson import ObjectId

import motor.motor_asyncio
from pymongo import ReturnDocument

from common.config.settings import MONGO_URI, MONGO_DB_NAME
from common.utils.logging_utils import get_logger
from crawling.domain.models.article import Article
from crawling.domain.interfaces.repository import ArticleRepository


class MongoArticleRepository(ArticleRepository):
    """Article MongoDB Repository 구현체"""
    
    def __init__(self, mongo_uri: str = MONGO_URI, db_name: str = MONGO_DB_NAME):
        """MongoDB Article Repository 초기화
        
        Args:
            mongo_uri: MongoDB 커넥션 문자열
            db_name: 데이터베이스 이름
        """
        self.logger = get_logger(self.__class__.__name__)
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db["articles"]
        self.logger.info(f"MongoDB Article Repository 초기화 완료: {db_name}.articles")
    
    def _convert_to_article(self, doc: dict[str, Any]) -> Article:
        """MongoDB 문서를 Article 객체로 변환
        
        Args:
            doc: MongoDB 문서
        
        Returns:
            변환된 Article 객체
        """
        # ObjectId -> str 변환
        if '_id' in doc:
            doc['id'] = str(doc.pop('_id'))
            
        return Article(
            id=doc.get('id'),
            url=doc.get('url', ''),
            title=doc.get('title', ''),
            content=doc.get('content', ''),
            html_content=doc.get('html_content', ''),
            source=doc.get('source', ''),
            keywords=doc.get('keywords', []),
            pub_date=doc.get('pub_date'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )
    
    def _convert_to_doc(self, article: Article) -> dict[str, Any]:
        """Article 객체를 MongoDB 문서로 변환
        
        Args:
            article: Article 객체
        
        Returns:
            변환된 MongoDB 문서
        """
        doc = article.__dict__.copy()
        
        # 시간 필드 체크
        now = datetime.utcnow()
        if 'created_at' not in doc or not doc['created_at']:
            doc['created_at'] = now
        doc['updated_at'] = now
        
        # MongoDB _id 체크
        if 'id' in doc and doc['id']:
            try:
                doc['_id'] = ObjectId(doc.pop('id'))
            except Exception:
                # id가 ObjectId 형식이 아닐경우 삭제
                doc.pop('id', None)
                
        return doc
        
    async def save(self, article: Article) -> Article:
        """Article 객체 저장
        
        Args:
            article: 저장할 Article 객체
        
        Returns:
            저장된 Article 객체
        """
        doc = self._convert_to_doc(article)
        result = await self.collection.insert_one(doc)
        doc['_id'] = result.inserted_id
        return self._convert_to_article(doc)
    
    async def save_all(self, articles: list[Article]) -> list[Article]:
        """여러 Article 객체 저장
        
        Args:
            articles: 저장할 Article 객체 목록
        
        Returns:
            저장된 Article 객체 목록
        """
        if not articles:
            return []
            
        docs = [self._convert_to_doc(article) for article in articles]
        result = await self.collection.insert_many(docs)
        
        # inserted_ids 사용하여 객체 갱신
        for i, doc in enumerate(docs):
            if i < len(result.inserted_ids):
                doc['_id'] = result.inserted_ids[i]
                
        return [self._convert_to_article(doc) for doc in docs]
    
    async def find_by_id(self, id: str) -> Optional[Article]:
        """아이디로 Article 검색
        
        Args:
            id: 검색할 Article ID
        
        Returns:
            찾은 Article 또는 None
        """
        try:
            doc = await self.collection.find_one({'_id': ObjectId(id)})
            return self._convert_to_article(doc) if doc else None
        except Exception as e:
            self.logger.error(f"ID 검색 오류: {e}")
            return None
    
    async def find_all(self) -> list[Article]:
        """모든 Article 검색
        
        Returns:
            검색된 Article 객체 목록
        """
        cursor = self.collection.find()
        docs = await cursor.to_list(length=None)
        return [self._convert_to_article(doc) for doc in docs]
    
    async def find_by_criteria(self, criteria: dict[str, Any]) -> list[Article]:
        """조건으로 Article 검색
        
        Args:
            criteria: 검색 조건
        
        Returns:
            검색된 Article 객체 목록
        """
        cursor = self.collection.find(criteria)
        docs = await cursor.to_list(length=None)
        return [self._convert_to_article(doc) for doc in docs]
    
    async def update(self, article: Article) -> Article:
        """Article 객체 업데이트
        
        Args:
            article: 업데이트할 Article 객체
        
        Returns:
            업데이트된 Article 객체
        """
        if not article.id:
            # ID없는 경우는 첨부
            return await self.save(article)
        
        doc = self._convert_to_doc(article)
        object_id = doc.pop('_id', None)
        
        result = await self.collection.find_one_and_update(
            {'_id': object_id},
            {'$set': doc},
            return_document=ReturnDocument.AFTER
        )
        
        if not result:
            # 만약 업데이트할 문서가 없는 경우 다시 저장
            doc['_id'] = object_id
            return await self.save(article)
        
        return self._convert_to_article(result)
    
    async def delete(self, id: str) -> bool:
        """ID 기준으로 Article 삭제
        
        Args:
            id: 삭제할 Article ID
        
        Returns:
            삭제 성공 여부
        """
        try:
            result = await self.collection.delete_one({'_id': ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"삭제 오류: {e}")
            return False
    
    async def delete_all(self) -> bool:
        """모든 Article 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            result = await self.collection.delete_many({})  # 모든 문서 삭제
            self.logger.info(f"{result.deleted_count}개 Article 삭제 완료")
            return True
        except Exception as e:
            self.logger.error(f"전체 삭제 오류: {e}")
            return False
    
    async def find_by_keyword(self, keyword: str) -> list[Article]:
        """키워드로 Article 검색
        
        Args:
            keyword: 검색할 키워드
        
        Returns:
            검색된 Article 객체 목록
        """
        # 태거나 콘텐츠에서 키워드 검색
        query = {
            '$or': [
                {'title': {'$regex': keyword, '$options': 'i'}},
                {'content': {'$regex': keyword, '$options': 'i'}},
                {'keywords': keyword}
            ]
        }
        return await self.find_by_criteria(query)
    
    async def find_by_source(self, source: str) -> list[Article]:
        """소스별 Article 검색
        
        Args:
            source: 검색할 소스
        
        Returns:
            검색된 Article 객체 목록
        """
        return await self.find_by_criteria({'source': source})
    
    async def find_by_date_range(self, start_date: str, end_date: str) -> list[Article]:
        """날짜 범위로 Article 검색
        
        Args:
            start_date: 시작 날짜 (ISO 형식: YYYY-MM-DD)
            end_date: 마지막 날짜 (ISO 형식: YYYY-MM-DD)
        
        Returns:
            검색된 Article 객체 목록
        """
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            # 마지막 날짜는 하루 마지막 시간으로 설정
            end = end.replace(hour=23, minute=59, second=59)
            
            query = {
                '$or': [
                    # pub_date 날짜 범위 검색
                    {'pub_date': {'$gte': start, '$lte': end}},
                    # 생성 날짜 범위 검색
                    {'created_at': {'$gte': start, '$lte': end}}
                ]
            }
            return await self.find_by_criteria(query)
        except ValueError as e:
            self.logger.error(f"날짜 형식 오류: {e}")
            return []
