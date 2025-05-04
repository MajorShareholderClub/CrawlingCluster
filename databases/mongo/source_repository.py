"""
MongoDB Source Repository 구현 모듈

이 모듈은 Source 도메인 모델을 MongoDB 저장소에 저장하고 검색하는 구현체를 제공합니다.
"""

from datetime import datetime
from typing import Any, Optional
from bson import ObjectId

import motor.motor_asyncio
from pymongo import ReturnDocument, ASCENDING

from common.config.settings import MONGO_URI, MONGO_DB_NAME
from common.utils.logging_utils import get_logger
from crawling.domain.models.source import Source, SourceType
from crawling.domain.interfaces.repository import SourceRepository


class MongoSourceRepository(SourceRepository):
    """Source MongoDB Repository 구현체"""
    
    def __init__(self, mongo_uri: str = MONGO_URI, db_name: str = MONGO_DB_NAME):
        """
        MongoDB Source Repository 초기화
        
        Args:
            mongo_uri: MongoDB 커넥션 문자열
            db_name: 데이터베이스 이름
        """
        self.logger = get_logger(self.__class__.__name__)
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db["sources"]
        self.logger.info(f"MongoDB Source Repository 초기화 완료: {db_name}.sources")
    
    def _convert_to_source(self, doc: dict[str, Any]) -> Source:
        """MongoDB 문서를 Source 객체로 변환
        
        Args:
            doc: MongoDB 문서
        
        Returns:
            변환된 Source 객체
        """
        # ObjectId -> str 변환
        if '_id' in doc:
            doc['id'] = str(doc.pop('_id'))
        
        # source_type 이름에서 열거형으로 변환
        source_type = doc.get('type')
        if isinstance(source_type, str):
            try:
                source_type = SourceType[source_type]
            except (KeyError, ValueError):
                source_type = SourceType.NEWS  # 기본값
        
        return Source(
            id=doc.get('id'),
            name=doc.get('name', ''),
            base_url=doc.get('base_url', ''),
            type=source_type if source_type else SourceType.NEWS,
            priority=doc.get('priority', 5),
            active=doc.get('active', True),
            headers=doc.get('headers', {}),
            selectors=doc.get('selectors', {}),
            rate_limit=doc.get('rate_limit'),
            keywords=doc.get('keywords', [])
        )
    
    def _convert_to_doc(self, source: Source) -> dict[str, Any]:
        """Source 객체를 MongoDB 문서로 변환
        
        Args:
            source: Source 객체
        
        Returns:
            변환된 MongoDB 문서
        """
        # to_dict 메서드 사용
        doc = source.to_dict()
        
        # MongoDB _id 체크
        if 'id' in doc and doc['id']:
            try:
                doc['_id'] = ObjectId(doc.pop('id'))
            except Exception:
                # id가 ObjectId 형식이 아닌경우 삭제
                doc.pop('id', None)
                
        return doc
        
    async def save(self, source: Source) -> Source:
        """Source 객체 저장
        
        Args:
            source: 저장할 Source 객체
        
        Returns:
            저장된 Source 객체
        """
        # 동일 이름의 소스가 있는지 검색
        existing = await self.collection.find_one({'name': source.name})
        
        if existing:
            # 이미 존재하는 소스인 경우 업데이트
            doc = self._convert_to_doc(source)
            doc.pop('_id', None)  # 동일 소스 업데이트이므로 _id 제거
            
            result = await self.collection.find_one_and_update(
                {'_id': existing['_id']},
                {'$set': doc},
                return_document=ReturnDocument.AFTER
            )
            return self._convert_to_source(result)
        else:
            # 새로운 소스인 경우 생성
            doc = self._convert_to_doc(source)
            result = await self.collection.insert_one(doc)
            doc['_id'] = result.inserted_id
            return self._convert_to_source(doc)
    
    async def save_all(self, sources: list[Source]) -> list[Source]:
        """Source 객체 목록 저장
        
        Args:
            sources: 저장할 Source 객체 목록
        
        Returns:
            저장된 Source 객체 목록
        """
        if not sources:
            return []
        
        results = []
        for source in sources:
            # 각 소스를 개별적으로 저장 (중복 체크를 위해)
            saved_source = await self.save(source)
            results.append(saved_source)
            
        return results
    
    async def find_by_id(self, id: str) -> Optional[Source]:
        """ID에 해당하는 Source 검색
        
        Args:
            id: 검색할 Source ID
        
        Returns:
            검색된 Source 객체 또는 None
        """
        try:
            doc = await self.collection.find_one({'_id': ObjectId(id)})
            return self._convert_to_source(doc) if doc else None
        except Exception as e:
            self.logger.error(f"ID 검색 오류: {e}")
            return None
    
    async def find_all(self) -> list[Source]:
        """Source 전체 목록 검색
        
        Returns:
            검색된 Source 객체 목록
        """
        cursor = self.collection.find().sort('priority', ASCENDING)
        docs = await cursor.to_list(length=None)
        return [self._convert_to_source(doc) for doc in docs]
    
    async def find_by_criteria(self, criteria: dict[str, Any]) -> list[Source]:
        """조건에 맞는 Source 객체 검색
        
        Args:
            criteria: 검색 조건
            
        Returns:
            검색된 Source 객체 목록
        """
        cursor = self.collection.find(criteria).sort('priority', ASCENDING)
        docs = await cursor.to_list(length=None)
        return [self._convert_to_source(doc) for doc in docs]
    
    async def update(self, source: Source) -> Source:
        """Source 객체 업데이트
        
        Args:
            source: 업데이트할 Source 객체
            
        Returns:
            업데이트된 Source 객체
        """
        if not source.id:
            # ID가 없는 경우 저장
            return await self.save(source)
        
        doc = self._convert_to_doc(source)
        object_id = doc.pop('_id', None)
        
        result = await self.collection.find_one_and_update(
            {'_id': object_id},
            {'$set': doc},
            return_document=ReturnDocument.AFTER
        )
        
        if not result:
            # 업데이트할 문서가 없는 경우 저장
            doc['_id'] = object_id
            return await self.save(source)
        
        return self._convert_to_source(result)
    
    async def delete(self, id: str) -> bool:
        """ID로 Source 삭제
        
        Args:
            id: 삭제할 Source ID
            
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
        """Source 전체 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            result = await self.collection.delete_many({})  # 전체 삭제
            self.logger.info(f"{result.deleted_count}개 소스 삭제 완료")
            return True
        except Exception as e:
            self.logger.error(f"전체 삭제 오류: {e}")
            return False
    
    async def find_by_type(self, source_type: str) -> list[Source]:
        """타입별 Source 검색
        
        Args:
            source_type: 검색할 소스 타입 (예: NEWS, BLOG)
            
        Returns:
            검색된 Source 객체 목록
        """
        # 열거형 이름이나 문자열 모두 처리
        if isinstance(source_type, SourceType):
            source_type = source_type.name
            
        return await self.find_by_criteria({'type': source_type, 'active': True})
    
    async def find_active(self) -> list[Source]:
        """활성화된 Source 검색
        
        Returns:
            활성화된 Source 객체 목록
        """
        return await self.find_by_criteria({'active': True})
    
    async def find_by_name(self, name: str) -> Optional[Source]:
        """이름으로 Source 검색
        
        Args:
            name: 검색할 소스 이름
            
        Returns:
            검색된 Source 객체 또는 None
        """
        doc = await self.collection.find_one({'name': name})
        return self._convert_to_source(doc) if doc else None
    
    async def find_by_domain(self, domain: str) -> Optional[Source]:
        """도메인으로 Source 검색
        
        Args:
            domain: 검색할 도메인
            
        Returns:
            검색된 Source 객체 또는 None
        """
        # base_url에서 도메인 부분 검색
        doc = await self.collection.find_one({'base_url': {'$regex': domain, '$options': 'i'}})
        return self._convert_to_source(doc) if doc else None
    
    async def update_active_status(self, id: str, active: bool) -> bool:
        """Source 사용 활성화 상태를 업데이트
        
        Args:
            id: 업데이트할 Source ID
            active: 활성화 여부
            
        Returns:
            업데이트 성공 여부
        """
        try:
            result = await self.collection.update_one(
                {'_id': ObjectId(id)},
                {'$set': {'active': active, 'updated_at': datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"활성화 상태 업데이트 오류: {e}")
            return False
