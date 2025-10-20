# RAG-Assistant

A simple Retrieval-Augmented Generation (RAG) assistant with:
- FastAPI backend using Chroma for local vector storage and HuggingFace embeddings
- React + Vite frontend with Prompt Kit-style chat UI (PromptInput, Message, ChatContainer)
- PDF upload, list, delete, and chat with cited sources


## Features
- Upload PDFs and embed them into Chroma
- List uploaded PDFs and delete by document id
- Ask questions; retrieves top-k chunks and calls OpenRouter for answers
- Shows citations with doc name and page
- Rolling chat window + lightweight conversation summary sent with each query


## Demo
Below is a short screen recording of the app in action:

<video src="public/20251020-1226-52.7592098.mp4" controls width="720"></video>


## Architecture
- Backend: FastAPI (`backend/app.py`)
  - Embedding: `sentence-transformers/all-mpnet-base-v2`
  - Vector DB: Chroma persisted at `./db`
  - Endpoints: `/upload`, `/list`, `/delete/{doc_id}`, `/chat`
- Frontend: React + Vite (`frontend/`)
  - UI: Prompt Kit-style components in `src/components/ui/...`
  - API helpers in `src/lib/api.ts`
  - Configurable backend URL via `VITE_BACKEND_URL`


## Prerequisites
- Python 3.11+
- Node 20+
- OpenRouter API key (`OPENROUTER_API_KEY`)


## Backend - Local Run
```powershell
cd backend
python -m venv .venv
./.venv/Scripts/Activate.ps1  # on Windows
pip install -r requirements.txt || pip install fastapi uvicorn python-multipart langchain-community pypdf chromadb sentence-transformers httpx python-dotenv

# Run FastAPI
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
Environment variables:
- `OPENROUTER_API_KEY`: Your OpenRouter key

CORS is permissive for dev; restrict in production.


## Frontend - Local Run
```powershell
cd frontend
npm install
# Create .env with backend URL (default is http://127.0.0.1:8000)
# echo VITE_BACKEND_URL=http://127.0.0.1:8000 > .env
npm run dev
```
Open the printed URL (e.g., http://localhost:5173).


## API Endpoints
- POST `/upload` (multipart/form-data)
  - field: `file`: PDF
  - response: `{ status: "ok", doc_id, filename, pages }`
- GET `/list`
  - response: `{ status: "ok", docs: [{ doc_id, filename, pages }] }`
- DELETE `/delete/{doc_id}`
  - response: `{ status: "ok", deleted: doc_id }`
- POST `/chat`
  - request json: `{ messages: [{ role: "user"|"assistant", content: string }], top_k?: number, summary?: string }`
  - response: `{ answer: string, sources: [{ doc: string, page: number, snippet: string }] }`


## Frontend Configuration
- Path aliases: `@/* -> src/*` handled via Vite config and tsconfig
- Backend URL: set `VITE_BACKEND_URL` in `frontend/.env`
- Prompt UI lives in `frontend/src/components/ui`:
  - `chat.tsx`, `chat-container.tsx`, `message.tsx`, `prompt-input.tsx`, `markdown.tsx`, `code-block.tsx`, `button.tsx`, `textarea.tsx`, `tooltip.tsx`, `avatar.tsx`


## Deployment
Frontend (Vercel/Netlify):
- Project directory: `frontend`
- Build: `npm run build`
- Output: `dist`
- Env var: `VITE_BACKEND_URL=https://your-backend.example.com`

Backend (Render/Railway/Fly/Docker on VPS):
- Start: `uvicorn app:app --host 0.0.0.0 --port 8000`
- Env: `OPENROUTER_API_KEY`
- Persist Chroma DB: mount `./db` as a volume (e.g., `/app/db`)
- Restrict CORS `allow_origins` to your frontend origin

Example Dockerfiles are easy to add if you choose Dockerize both services.


## Troubleshooting
- TS cannot find `@/lib/utils`: ensure `frontend/src/lib/utils.ts` exists and Vite tsconfig paths are active. We use `vite-tsconfig-paths` and alias `@` to `./src`.
- 404 from backend: confirm `VITE_BACKEND_URL` and backend is reachable.
- Model errors: check `OPENROUTER_API_KEY`