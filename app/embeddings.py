from __future__ import annotations

import hashlib
import math
import re


def _tokenize(text: str) -> list[str]:
    normalized = text.lower()
    ascii_tokens = re.findall(r"[a-z0-9+#.]+", normalized)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", normalized)
    cjk_bigrams = [
        "".join(cjk_chars[index : index + 2])
        for index in range(len(cjk_chars) - 1)
    ]
    return [*ascii_tokens, *cjk_bigrams]


def _hash_index(token: str, dimension: int) -> int:
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % dimension


def embed_text(text: str, *, dimension: int = 384) -> list[float]:
    vector = [0.0] * dimension
    for token in _tokenize(text):
        vector[_hash_index(token, dimension)] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimension.")
    return sum(left_value * right_value for left_value, right_value in zip(left, right))
