"""pgvector-backed long-term memory for AI agents.

Stores chat turns + embeddings, retrieves the most relevant past turns by
cosine similarity. Embedding model defaults to `nomic-embed-text` served by
Ollama (768 dims). Swap embedder + adjust vector dim in 0002_memory.sql if
you use a different model.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import asyncpg
import httpx


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")


@dataclass
class MemoryRecord:
    id: str
    persona: str
    role: str
    content: str
    similarity: float | None = None


async def embed(text: str, client: httpx.AsyncClient | None = None) -> list[float]:
    """Get an embedding from Ollama. Returns a list of floats."""
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        r = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
        )
        r.raise_for_status()
        return r.json()["embedding"]
    finally:
        if own:
            await client.aclose()


class Memory:
    """Async memory store backed by Postgres + pgvector."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None
        self._http: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        if self._http is not None:
            await self._http.aclose()

    async def store(self, persona: str, role: str, content: str) -> str:
        assert self._pool is not None and self._http is not None
        vec = await embed(content, client=self._http)
        vec_str = "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO agent_memories (persona, role, content, embedding)
                VALUES ($1, $2, $3, $4::vector)
                RETURNING id::text
                """,
                persona,
                role,
                content,
                vec_str,
            )
        return row["id"]

    async def recall(
        self, persona: str, query: str, k: int = 5
    ) -> list[MemoryRecord]:
        assert self._pool is not None and self._http is not None
        vec = await embed(query, client=self._http)
        vec_str = "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id::text, persona, role, content,
                       1 - (embedding <=> $1::vector) AS similarity
                FROM agent_memories
                WHERE persona = $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                vec_str,
                persona,
                k,
            )
        return [MemoryRecord(**dict(r)) for r in rows]
