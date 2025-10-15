from langchain_community.vectorstores import Chroma
from services.embeddings import get_embeddings


def get_vectorstore(persist_directory: str = "./db") -> Chroma:
    hf = get_embeddings()
    return Chroma(persist_directory=persist_directory, embedding_function=hf)


