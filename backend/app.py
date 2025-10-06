from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader
import httpx, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # open during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Models 
class ChatRequest(BaseModel):
    query: str
    top_k: int = 6
    must_cite: bool = True

class Source(BaseModel):
    doc: str
    page: int
    score: float = 0.0
    snippet: str = ""

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []

#Embeddings + Chroma
hf = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
chroma = Chroma(persist_directory="./db", embedding_function=hf)


# List Files Endpoint

@app.get("/list")
async def list_docs():
    try:
        results = chroma._collection.get(include=["metadatas"])
        docs = {}

        # Aggregate pages per document
        for m in results["metadatas"]:
            doc_name = m.get("doc", "").strip()
            if not doc_name:
                continue  # skip invalid entries

            if doc_name not in docs:
                docs[doc_name] = {"doc_id": doc_name, "filename": doc_name, "pages": 0}

            docs[doc_name]["pages"] += 1

        # Return as a list instead of dict for easier frontend mapping
        doc_list = list(docs.values())

        return {"status": "ok", "docs": doc_list}

    except Exception as e:
        return {"status": "error", "error": str(e)}



# Delete Files Endpoint
@app.delete("/delete/{doc_id}")
async def delete_doc(doc_id: str):
    try:
        chroma._collection.delete(where={"doc": doc_id})
        return {"status": "ok", "deleted": doc_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}




# Upload Endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        reader = PdfReader(file.file)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({
                "page_content": text,
                "metadata": {
                    "doc": file.filename,
                    "page": i + 1
                }
            })

        # Add to Chroma
        chroma.add_texts(
            texts=[p["page_content"] for p in pages],
            metadatas=[p["metadata"] for p in pages]
        )

        # Return info for frontend
        return {
            "status": "ok",
            "doc_id": file.filename,   # use filename as doc_id
            "filename": file.filename,
            "pages": len(pages),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

#Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    results = chroma.similarity_search(req.query, k=req.top_k)

    context_text = "\n\n".join([doc.page_content for doc in results])
    prompt_text = f"Context:\n{context_text}\n\nQuestion: {req.query}\nAnswer concisely with citations."

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat-v3.1:free",
                "messages": [{"role": "user", "content": prompt_text}],
            },
            timeout=30.0
        )

    data = resp.json()
    answer = data["choices"][0]["message"]["content"]

    sources = []
    for doc in results:
        meta = doc.metadata
        sources.append(Source(
            doc=meta.get("doc", "unknown"),
            page=meta.get("page", -1),
            snippet=doc.page_content[:200]  # preview snippet
        ))

    return ChatResponse(answer=answer, sources=sources)
