"""User-Controlled Local Memory Management Service."""

import logging
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from backend.app.storage.database import engine
from backend.app.storage.models import MemoryRecord, utc_now_iso

logger = logging.getLogger("aitmate.services.memory")


class MemoryService:
    """Provides user-auditable local memory operations stored on local SQLite."""

    def list(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """List stored memories with optional search and category filters."""
        with Session(engine, expire_on_commit=False) as session:
            statement = select(MemoryRecord)
            if category:
                statement = statement.where(MemoryRecord.category == category)
            if search:
                term = f"%{search.lower()}%"
                statement = statement.where(
                    MemoryRecord.key.ilike(term) | MemoryRecord.content.ilike(term)
                )
            statement = statement.order_by(MemoryRecord.updated_at.desc()).limit(limit)
            return list(session.exec(statement).all())

    def get(self, memory_id: str) -> Optional[MemoryRecord]:
        """Fetch memory record by ID."""
        with Session(engine, expire_on_commit=False) as session:
            return session.get(MemoryRecord, memory_id)

    def set(self, key: str, content: str, category: str = "preference") -> MemoryRecord:
        """Create or update a memory record by key."""
        with Session(engine, expire_on_commit=False) as session:
            statement = select(MemoryRecord).where(MemoryRecord.key == key)
            record = session.exec(statement).first()
            if record:
                record.content = content
                record.category = category
                record.updated_at = utc_now_iso()
                session.add(record)
                session.commit()
                session.refresh(record)
                logger.info("Updated existing memory key: %s", key)
                return record

            record = MemoryRecord(
                key=key,
                content=content,
                category=category,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info("Saved new memory key: %s", key)
            return record

    def delete(self, memory_id: str) -> bool:
        """Delete a single memory record."""
        with Session(engine, expire_on_commit=False) as session:
            record = session.get(MemoryRecord, memory_id)
            if not record:
                return False
            session.delete(record)
            session.commit()
            logger.info("Deleted memory ID: %s", memory_id)
            return True

    def clear(self) -> int:
        """Purge all stored memories (full user wipe)."""
        with Session(engine, expire_on_commit=False) as session:
            records = session.exec(select(MemoryRecord)).all()
            count = len(records)
            for r in records:
                session.delete(r)
            session.commit()
            logger.warning("User wiped all %d stored memories.", count)
            return count

    def export_all(self) -> List[Dict[str, Any]]:
        """Export all memories as JSON-serializable list for user backup/portability."""
        with Session(engine, expire_on_commit=False) as session:
            records = session.exec(select(MemoryRecord)).all()
            return [
                {
                    "id": r.id,
                    "key": r.key,
                    "content": r.content,
                    "category": r.category,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in records
            ]


memory_service = MemoryService()
