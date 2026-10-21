"""Unit and Security Tests for Initial Real Tools."""

import pytest
from backend.app.agent.orchestrator import orchestrator
from backend.app.tools.registry import (
    AppStatusTool,
    DraftGeneratorTool,
    ScopedFileReaderTool,
    TaskHistoryTool,
    TextDiffTool,
    TextSummarizerTool,
    tool_registry,
)


@pytest.mark.asyncio
async def test_file_reader_tool_reads_valid_workspace_file():
    """Verify ScopedFileReaderTool reads authorized relative workspace files."""
    reader = ScopedFileReaderTool()
    # Read SKILL.md
    result = await reader.execute({"relative_path": "SKILL.md"})
    assert result["bytes_read"] > 0
    assert "AitMate" in result["content"]


@pytest.mark.asyncio
async def test_file_reader_blocks_directory_traversal():
    """Security rule: Relative paths containing .. are rejected with PermissionError."""
    reader = ScopedFileReaderTool()
    with pytest.raises(PermissionError):
        await reader.execute({"relative_path": "../../../Windows/System32/drivers/etc/hosts"})


@pytest.mark.asyncio
async def test_file_reader_blocks_absolute_paths():
    """Security rule: Absolute paths outside the workspace are rejected with PermissionError."""
    reader = ScopedFileReaderTool()
    with pytest.raises(PermissionError):
        await reader.execute({"relative_path": "C:/Windows/win.ini"})


@pytest.mark.asyncio
async def test_text_diff_tool_produces_unified_diff():
    """Verify TextDiffTool computes unified line-by-line diffs for previews."""
    differ = TextDiffTool()
    orig = "line 1\nline 2\nline 3\n"
    modified = "line 1\nline 2 modified\nline 3\n"
    res = await differ.execute(
        {
            "original_text": orig,
            "modified_text": modified,
            "filename": "sample.py",
        }
    )
    assert res["has_changes"] is True
    assert "+line 2 modified" in res["diff_text"]
    assert "-line 2" in res["diff_text"]


@pytest.mark.asyncio
async def test_task_history_tool_retrieves_records():
    """Verify TaskHistoryTool queries SQLite and returns local task records."""
    # Ensure at least one task exists
    orchestrator.create_task("History test task")

    history_tool = TaskHistoryTool()
    res = await history_tool.execute({"limit": 5})
    assert res["count"] >= 1
    assert any("History test task" in t["instruction"] for t in res["tasks"])


@pytest.mark.asyncio
async def test_draft_generator_tool():
    """Verify DraftGeneratorTool creates draft with is_sent=False."""
    drafter = DraftGeneratorTool()
    res = await drafter.execute(
        {
            "topic": "Status Report",
            "recipient": "Team Lead",
            "instructions": "Be concise",
        }
    )
    assert res["is_sent"] is False
    assert "Draft Briefing: Status Report" in res["draft_body"]
