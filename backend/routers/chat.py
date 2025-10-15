from fastapi import APIRouter
from typing import List
from services.vectorstore import get_vectorstore
from services.llm import complete_chat
from schemas.chat import ChatRequest, ChatResponse, Source


router = APIRouter()
chroma = get_vectorstore()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: dict):
    # Extract user message from messages array (frontend format)
    user_text = ""
    if "messages" in req:
        messages = req.get("messages", [])
        for m in reversed(messages):
            if m.get("role") == "user" and m.get("content"):
                user_text = m["content"]
                break
    else:
        # Fallback to direct message/query fields
        user_text = req.get("message") or req.get("query") or ""

    user_text = user_text.strip()
    if not user_text:
        return ChatResponse(answer="⚠️ No message provided.", sources=[])

    try:
        top_k = req.get("top_k", 6)
        results = chroma.similarity_search(user_text, k=top_k)
        context_text = "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        return ChatResponse(answer=f"Vector DB error: {str(e)}", sources=[])

    # Build the prompt including optional rolling summary
    summary_text = req.get("summary", "").strip()
    system_summary_block = (
        f"Conversation summary (may be incomplete, prefer user's latest message):\n{summary_text}\n\n"
        if summary_text
        else ""
    )

    prompt_text = (
        f"{system_summary_block}Context:\n{context_text}\n\n"
        f"Question: {user_text}\n"
        f"Answer concisely with citations from the provided context."
    )

    try:
        answer = await complete_chat(prompt_text)
    except Exception as e:
        return ChatResponse(answer=f"Error fetching model response: {e}", sources=[])

    sources: List[Source] = []
    for doc in results:
        meta = doc.metadata
        sources.append(
            Source(
                doc=meta.get("doc", "unknown"),
                page=meta.get("page", -1),
                snippet=(doc.page_content or "")[:200],
            )
        )

    return ChatResponse(answer=answer, sources=sources)


