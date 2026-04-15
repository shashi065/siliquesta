"""Local retrieval system for SILIQUESTA AI."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - optional at runtime
    TfidfVectorizer = None
    cosine_similarity = None

logger = logging.getLogger(__name__)


@dataclass
class RetrievalDoc:
    id: str
    title: str
    content: str
    tags: list[str]
    score: float = 0.0
    source: str = "builtin"


class RAGSystem:
    """
    Lightweight local retrieval layer.

    This is intentionally fully local and dependency-light:
    - TF-IDF ranking when scikit-learn is available
    - token overlap fallback otherwise
    - persistent user/design/interactions store on disk
    """

    def __init__(self, index_path: str = "./data/faiss_index"):
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_path = self.index_path / "knowledge.json"
        self.interactions_path = self.index_path / "interactions.json"
        self.designs_path = self.index_path / "design_memory.json"
        self.documents: list[RetrievalDoc] = self._load_documents()
        self.vectorizer = None
        self.doc_matrix = None
        self._rebuild_index()

    def _builtin_documents(self) -> list[RetrievalDoc]:
        return [
            RetrievalDoc(
                id="builtin-cmos-inverter",
                title="CMOS Inverter Design Guide",
                content=(
                    "CMOS inverter fundamentals. Balanced switching usually appears near WP/WN ratio 2.0 to 2.5. "
                    "Propagation delay scales with load capacitance and falls with stronger drive current. "
                    "Dynamic power rises with capacitance, voltage squared, and switching frequency. "
                    "Low VDD reduces dynamic power but can collapse switching margin in slow corners."
                ),
                tags=["inverter", "cmos", "delay", "power", "ratio"],
                source="builtin",
            ),
            RetrievalDoc(
                id="builtin-pvt",
                title="PVT Corner Guidelines",
                content=(
                    "TT is the reference operating point. SS is worst for speed and often limits setup timing. "
                    "FF increases speed and leakage. Temperature rise reduces mobility and hurts frequency. "
                    "Low voltage and slow process corners can become non-switching points in real SPICE sweeps."
                ),
                tags=["pvt", "corners", "ss", "tt", "ff", "temperature", "voltage"],
                source="builtin",
            ),
            RetrievalDoc(
                id="builtin-power",
                title="Power Optimization Techniques",
                content=(
                    "The strongest first-order power knob is VDD. Lowering VDD reduces dynamic power quadratically "
                    "but also cuts overdrive and frequency. Capacitance reduction improves both speed and energy. "
                    "Selective upsizing on critical paths is safer than global upsizing."
                ),
                tags=["power", "optimization", "energy", "vdd", "capacitance"],
                source="builtin",
            ),
            RetrievalDoc(
                id="builtin-timing",
                title="Timing Closure Playbook",
                content=(
                    "Use SS and hot temperature to estimate timing risk. Increase drive only on critical stages. "
                    "Reduce fanout and wire load before broad voltage increases. "
                    "Validate timing fixes against power and reliability, not frequency alone."
                ),
                tags=["timing", "closure", "critical path", "delay"],
                source="builtin",
            ),
            RetrievalDoc(
                id="builtin-reliability",
                title="Reliability and Aging",
                content=(
                    "NBTI shifts PMOS threshold over lifetime. HCI hurts short-channel NMOS current. "
                    "Electromigration risk rises with current density and temperature. "
                    "High VDD and high temperature accelerate aging and reduce long-term margin."
                ),
                tags=["reliability", "aging", "nbti", "hci", "electromigration"],
                source="builtin",
            ),
            RetrievalDoc(
                id="builtin-spice",
                title="SPICE Verification Principles",
                content=(
                    "SPICE-verified data should be preferred for signoff-style interpretation. "
                    "If a point does not switch in transient simulation, report it honestly as non-switching rather than extrapolating a fake frequency. "
                    "Corner sweeps should preserve source metadata and switching validity."
                ),
                tags=["spice", "verification", "waveform", "signoff"],
                source="builtin",
            ),
        ]

    def _load_json_docs(self, path: Path, source: str) -> list[RetrievalDoc]:
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not load retrieval store %s: %s", path, exc)
            return []

        docs: list[RetrievalDoc] = []
        if isinstance(raw, list):
            for idx, item in enumerate(raw):
                if not isinstance(item, dict):
                    continue
                docs.append(
                    RetrievalDoc(
                        id=str(item.get("id") or f"{source}-{idx+1}"),
                        title=str(item.get("title") or f"{source.title()} #{idx+1}"),
                        content=str(item.get("content") or ""),
                        tags=[str(tag) for tag in item.get("tags", [])],
                        source=source,
                    )
                )
        return docs

    def _load_documents(self) -> list[RetrievalDoc]:
        documents = self._builtin_documents()
        documents.extend(self._load_json_docs(self.knowledge_path, "knowledge"))
        documents.extend(self._load_json_docs(self.interactions_path, "interaction"))
        documents.extend(self._load_json_docs(self.designs_path, "design-memory"))
        return documents

    def _rebuild_index(self) -> None:
        if not self.documents:
            self.vectorizer = None
            self.doc_matrix = None
            return
        if TfidfVectorizer is None:
            self.vectorizer = None
            self.doc_matrix = None
            return
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        corpus = [self._document_text(doc) for doc in self.documents]
        self.doc_matrix = self.vectorizer.fit_transform(corpus)

    def _document_text(self, doc: RetrievalDoc) -> str:
        return f"{doc.title}\n{' '.join(doc.tags)}\n{doc.content}"

    def _context_documents(self, context: dict | None) -> list[RetrievalDoc]:
        if not context:
            return []
        docs: list[RetrievalDoc] = []
        parts: list[str] = []
        for key in ("wn", "wp", "vdd", "temp", "cl_ff", "tech_node", "corner", "freq", "power", "delay"):
            if key in context and context[key] is not None:
                parts.append(f"{key}={context[key]}")
        if parts:
            docs.append(
                RetrievalDoc(
                    id="context-operating-point",
                    title="Current Operating Point",
                    content="Current design context: " + ", ".join(parts),
                    tags=["context", "operating-point", "design"],
                    source="context",
                )
            )
        if context.get("spice_verified") is True:
            docs.append(
                RetrievalDoc(
                    id="context-spice",
                    title="Current Run Is SPICE Verified",
                    content="The latest visible design state is SPICE verified and should be treated as higher-confidence evidence.",
                    tags=["context", "spice", "verified"],
                    source="context",
                )
            )
        return docs

    def retrieve_documents(self, query: str, context: dict | None = None, top_k: int = 4) -> list[RetrievalDoc]:
        docs = [*self.documents, *self._context_documents(context)]
        if not docs:
            return []
        if self.vectorizer is not None and self.doc_matrix is not None and len(docs) == len(self.documents):
            query_vec = self.vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self.doc_matrix).flatten()
            ranked = sorted(
                (
                    RetrievalDoc(
                        id=doc.id,
                        title=doc.title,
                        content=doc.content,
                        tags=list(doc.tags),
                        source=doc.source,
                        score=float(score),
                    )
                    for doc, score in zip(self.documents, scores)
                ),
                key=lambda doc: doc.score,
                reverse=True,
            )
            return [doc for doc in ranked[:top_k] if doc.score > 0.01]

        query_terms = {term for term in query.lower().split() if len(term) > 2}
        ranked: list[RetrievalDoc] = []
        for doc in docs:
            hay = self._document_text(doc).lower()
            score = 0.0
            for term in query_terms:
                score += hay.count(term)
            if doc.source == "context":
                score += 1.25
            if score > 0:
                ranked.append(
                    RetrievalDoc(
                        id=doc.id,
                        title=doc.title,
                        content=doc.content,
                        tags=list(doc.tags),
                        source=doc.source,
                        score=score,
                    )
                )
        ranked.sort(key=lambda doc: doc.score, reverse=True)
        return ranked[:top_k]

    def retrieve(self, query: str, top_k: int = 4, context: dict | None = None) -> str:
        docs = self.retrieve_documents(query=query, context=context, top_k=top_k)
        if not docs:
            return "No relevant knowledge found."
        blocks = []
        for doc in docs:
            blocks.append(f"[{doc.title}] {doc.content}")
        return "\n\n---\n\n".join(blocks)

    def add_knowledge(self, title: str, content: str, tags: List[str]) -> None:
        self._append_json_doc(
            self.knowledge_path,
            {
                "id": f"knowledge-{len(self.documents)+1}",
                "title": title,
                "content": content,
                "tags": tags,
            },
        )

    def add_interaction(self, question: str, answer: str, context: dict | None = None) -> None:
        title = f"AI Interaction: {question[:60].strip()}"
        parts = [f"User question: {question}", f"AI answer: {answer}"]
        if context:
            ctx = ", ".join(f"{k}={v}" for k, v in context.items() if v is not None)
            if ctx:
                parts.append(f"Context: {ctx}")
        self._append_json_doc(
            self.interactions_path,
            {
                "id": f"interaction-{abs(hash(question + answer))}",
                "title": title,
                "content": "\n".join(parts),
                "tags": ["interaction", "ai", "design-memory"],
            },
        )

    def add_design_memory(self, name: str, content: str, tags: list[str] | None = None) -> None:
        self._append_json_doc(
            self.designs_path,
            {
                "id": f"design-{abs(hash(name + content))}",
                "title": name,
                "content": content,
                "tags": tags or ["design-memory"],
            },
        )

    def _append_json_doc(self, path: Path, item: dict) -> None:
        try:
            existing = []
            if path.exists():
                existing = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            existing.append(item)
            path.write_text(json.dumps(existing[-500:], indent=2), encoding="utf-8")
            self.documents = self._load_documents()
            self._rebuild_index()
        except Exception as exc:
            logger.error("Could not persist retrieval item to %s: %s", path, exc)
