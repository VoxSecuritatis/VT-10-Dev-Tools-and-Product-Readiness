# ================================================================
# Vector Memory Tests
# ================================================================
# Objective:
#       Verify the Chroma-backed add/query round trip, using a
#       temporary directory so tests never touch the project's real
#       data/chroma_store.
# Notes:
#   - First run in a fresh environment may need network access once
#     to download Chroma's default embedding model; it is cached
#     locally afterward.
# ================================================================

import memory.vector_store as vector_store


def test_add_and_query_finding(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(vector_store, "CHROMA_PERSIST_DIR", tmp_path / "chroma_store")

    vector_store.add_finding(domain="fintech", agent="research_agent", text="digital banks are growing")
    result = vector_store.query_similar(domain="fintech", agent="research_agent")

    assert "digital banks are growing" in result


def test_query_similar_returns_empty_string_when_no_findings(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(vector_store, "CHROMA_PERSIST_DIR", tmp_path / "chroma_store")

    result = vector_store.query_similar(domain="fintech", agent="research_agent")

    assert result == ""


def test_query_similar_is_scoped_by_agent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(vector_store, "CHROMA_PERSIST_DIR", tmp_path / "chroma_store")

    vector_store.add_finding(domain="fintech", agent="research_agent", text="market trend text")
    vector_store.add_finding(domain="fintech", agent="funding_advisor", text="funding program text")

    research_result = vector_store.query_similar(domain="fintech", agent="research_agent")

    assert "market trend text" in research_result
    assert "funding program text" not in research_result
