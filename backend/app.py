from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader
import httpx, os, uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: Optional[str] = Field(None, description="User message")
    query: Optional[str] = Field(None, description="Legacy key support")
    top_k: int = 6
    must_cite: bool = True

    @property
    def text(self) -> str:
        """Return whichever field is set"""
        return self.message or self.query or ""


class Source(BaseModel):
    doc: str
    page: int
    score: float = 0.0
    snippet: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []



#Embeddings + ChromaDB setup
hf = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
chroma = Chroma(persist_directory="./db", embedding_function=hf)



# List documents
@app.get("/list")
async def list_docs():
    try:
        results = chroma._collection.get(include=["metadatas"])
        docs = {}

        for m in results["metadatas"]:
            doc_name = m.get("doc", "").strip()
            if not doc_name:
                continue
            if doc_name not in docs:
                docs[doc_name] = {"doc_id": doc_name, "filename": doc_name, "pages": 0}
            docs[doc_name]["pages"] += 1

        return {"status": "ok", "docs": list(docs.values())}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# Delete document
@app.delete("/delete/{doc_id}")
async def delete_doc(doc_id: str):
    try:
        chroma._collection.delete(where={"doc": doc_id})
        return {"status": "ok", "deleted": doc_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Upload PDF and embed
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        reader = PdfReader(file.file)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({
                "page_content": text,
                "metadata": {"doc": file.filename, "page": i + 1},
            })

        chroma.add_texts(
            texts=[p["page_content"] for p in pages],
            metadatas=[p["metadata"] for p in pages],
        )

        return {
            "status": "ok",
            "doc_id": file.filename,
            "filename": file.filename,
            "pages": len(pages),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(req: dict):
     
    user_text = ""
    if "messages" in req:
        messages = req.get("messages", [])
        for m in reversed(messages):
            if m.get("role") == "user" and m.get("content"):
                user_text = m["content"]
                break
    else:
        user_text = req.get("message") or req.get("query") or ""

    user_text = user_text.strip()
    if not user_text:
        return ChatResponse(answer="⚠️ No message provided.", sources=[])

    # Retrieve relevant chunks from Chroma 
    try:
        top_k = req.get("top_k", 6)
        results = chroma.similarity_search(user_text, k=top_k)
        context_text = "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        return ChatResponse(answer=f"Vector DB error: {str(e)}", sources=[])

    # Build the prompt including optional rolling summary
    summary_text = req.get("summary", "").strip()
    system_summary_block = (
        f"Conversation summary (may be incomplete, prefer user’s latest message):\n{summary_text}\n\n"
        if summary_text
        else ""
    )

    prompt_text = (
        f"{system_summary_block}Context:\n{context_text}\n\n"
        f"Question: {user_text}\n"
        f"Answer concisely with citations from the provided context."
    )

    #  Call OpenRouter 
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "alibaba/tongyi-deepresearch-30b-a3b:free",
                    "messages": [{"role": "user", "content": prompt_text}],
                },
                timeout=30.0,
            )

        data = resp.json()

        # parse the model response
        answer = None
        if "choices" in data and len(data["choices"]) > 0:
            answer = data["choices"][0].get("message", {}).get("content")
        if not answer and "output" in data and len(data["output"]) > 0:
            out = data["output"][0]
            if "content" in out and len(out["content"]) > 0:
                answer = out["content"][0].get("text")
        if not answer:
            return ChatResponse(
                answer=f"Error: unexpected model response {data}", sources=[]
            )

    except Exception as e:
        return ChatResponse(answer=f"Error fetching model response: {e}", sources=[])

    # Format sources for frontend 
    sources = []
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
