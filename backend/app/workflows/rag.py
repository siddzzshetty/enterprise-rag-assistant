from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - optional dependency
    END = None
    StateGraph = None

from backend.app.services.knowledge_base import KnowledgeBaseService, RetrievedChunk


@dataclass
class RagState:
    client_id: int
    project_id: int
    user_id: int
    question: str
    rewritten_query: str = ""
    candidate_chunks: list[RetrievedChunk] | None = None
    reranked_chunks: list[RetrievedChunk] | None = None
    answer: str = ""
    verified_answer: str = ""
    verification_status: str = "pending"
    verification_notes: str = ""
    sources: list[dict[str, Any]] | None = None
    top_document_id: int | None = None
    top_document_name: str = ""
    top_chunk_score: float = 0.0


def _asdict(state: RagState) -> dict[str, Any]:
    """Convert RagState to dict, handling non-serializable fields."""
    result = asdict(state)
    # Convert RetrievedChunk objects to serializable format
    if state.candidate_chunks:
        result["candidate_chunks"] = [asdict(c) if hasattr(c, "__dict__") else c for c in state.candidate_chunks]
    if state.reranked_chunks:
        result["reranked_chunks"] = [asdict(c) if hasattr(c, "__dict__") else c for c in state.reranked_chunks]
    return result


class IntelligentRAGWorkflow:
    def __init__(self, service: KnowledgeBaseService) -> None:
        self.service = service
        self._graph = self._build_graph() if StateGraph is not None else None

    def run(self, client_id: int, project_id: int, user_id: int, question: str) -> dict[str, Any]:
        state = RagState(client_id=client_id, project_id=project_id, user_id=user_id, question=question)
        if self._graph is not None:
            # Convert to dict for langgraph
            state_dict = _asdict(state)
            result = self._graph.invoke(state_dict)
        else:
            # For fallback, use dict directly
            state_dict = asdict(state) if hasattr(state, "__dict__") else {"client_id": client_id, "project_id": project_id, "user_id": user_id, "question": question}
            result = self._fallback_run(state_dict)
        return self._finalize(result)

    def _build_graph(self):
        graph = StateGraph(dict)
        graph.add_node("understand_query", self._understand_query)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("rerank_context", self._rerank_context)
        graph.add_node("generate_answer", self._generate_answer)
        graph.add_node("verify_answer", self._verify_answer)
        graph.add_node("package_response", self._package_response)
        graph.set_entry_point("understand_query")
        graph.add_edge("understand_query", "retrieve_context")
        graph.add_edge("retrieve_context", "rerank_context")
        graph.add_edge("rerank_context", "generate_answer")
        graph.add_edge("generate_answer", "verify_answer")
        graph.add_edge("verify_answer", "package_response")
        graph.add_edge("package_response", END)
        return graph.compile()

    def _fallback_run(self, state: dict[str, Any]) -> dict[str, Any]:
        state = self._understand_query(state)
        state = self._retrieve_context(state)
        state = self._rerank_context(state)
        state = self._generate_answer(state)
        state = self._verify_answer(state)
        return self._package_response(state)

    def _understand_query(self, state: dict[str, Any]) -> dict[str, Any]:
        state["rewritten_query"] = self.service.rewrite_query(state["question"])
        return state

    def _retrieve_context(self, state: dict[str, Any]) -> dict[str, Any]:
        state["candidate_chunks"] = self.service.retrieve_chunks(
            state["client_id"],
            state["project_id"],
            state["rewritten_query"],
            limit=8,
        )
        return state

    def _rerank_context(self, state: dict[str, Any]) -> dict[str, Any]:
        chunks = state.get("candidate_chunks") or []
        state["reranked_chunks"] = self.service.rerank_chunks(state["rewritten_query"], chunks)
        return state

    def _generate_answer(self, state: dict[str, Any]) -> dict[str, Any]:
        project = self.service.get_project(state["client_id"], state["project_id"])
        chunks = state.get("reranked_chunks") or []
        state["answer"] = self.service.generate_answer(
            question=state["question"],
            rewritten_query=state["rewritten_query"],
            project=project,
            chunks=chunks,
        )
        return state

    def _verify_answer(self, state: dict[str, Any]) -> dict[str, Any]:
        chunks = state.get("reranked_chunks") or []
        verified_answer, verification_status, verification_notes = self.service.verify_answer(
            question=state["question"],
            rewritten_query=state["rewritten_query"],
            answer=state["answer"],
            chunks=chunks,
        )
        state["verified_answer"] = verified_answer
        state["verification_status"] = verification_status
        state["verification_notes"] = verification_notes
        return state

    def _package_response(self, state: dict[str, Any]) -> dict[str, Any]:
        chunks = state.get("reranked_chunks") or []
        sources = [self.service._chunk_source(chunk) for chunk in chunks]
        top_chunk = chunks[0] if chunks else None
        state["sources"] = sources
        state["top_document_id"] = top_chunk.document_id if top_chunk else None
        state["top_document_name"] = top_chunk.document_name if top_chunk else ""
        state["top_chunk_score"] = top_chunk.score if top_chunk else 0.0
        state["answer"] = state.get("verified_answer") or state.get("answer") or ""
        self.service.log_retrieval_event(
            client_id=state["client_id"],
            project_id=state["project_id"],
            user_id=state["user_id"],
            original_query=state["question"],
            rewritten_query=state["rewritten_query"],
            top_document_id=state["top_document_id"],
            top_document_name=state["top_document_name"],
            top_chunk_score=state["top_chunk_score"],
            verification_status=state["verification_status"],
        )
        self.service.save_chat_response(
            client_id=state["client_id"],
            project_id=state["project_id"],
            user_id=state["user_id"],
            question=state["question"],
            answer=state["answer"],
            sources=sources,
        )
        return state

    def _finalize(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "query": state["rewritten_query"],
            "original_query": state["question"],
            "answer": state["answer"],
            "project_id": state["project_id"],
            "document_id": state.get("top_document_id"),
            "sources": state.get("sources", []),
            "verification_status": state.get("verification_status", "pending"),
            "verification_notes": state.get("verification_notes", ""),
        }
