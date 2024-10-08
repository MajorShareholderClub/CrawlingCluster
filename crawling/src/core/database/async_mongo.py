from crawling.config.properties import mongo_uri
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDBAsync:
    def __init__(self, uri, db_name) -> None:
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    async def insert_data(self, collection_name, data):
        collection = self.db[collection_name]
        result = await collection.insert_one(data)
        return result.inserted_id

    async def close(self):
        self.client.close()


async def mongo_main(data: list, table: str) -> None:
    # MongoDB URI와 데이터베이스 이름
    uri = mongo_uri  # 자신의 MongoDB URI로 변경
    db_name = "crawling_data_insert_db"

    # MongoDBAsync 인스턴스 생성
    mongo = MongoDBAsync(uri, db_name)

    # 데이터 삽입
    inserted_id = await mongo.insert_data(f"{table}_collection", data)
    print(f"Inserted document ID: {inserted_id}")

    # 연결 종료
    await mongo.close()
