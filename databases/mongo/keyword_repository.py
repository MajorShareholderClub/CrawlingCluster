"""
MongoDB Keyword Repository 구현 모듈

이 모듈은 Keyword 도메인 모델을 MongoDB 저장소에 저장하고 검색하는 구현체를 제공합니다.
"""

from datetime import datetime
from typing import Any, Optional
from bson import ObjectId

import motor.motor_asyncio
from pymongo import ReturnDocument, DESCENDING, ASCENDING

from common.config.settings import MONGO_URI, MONGO_DB_NAME
from common.utils.logging_utils import get_logger
from crawling.domain.models.keyword import Keyword
from crawling.domain.interfaces.repository import KeywordRepository


class MongoKeywordRepository(KeywordRepository):
    """Keyword MongoDB Repository 구현체"""
    
    def __init__(self, mongo_uri: str = MONGO_URI, db_name: str = MONGO_DB_NAME):
        """
        MongoDB Keyword Repository 초기화
        
        Args:
            mongo_uri: MongoDB 커넥션 문자열
            db_name: 데이터베이스 이름
        """
        self.logger = get_logger(self.__class__.__name__)
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db["keywords"]
        self.logger.info(f"MongoDB Keyword Repository 초기화 완료: {db_name}.keywords")
    
    def _convert_to_keyword(self, doc: dict[str, Any]) -> Keyword:
        """MongoDB 문서를 Keyword 객체로 변환
        
        Args:
            doc: MongoDB 문서
        
        Returns:
            변환된 Keyword 객체
        """
        # ObjectId -> str 변환
        if '_id' in doc:
            doc['id'] = str(doc.pop('_id'))
            
        return Keyword(
            id=doc.get('id'),
            text=doc.get('text', ''),
            category=doc.get('category', ''),
            priority=doc.get('priority', 5),
            related_keywords=doc.get('related_keywords', []),
            search_count=doc.get('search_count', 0),
            article_count=doc.get('article_count', 0),
            last_searched_at=doc.get('last_searched_at'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at'),
            active=doc.get('active', True),
            metadata=doc.get('metadata', {})
        )
    
    def _convert_to_doc(self, keyword: Keyword) -> dict[str, Any]:
        """Keyword 객체를 MongoDB 문서로 변환
        
        Args:
            keyword: Keyword 객체
        
        Returns:
            변환된 MongoDB 문서
        """
        doc = keyword.__dict__.copy()
        
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
                # id가 ObjectId 형식이 아닌경우 삭제
                doc.pop('id', None)
                
        return doc
        
    async def save(self, keyword: Keyword) -> Keyword:
        """Keyword 객체 저장
        
        Args:
            keyword: 저장할 Keyword 객체
        
        Returns:
            저장된 Keyword 객체
        """
        # 동일 텍스트의 키워드가 있는지 검색
        existing = await self.collection.find_one({'text': keyword.text})
        
        if existing:
            # 이미 존재하는 키워드인 경우 업데이트
            doc = self._convert_to_doc(keyword)
            doc.pop('_id', None)  # 동일 키워드 업데이트이므로 _id 제거
            
            result = await self.collection.find_one_and_update(
                {'_id': existing['_id']},
                {'$set': doc},
                return_document=ReturnDocument.AFTER
            )
            return self._convert_to_keyword(result)
        else:
            # 새로운 키워드인 경우 생성
            doc = self._convert_to_doc(keyword)
            result = await self.collection.insert_one(doc)
            doc['_id'] = result.inserted_id
            return self._convert_to_keyword(doc)
    
    async def save_all(self, keywords: list[Keyword]) -> list[Keyword]:
        """Keyword 객체 목록 저장
        
        Args:
            keywords: 저장할 Keyword 객체 목록
        
        Returns:
            저장된 Keyword 객체 목록
        """
        if not keywords:
            return []
        
        results = []
        for keyword in keywords:
            # 각 키워드를 개별적으로 저장 (중복 체크를 위해)
            saved_keyword = await self.save(keyword)
            results.append(saved_keyword)
            
        return results
    
    async def find_by_id(self, id: str) -> Optional[Keyword]:
        """ID에 해당하는 Keyword 검색
        
        Args:
            id: 검색할 Keyword ID
        
        Returns:
            검색된 Keyword 객체 또는 None
        """
        try:
            doc = await self.collection.find_one({'_id': ObjectId(id)})
            return self._convert_to_keyword(doc) if doc else None
        except Exception as e:
            self.logger.error(f"ID 검색 오류: {e}")
            return None
    
    async def find_all(self) -> list[Keyword]:
        """Keyword 전체 목록 검색
        
        Returns:
            검색된 Keyword 객체 목록
        """
        cursor = self.collection.find()
        docs = await cursor.to_list(length=None)
        return [self._convert_to_keyword(doc) for doc in docs]
    
    async def find_by_criteria(self, criteria: dict[str, Any]) -> list[Keyword]:
        """조건에 맞는 Keyword 객체 검색
        
        Args:
            criteria: 검색 조건
            
        Returns:
            검색된 Keyword 객체 목록
        """
        cursor = self.collection.find(criteria)
        docs = await cursor.to_list(length=None)
        return [self._convert_to_keyword(doc) for doc in docs]
    
    async def update(self, keyword: Keyword) -> Keyword:
        """Keyword 객체 업데이트
        
        Args:
            keyword: 업데이트할 Keyword 객체
            
        Returns:
            업데이트된 Keyword 객체
        """
        if not keyword.id:
            # ID가 없는 경우 저장
            return await self.save(keyword)
        
        doc = self._convert_to_doc(keyword)
        object_id = doc.pop('_id', None)
        
        result = await self.collection.find_one_and_update(
            {'_id': object_id},
            {'$set': doc},
            return_document=ReturnDocument.AFTER
        )
        
        if not result:
            # 업데이트할 문서가 없는 경우 저장
            doc['_id'] = object_id
            return await self.save(keyword)
        
        return self._convert_to_keyword(result)
    
    async def delete(self, id: str) -> bool:
        """ID로 Keyword 삭제
        
        Args:
            id: 삭제할 Keyword ID
            
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
        """Keyword 전체 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            result = await self.collection.delete_many({})  # 전체 삭제
            self.logger.info(f"{result.deleted_count}개 키워드 삭제 완료")
            return True
        except Exception as e:
            self.logger.error(f"전체 삭제 오류: {e}")
            return False
    
    async def find_by_category(self, category: str) -> list[Keyword]:
        """카테고리로 Keyword 검색
        
        Args:
            category: 검색할 카테고리
            
        Returns:
            검색된 Keyword 객체 목록
        """
        return await self.find_by_criteria({'category': category, 'active': True})
    
    async def find_trending(self, limit: int = 10) -> list[Keyword]:
        """트렌딩 키워드 검색
        
        Args:
            limit: 가져올 최대 키워드 수
            
        Returns:
            검색된 키워드 목록
        """
        # search_count와 article_count를 기준으로 정렬
        cursor = self.collection.find({'active': True}).\
                              sort([('search_count', DESCENDING), 
                                    ('article_count', DESCENDING)]).\
                              limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return [self._convert_to_keyword(doc) for doc in docs]
    
    async def update_keyword_stats(self, keyword: str, article_count: int) -> bool:
        """Keyword 통계 정보 업데이트
        
        Args:
            keyword: 업데이트할 키워드 텍스트
            article_count: 새로 찾은 기사 수
            
        Returns:
            업데이트 성공 여부
        """
        try:
            now = datetime.utcnow()
            result = await self.collection.update_one(
                {'text': keyword},
                {
                    '$inc': {
                        'search_count': 1,
                        'article_count': article_count
                    },
                    '$set': {
                        'last_searched_at': now,
                        'updated_at': now
                    }
                },
                upsert=True  # 없으면 생성
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            self.logger.error(f"통계 업데이트 오류: {e}")
            return False
    
    async def find_by_text(self, text: str, exact_match: bool = False) -> Optional[Keyword]:
        """Keyword 텍스트로 검색
        
        Args:
            text: 검색할 키워드 텍스트
            exact_match: 정확한 일치 여부 (기본값: False)
            
        Returns:
            검색된 Keyword 객체 또는 None
        """
        if exact_match:
            doc = await self.collection.find_one({'text': text})
        else:
            # 정규식을 사용한 부분 일치 검색
            doc = await self.collection.find_one({'text': {'$regex': text, '$options': 'i'}})
        
        return self._convert_to_keyword(doc) if doc else None
    
    async def find_related_keywords(self, text: str, limit: int = 5) -> list[Keyword]:
        """Keyword와 관련된 키워드 검색
        
        Args:
            text: 검색할 키워드 텍스트
            limit: 가져올 최대 키워드 수
            
        Returns:
            관련 키워드 목록
        """
        # 1. 정확한 키워드 검색
        keyword = await self.find_by_text(text, exact_match=True)
        
        if keyword and keyword.related_keywords:
            # 관련 키워드가 있는 경우, 해당 키워드들 가져오기
            cursor = self.collection.find({
                'text': {'$in': keyword.related_keywords},
                'active': True
            }).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            related = [self._convert_to_keyword(doc) for doc in docs]
            
            if len(related) >= limit:
                return related
                
            remaining = limit - len(related)
        else:
            remaining = limit
            related = []
        
        # 2. 키워드가 없다면 유사 키워드 검색
        if remaining > 0:
            cursor = self.collection.find({
                'text': {'$regex': f".*{text}.*", '$options': 'i'},
                'active': True
            }).limit(remaining)
            
            docs = await cursor.to_list(length=remaining)
            similar = [self._convert_to_keyword(doc) for doc in docs]
            related.extend(similar)
        
        return related
