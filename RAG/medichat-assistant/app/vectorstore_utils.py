from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List

def create_faiss_index(texts: List[str]):
    """_summary_

    Args:
        texts (List[str]): _description_

    Returns:
        _type_: _description_
    """
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    vectorstore = FAISS.from_texts(texts, embeddings)
    return vectorstore

def retreive_similar_documents(vectorstore, query: str, k: int = 4):
    """_summary_

    Args:
        vectorstore (_type_): _description_
        query (str): _description_
        k (int, optional): _description_. Defaults to 4.

    Returns:
        _type_: _description_
    """
    docs = vectorstore.similarity_search(query, k=k)
    return docs