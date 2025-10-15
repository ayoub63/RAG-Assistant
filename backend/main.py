import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.chat import router as chat_router
from routers.docs import router as docs_router


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(docs_router)
    app.include_router(chat_router)

    return app


app = create_app()


