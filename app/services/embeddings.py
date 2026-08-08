from sentence_transformers import SentenceTransformer
import asyncio

_model = SentenceTransformer("all-MiniLM-L6-v2")

async def get_embedding(text:str) -> list[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: _model.encode(text).tolist())



