"""
Database storage layer supporting MongoDB and PostgreSQL
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from loguru import logger

try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    POSTGRES_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    POSTGRES_AVAILABLE = False

from ..core.config import settings


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def save(self, collection: str, data: Dict[str, Any]) -> str:
        """Save data to storage"""
        pass

    @abstractmethod
    def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find documents matching query"""
        pass

    @abstractmethod
    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document matching query"""
        pass

    @abstractmethod
    def update(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update documents matching query"""
        pass

    @abstractmethod
    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete documents matching query"""
        pass

    @abstractmethod
    def close(self):
        """Close connection"""
        pass


class MongoDBStorage(StorageBackend):
    """MongoDB storage backend"""

    def __init__(self):
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo not installed. Install with: pip install pymongo")

        self.client = MongoClient(settings.database.mongodb_uri)
        self.db = self.client[settings.database.mongodb_db_name]
        logger.info(f"Connected to MongoDB: {settings.database.mongodb_db_name}")

    def save(self, collection: str, data: Dict[str, Any]) -> str:
        """Save data to MongoDB"""
        # Add timestamp
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow()

        result = self.db[collection].insert_one(data)
        logger.debug(f"Saved document to {collection}: {result.inserted_id}")
        return str(result.inserted_id)

    def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find documents in MongoDB"""
        results = list(self.db[collection].find(query))
        # Convert ObjectId to string
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        return results

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document in MongoDB"""
        result = self.db[collection].find_one(query)
        if result and "_id" in result:
            result["_id"] = str(result["_id"])
        return result

    def update(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update documents in MongoDB"""
        # Add update timestamp
        data["updated_at"] = datetime.utcnow()

        result = self.db[collection].update_many(query, {"$set": data})
        logger.debug(f"Updated {result.modified_count} documents in {collection}")
        return result.modified_count > 0

    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete documents from MongoDB"""
        result = self.db[collection].delete_many(query)
        logger.debug(f"Deleted {result.deleted_count} documents from {collection}")
        return result.deleted_count

    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        logger.info("MongoDB connection closed")


if POSTGRES_AVAILABLE:
    class ScrapedData(Base):
        """SQLAlchemy model for scraped data"""
        __tablename__ = "scraped_data"

        id = Column(Integer, primary_key=True, autoincrement=True)
        collection = Column(String(255), nullable=False, index=True)
        url = Column(Text, nullable=True)
        title = Column(Text, nullable=True)
        content = Column(Text, nullable=True)
        metadata = Column(JSON, nullable=True)
        entities = Column(JSON, nullable=True)
        structured_data = Column(JSON, nullable=True)
        raw_data = Column(JSON, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostgreSQLStorage(StorageBackend):
    """PostgreSQL storage backend"""

    def __init__(self):
        if not POSTGRES_AVAILABLE:
            raise ImportError("sqlalchemy not installed. Install with: pip install sqlalchemy psycopg2-binary")

        self.engine = create_engine(settings.database.get_postgres_url())
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Connected to PostgreSQL: {settings.database.postgres_db}")

    def save(self, collection: str, data: Dict[str, Any]) -> str:
        """Save data to PostgreSQL"""
        session: Session = self.SessionLocal()

        try:
            record = ScrapedData(
                collection=collection,
                url=data.get("url"),
                title=data.get("title"),
                content=data.get("content"),
                metadata=data.get("metadata"),
                entities=data.get("entities"),
                structured_data=data.get("structured_data"),
                raw_data=data,
            )

            session.add(record)
            session.commit()
            record_id = record.id
            logger.debug(f"Saved record to {collection}: {record_id}")
            return str(record_id)

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to PostgreSQL: {e}")
            raise
        finally:
            session.close()

    def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find records in PostgreSQL"""
        session: Session = self.SessionLocal()

        try:
            q = session.query(ScrapedData).filter(ScrapedData.collection == collection)

            # Simple query support
            if "url" in query:
                q = q.filter(ScrapedData.url == query["url"])
            if "title" in query:
                q = q.filter(ScrapedData.title.like(f"%{query['title']}%"))

            results = []
            for record in q.all():
                results.append({
                    "id": record.id,
                    "collection": record.collection,
                    "url": record.url,
                    "title": record.title,
                    "content": record.content,
                    "metadata": record.metadata,
                    "entities": record.entities,
                    "structured_data": record.structured_data,
                    "raw_data": record.raw_data,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                })

            return results

        finally:
            session.close()

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one record in PostgreSQL"""
        results = self.find(collection, query)
        return results[0] if results else None

    def update(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update records in PostgreSQL"""
        session: Session = self.SessionLocal()

        try:
            q = session.query(ScrapedData).filter(ScrapedData.collection == collection)

            if "url" in query:
                q = q.filter(ScrapedData.url == query["url"])

            count = q.update({
                "title": data.get("title"),
                "content": data.get("content"),
                "metadata": data.get("metadata"),
                "entities": data.get("entities"),
                "structured_data": data.get("structured_data"),
                "raw_data": data.get("raw_data"),
                "updated_at": datetime.utcnow(),
            })

            session.commit()
            logger.debug(f"Updated {count} records in {collection}")
            return count > 0

        except Exception as e:
            session.rollback()
            logger.error(f"Error updating PostgreSQL: {e}")
            raise
        finally:
            session.close()

    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete records from PostgreSQL"""
        session: Session = self.SessionLocal()

        try:
            q = session.query(ScrapedData).filter(ScrapedData.collection == collection)

            if "url" in query:
                q = q.filter(ScrapedData.url == query["url"])

            count = q.delete()
            session.commit()
            logger.debug(f"Deleted {count} records from {collection}")
            return count

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting from PostgreSQL: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close PostgreSQL connection"""
        self.engine.dispose()
        logger.info("PostgreSQL connection closed")


class DatabaseManager:
    """Database manager that selects appropriate backend"""

    def __init__(self, db_type: Optional[str] = None):
        self.db_type = db_type or settings.database.database_type
        self.backend: StorageBackend

        if self.db_type == "mongodb":
            self.backend = MongoDBStorage()
        elif self.db_type == "postgres":
            self.backend = PostgreSQLStorage()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def save(self, collection: str, data: Dict[str, Any]) -> str:
        """Save data"""
        return self.backend.save(collection, data)

    def find(self, collection: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find documents"""
        return self.backend.find(collection, query or {})

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document"""
        return self.backend.find_one(collection, query)

    def update(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update documents"""
        return self.backend.update(collection, query, data)

    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete documents"""
        return self.backend.delete(collection, query)

    def close(self):
        """Close connection"""
        self.backend.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
