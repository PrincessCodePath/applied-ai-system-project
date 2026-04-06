"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob
import string
from collections import defaultdict


def _tokenize(text):
    lowered = text.lower()
    for ch in "/<>[]{}()`":
        lowered = lowered.replace(ch, " ")
    words = []
    for raw in lowered.split():
        token = raw.strip(string.punctuation)
        if token:
            words.append(token)
    return words


def _paragraph_chunks(text):
    chunks = []
    for block in text.split("\n\n"):
        piece = block.strip()
        if piece:
            chunks.append(piece)
    return chunks


_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "which", "how", "do", "does", "did", "i", "we", "you", "me",
    "to", "of", "in", "it", "for", "on", "at", "by", "from", "as",
    "and", "or", "but", "if", "any", "there", "these", "those", "this", "that",
    "my", "your", "with", "not", "no", "can", "will", "should", "would", "could",
    "docs", "documentation",
})


def _content_tokens(query_text):
    return [t for t in _tokenize(query_text) if t not in _STOPWORDS]


class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        self.documents = self.load_documents()
        self.chunks = []
        for filename, text in self.documents:
            for piece in _paragraph_chunks(text):
                self.chunks.append((filename, piece))
        self.index = self.build_index(self.chunks)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, chunks):
        """Inverted index: token -> sorted list of chunk indices."""
        temp = defaultdict(set)
        for idx, (_, text) in enumerate(chunks):
            for token in set(_tokenize(text)):
                temp[token].add(idx)
        return {token: sorted(indices) for token, indices in temp.items()}

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """Score by counting content (non-stopword) query tokens in the text."""
        query_words = _content_tokens(query)
        if not query_words:
            return 0
        text_tokens = set(_tokenize(text))
        return sum(1 for w in query_words if w in text_tokens)

    def _evidence_sufficient(self, query, best_score):
        words = _content_tokens(query)
        if not words or best_score <= 0:
            return False
        if len(words) >= 5 and best_score < 2:
            return False
        return True

    def retrieve(self, query, top_k=3):
        """Top-k (filename, snippet) by score on paragraph chunks; empty if evidence is too weak."""
        query_words = _tokenize(query)
        if not query_words:
            return []

        focus = _content_tokens(query)
        lookup = focus if focus else query_words

        candidates = set()
        for w in lookup:
            for idx in self.index.get(w, []):
                candidates.add(idx)
        if not candidates:
            candidates = set(range(len(self.chunks)))

        scored = []
        for idx in candidates:
            fn, body = self.chunks[idx]
            s = self.score_document(query, body)
            scored.append((s, idx, fn, body))
        scored.sort(key=lambda x: (-x[0], x[2], x[1]))

        if not scored or not self._evidence_sufficient(query, scored[0][0]):
            return []

        out = []
        seen = set()
        for s, _, fn, body in scored:
            if len(out) >= top_k:
                break
            if s <= 0:
                continue
            key = (fn, body)
            if key in seen:
                continue
            seen.add(key)
            out.append((fn, body))
        return out

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
