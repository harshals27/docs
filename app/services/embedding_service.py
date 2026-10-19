from sentence_transformers import SentenceTransformer

from app.config import MODEL_PATH

model = SentenceTransformer(MODEL_PATH)


def get_embedding(text: str):
    return model.encode(text).tolist()


def get_embeddings(texts: list):
    return model.encode(texts).tolist()