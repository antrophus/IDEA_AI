import os
from dotenv import load_dotenv
import asyncio
from openai import AsyncOpenAI
from app.data_service.data_manager import (
    get_policy_chunks_without_embedding,
    update_policy_chunk_embedding,
    count_policy_chunks_without_embedding
)
from app.utils import get_embedding

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("💡 아직 임베딩되지 않은 정책 문서 수:", count_policy_chunks_without_embedding())

async def fill_embeddings():
    chunks = get_policy_chunks_without_embedding()
    for chunk in chunks:
        print("🔍 처리 중:", chunk["metadata"]["title"])
        text = chunk.get("page_content", "")
        if not text.strip():
            continue
        try:
            embedding = await get_embedding(openai_client, text)
            update_policy_chunk_embedding(chunk["_id"], embedding)
            print(f"✅ 임베딩 완료: {chunk['metadata']['title'][:30]}...")
        except Exception as e:
            import traceback
            print(f"❌ 에러: {e}")

if __name__ == "__main__":
    asyncio.run(fill_embeddings())