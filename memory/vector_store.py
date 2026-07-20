# ================================================================
# Vector Memory Store
# ================================================================
# Objective:
#       Persist and retrieve agent findings (research, funding) in a
#       local Chroma vector store, keyed by domain and agent, so later
#       runs or feedback-loop passes on the same domain can reuse prior
#       context instead of starting from nothing.
# Inputs:
#       - domain, agent name, and finding text to store or query
# Outputs:
#       - Documents persisted under config.CHROMA_PERSIST_DIR
# Notes:
#   - A fresh PersistentClient is opened per call rather than kept as
#     module-level state; this project's call volume is small enough
#     that the extra open cost is negligible, and it avoids hidden
#     global mutable state.
# ================================================================

import uuid

import chromadb

from config import CHROMA_PERSIST_DIR

COLLECTION_NAME = "agent_findings"


def get_collection() -> chromadb.Collection:
    """Open (creating if needed) the local persistent Chroma collection."""
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    return client.get_or_create_collection(COLLECTION_NAME)


def add_finding(domain: str, agent: str, text: str) -> None:
    """Store an agent's finding for a domain in the vector store."""
    collection = get_collection()
    collection.add(
        documents=[text],
        metadatas=[{"domain": domain, "agent": agent}],
        ids=[str(uuid.uuid4())],
    )


def query_similar(domain: str, agent: str, n_results: int = 3) -> str:
    """Return prior findings for a domain/agent pair joined into one string, or "" if none exist."""
    collection = get_collection()
    if collection.count() == 0:
        return ""
    results = collection.query(
        query_texts=[domain],
        n_results=n_results,
        where={"agent": agent},
    )
    documents = results.get("documents", [[]])[0]
    return "\n---\n".join(documents)
