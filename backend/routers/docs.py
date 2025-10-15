from fastapi import APIRouter, UploadFile, File
from pypdf import PdfReader
from services.vectorstore import get_vectorstore


router = APIRouter()
chroma = get_vectorstore()


@router.get("/list")
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


@router.delete("/delete/{doc_id}")
async def delete_doc(doc_id: str):
    try:
        chroma._collection.delete(where={"doc": doc_id})
        return {"status": "ok", "deleted": doc_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/upload")
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


