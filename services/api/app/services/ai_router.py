"""Hybrid AI router for SILIQUESTA."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.error import URLError

from app.services.local_llm import LocalLLMService
from app.services.local_reasoner import LocalReasoner
from app.services.rag_system import RAGSystem, RetrievalDoc

logger = logging.getLogger(__name__)


@dataclass
class HybridAIResult:
    response: str
    source: str
    confidence: float
    route: str
    retrieved_titles: list[str] = field(default_factory=list)


class HybridAIRouter:
    """Route AI requests to the fastest trustworthy local subsystem."""

    def __init__(self, rag_system: RAGSystem):
        self.rag = rag_system
        self.reasoner = LocalReasoner()
        self.local_llm = LocalLLMService()

    async def respond(self, message: str, context: dict | None = None) -> HybridAIResult:
        context = context or {}
        docs = self.rag.retrieve_documents(message, context=context, top_k=4)
        titles = list(dict.fromkeys(doc.title for doc in docs))

        if self.reasoner.can_answer_directly(message, context):
            result = self.reasoner.answer(message, context)
            return HybridAIResult(
                response=result.answer,
                source="siliquesta-local-engine",
                confidence=result.confidence,
                route=result.route,
                retrieved_titles=titles,
            )

        if self._prefers_llm(message):
            llm_result = await self._try_local_llm(message, context, docs)
            if llm_result is not None:
                return llm_result

        rag_answer = self._rag_grounded_answer(message, context, docs)
        return HybridAIResult(
            response=rag_answer,
            source="siliquesta-rag",
            confidence=0.74 if docs else 0.58,
            route="rag-local",
            retrieved_titles=titles,
        )

    def _prefers_llm(self, message: str) -> bool:
        msg = message.lower()
        llm_terms = (
            "generate",
            "write",
            "rtl",
            "verilog",
            "spice netlist",
            "netlist",
            "explain",
            "why",
            "how does",
            "document",
            "architecture",
            "pipeline",
            "debug",
            "fix",
        )
        return any(term in msg for term in llm_terms) or len(message.split()) > 16

    async def _try_local_llm(
        self,
        message: str,
        context: dict,
        docs: list[RetrievalDoc],
    ) -> HybridAIResult | None:
        formatted_context = self._format_context(context)
        retrieval = self._format_retrieval(docs)
        system_prompt = (
            "You are SILIQUESTA AI, a semiconductor and EDA copilot. "
            "Answer with precise engineering guidance, not generic assistant chatter. "
            "Prefer retrieved facts and visible circuit context. "
            "If information is uncertain, say what should be verified with SPICE."
            f"\n\nCurrent design context:\n{formatted_context}\n\nRetrieved knowledge:\n{retrieval}"
        )
        try:
            response = await self.local_llm.generate(prompt=message, system_prompt=system_prompt, temperature=0.12)
            if response:
                return HybridAIResult(
                    response=response,
                    source="siliquesta-ollama",
                    confidence=0.82 if docs else 0.72,
                    route="rag-llm",
                    retrieved_titles=[doc.title for doc in docs],
                )
        except URLError:
            logger.info("Local LLM unavailable; falling back to retrieval/local engine.")
        except Exception as exc:
            logger.warning("Local LLM failed, using fallback path: %s", exc)
        return None

    def _rag_grounded_answer(self, message: str, context: dict, docs: list[RetrievalDoc]) -> str:
        summary = self.reasoner.answer("summary", context).answer
        if not docs:
            return summary
        retrieved = []
        for doc in docs[:3]:
            retrieved.append(f"{doc.title}: {doc.content}")
        return (
            f"{summary}\n\n"
            "Relevant local knowledge:\n"
            + "\n".join(f"- {item}" for item in retrieved)
            + "\n\nUse the retrieved guidance above as design context, and confirm signoff-critical changes with SPICE."
        )

    def _format_context(self, context: dict) -> str:
        if not context:
            return "No active design context."
        rows = []
        for key in ("wn", "wp", "vdd", "temp", "cl_ff", "tech_node", "corner", "freq", "power", "delay"):
            if key in context and context[key] is not None:
                rows.append(f"- {key}: {context[key]}")
        return "\n".join(rows) if rows else "No active design context."

    def _format_retrieval(self, docs: list[RetrievalDoc]) -> str:
        if not docs:
            return "No retrieved knowledge."
        return "\n\n".join(f"[{doc.title}] {doc.content}" for doc in docs)
