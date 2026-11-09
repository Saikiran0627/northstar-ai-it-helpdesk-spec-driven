from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .security import scan_text


@dataclass(frozen=True)
class DocumentChunk:
    citation_id: str
    title: str
    source: str
    text: str
    score: float = 0.0
    flagged: bool = False


class KnowledgeBase:
    def __init__(self, kb_path: Path | str = "knowledge_base") -> None:
        self.kb_path = Path(kb_path)
        self.chunks: list[DocumentChunk] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self.load()

    def load(self) -> None:
        self.chunks = []
        if not self.kb_path.exists():
            return
        citation_index = 1
        for path in sorted(self.kb_path.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            title = self._extract_title(content, path)
            for chunk_text in self._chunk_markdown(content):
                scan = scan_text(chunk_text)
                self.chunks.append(DocumentChunk(
                    citation_id=f"N{citation_index}",
                    title=title,
                    source=str(path),
                    text=scan.safe_text.strip(),
                    flagged=scan.flagged,
                ))
                citation_index += 1
        if self.chunks:
            self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self._matrix = self._vectorizer.fit_transform([chunk.text for chunk in self.chunks])
        else:
            self._vectorizer = None
            self._matrix = None

    @staticmethod
    def _extract_title(content: str, path: Path) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return path.stem.replace("-", " ").title()

    @staticmethod
    def _chunk_markdown(content: str, max_chars: int = 1200) -> list[str]:
        blocks = [block.strip() for block in content.split("\n\n") if block.strip()]
        chunks: list[str] = []
        current = ""
        for block in blocks:
            if current and len(current) + len(block) + 2 > max_chars:
                chunks.append(current)
                current = block
            else:
                current = f"{current}\n\n{block}".strip()
        if current:
            chunks.append(current)
        return chunks

    def search(self, query: str, top_k: int = 4) -> tuple[list[DocumentChunk], float]:
        start = perf_counter()
        if not query.strip() or not self.chunks or self._vectorizer is None or self._matrix is None:
            return [], (perf_counter() - start) * 1000
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).ravel()
        ranked_indices = scores.argsort()[::-1][:top_k]
        results: list[DocumentChunk] = []
        for index in ranked_indices:
            score = float(scores[index])
            if score <= 0:
                continue
            chunk = self.chunks[int(index)]
            results.append(DocumentChunk(
                citation_id=chunk.citation_id,
                title=chunk.title,
                source=chunk.source,
                text=chunk.text,
                score=score,
                flagged=chunk.flagged,
            ))
        return results, (perf_counter() - start) * 1000

    @staticmethod
    def format_context(chunks: list[DocumentChunk]) -> str:
        lines = []
        for chunk in chunks:
            lines.append(f"[{chunk.citation_id}] {chunk.title} ({chunk.source})\n{chunk.text}")
        return "\n\n".join(lines)
