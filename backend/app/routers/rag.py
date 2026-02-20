from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.rag.retrieve import retrieve as rag_retrieve
from backend.app.services.crop_recommendation import _gemini_call as gemini_call  # re-use your Gemini helper

router = APIRouter(prefix="/api/rag", tags=["rag"])

# ---------- Schemas ----------
class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language query")
    k: int = Field(4, ge=1, le=20, description="Number of chunks to retrieve")

class RagHit(BaseModel):
    score: float
    title: Optional[str] = None
    source: Optional[str] = None
    page: Optional[int] = None
    snippet: str

class RagSearchResponse(BaseModel):
    query: str
    results: List[RagHit]

class RagAnswerRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Question to answer from RAG corpus")
    k: int = Field(4, ge=1, le=12, description="Number of chunks to retrieve")
    target_language: str = Field("en", description="Answer language (e.g., 'en', 'hi')")

class RagAnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]  # [{title, source, page, score}]

# ---------- Endpoints ----------
@router.post("/search", response_model=RagSearchResponse)
def rag_search(req: RagSearchRequest):
    try:
        hits = rag_retrieve(req.query, k=req.k)
        results: List[RagHit] = []
        for h in hits:
            text = h.get("text") or ""
            snippet = (text[:500] + "…") if len(text) > 500 else text
            results.append(
                RagHit(
                    score=float(h.get("score") or 0.0),
                    title=h.get("title"),
                    source=h.get("source"),
                    page=h.get("page"),
                    snippet=snippet,
                )
            )
        return RagSearchResponse(query=req.query, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"rag search failed: {e}")

@router.post("/answer", response_model=RagAnswerResponse)
def rag_answer(req: RagAnswerRequest):
    """
    Retrieve top-k snippets and ask Gemini to answer USING ONLY those snippets.
    Returns the answer + a compact list of sources.
    """
    try:
        hits = rag_retrieve(req.question, k=req.k)
        if not hits:
            return RagAnswerResponse(
                answer="Sorry, I couldn't find anything relevant in the knowledge base.",
                sources=[],
            )

        # Build numbered context for lightweight citations [S1], [S2], ...
        numbered = []
        meta_list: List[Dict[str, Any]] = []
        for i, h in enumerate(hits, start=1):
            text = (h.get("text") or "").strip()
            title = h.get("title") or h.get("source") or f"Doc {i}"
            page = h.get("page")
            source = h.get("source")
            score = float(h.get("score") or 0.0)
            if not text:
                continue
            numbered.append(f"[S{i}] {title}{f', p.{page}' if page is not None else ''}\n{text}")
            meta_list.append({"label": f"S{i}", "title": title, "source": source, "page": page, "score": score})

        context = "\n\n".join(numbered)

        prompt = f"""You are KrishiMitra. Answer the user's question USING ONLY the sources below.
If the answer is not in the sources, say you don't know.
Cite with [S#] minimally.

Question: {req.question}

Sources:
{context}

Respond in {req.target_language}.
"""

        answer = gemini_call(prompt)  # your existing sync helper; okay to call directly
        return RagAnswerResponse(answer=answer.strip(), sources=meta_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"rag answer failed: {e}")
