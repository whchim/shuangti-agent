"""混合检索器：向量检索 + BM25 + RRF 融合"""
import math
from loguru import logger


class BM25Retriever:
    """简易 BM25 实现"""

    def __init__(self, documents: list[str]):
        self.documents = documents
        self.k1 = 1.5
        self.b = 0.75
        self._build_index()

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()

    def _build_index(self):
        self.tokenized_docs = [self._tokenize(doc) for doc in self.documents]
        self.avgdl = sum(len(td) for td in self.tokenized_docs) / max(len(self.tokenized_docs), 1)
        self.N = len(self.documents)

        self.df = {}
        for td in self.tokenized_docs:
            for token in set(td):
                self.df[token] = self.df.get(token, 0) + 1

        self.idf = {}
        for token, freq in self.df.items():
            self.idf[token] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1)

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        query_tokens = self._tokenize(query)
        scores = []
        for i, doc_tokens in enumerate(self.tokenized_docs):
            score = 0.0
            doc_len = len(doc_tokens)
            for token in query_tokens:
                if token in self.idf:
                    tf = doc_tokens.count(token)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / max(self.avgdl, 1))
                    score += self.idf[token] * numerator / denominator
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def reciprocal_rank_fusion(vector_results: list[tuple[int, float]],
                           bm25_results: list[tuple[int, float]],
                           k: int = 60) -> list[int]:
    """RRF 融合排序，返回文档索引列表"""
    rrf_scores = {}

    for rank, (idx, _) in enumerate(vector_results):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank + 1)

    for rank, (idx, _) in enumerate(bm25_results):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank + 1)

    sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)
    return sorted_indices


async def hybrid_retrieve(query: str, documents: list[str],
                          vector_results: list[tuple[int, float]],
                          top_k: int = 5) -> list[str]:
    """混合检索主入口"""
    if not documents:
        return []

    bm25 = BM25Retriever(documents)
    bm25_results = bm25.search(query, top_k=top_k)

    merged_indices = reciprocal_rank_fusion(vector_results, bm25_results)
    final_docs = [documents[i] for i in merged_indices[:top_k] if i < len(documents)]

    logger.info(f"混合检索: 向量 {len(vector_results)} + BM25 {len(bm25_results)} → Top-{len(final_docs)}")
    return final_docs
