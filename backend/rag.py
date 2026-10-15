"""Assistente 'RAG local': recuperação por palavras-chave (BM25 simplificado)
sobre data/knowledge.json. Nenhum dado sai do servidor; sem IA externa."""
import json
import math
import re
import unicodedata
from collections import Counter

STOP = set("a o as os um uma de do da dos das em no na nos nas para por com sem e ou que como eu me meu minha se ao aos ja mais muito pode posso qual quais onde quando".split())


def norm(s: str) -> list:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return [t for t in re.findall(r"[a-z0-9]+", s) if t not in STOP]


class LocalRAG:
    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            kb = json.load(f)
        self.fallback = kb["fallback"]
        self.docs = kb["entradas"]
        self.tokens = []
        for d in self.docs:
            toks = norm(d["titulo"]) * 3 + [t for p in d["palavras"] for t in norm(p)] * 2 + norm(d["texto"])
            self.tokens.append(Counter(toks))
        n = len(self.docs)
        df = Counter(t for c in self.tokens for t in c)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.avg = sum(sum(c.values()) for c in self.tokens) / n

    def search(self, query: str, k: int = 2):
        q = norm(query)
        scored = []
        for doc, c in zip(self.docs, self.tokens):
            ln = sum(c.values())
            s = 0.0
            for t in set(q):
                f = c.get(t, 0)
                if f:
                    s += self.idf.get(t, 0) * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * ln / self.avg))
            if s > 0:
                scored.append((s, doc))
        scored.sort(key=lambda x: -x[0])
        return scored[:k]

    def answer(self, query: str) -> dict:
        hits = self.search(query)
        if not hits or hits[0][0] < 1.0:
            return {"resposta": self.fallback, "fontes": []}
        parts = [hits[0][1]["texto"]]
        if len(hits) > 1 and hits[1][0] > 0.6 * hits[0][0]:
            parts.append(hits[1][1]["texto"])
        parts.append("Em risco imediato, ligue 190. Esta é uma orientação informativa e não substitui advogada(o) ou defensoria.")
        return {"resposta": "\n\n".join(parts), "fontes": [h[1]["titulo"] for h in hits if h[0] >= 1.0]}
