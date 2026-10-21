"""API Routes for User-Controlled Local Memory Management."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from backend.app.core.security import verify_session_token
from backend.app.services.memory_service import memory_service
from backend.app.storage.models import MemoryRecord

router = APIRouter(prefix="/api/v1/memory", tags=["User-Controlled Memory"])


class MemoryCreateRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=120, description="Memory key or topic")
    content: str = Field(..., min_length=1, description="Memory content")
    category: str = Field(default="preference", description="Category: preference, snippet, project, custom")


class MemoryListResponse(BaseModel):
    count: int
    memories: List[MemoryRecord]


@router.get(
    "",
    response_model=MemoryListResponse,
    dependencies=[Depends(verify_session_token)],
    summary="List stored local memories with optional search",
)
def list_memories(
    q: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
) -> MemoryListResponse:
    records = memory_service.list(search=q, category=category, limit=limit)
    return MemoryListResponse(count=len(records), memories=records)


@router.post(
    "",
    response_model=MemoryRecord,
    dependencies=[Depends(verify_session_token)],
    summary="Store or update a local user memory",
)
def save_memory(req: MemoryCreateRequest) -> MemoryRecord:
    return memory_service.set(
        key=req.key.strip(),
        content=req.content.strip(),
        category=req.category.strip(),
    )


@router.delete(
    "/{memory_id}",
    dependencies=[Depends(verify_session_token)],
    summary="Delete a single stored memory",
)
def delete_memory(memory_id: str) -> Dict[str, Any]:
    success = memory_service.delete(memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record '{memory_id}' not found.",
        )
    return {"status": "deleted", "id": memory_id}


@router.post(
    "/clear",
    dependencies=[Depends(verify_session_token)],
    summary="Purge and wipe all stored user memories",
)
def clear_all_memories() -> Dict[str, Any]:
    purged_count = memory_service.clear()
    return {"status": "cleared", "purged_count": purged_count}


@router.get(
    "/export",
    dependencies=[Depends(verify_session_token)],
    summary="Export all memories for user backup",
)
def export_memories() -> Dict[str, Any]:
    records = memory_service.export_all()
    return {
        "status": "success",
        "total_records": len(records),
        "data": records,
    }
