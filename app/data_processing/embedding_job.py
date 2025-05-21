from openai import AsyncOpenAI
from app.data_service.data_manager import (
    get_disabled_job_offers_without_embedding,
    update_disabled_job_offer_embedding,
    count_disabled_job_offers_without_embedding
)
import os
from dotenv import load_dotenv
import asyncio
from app.utils import get_embedding

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("💡 아직 임베딩되지 않은 장애인 취업 제안 문서 수:", count_disabled_job_offers_without_embedding())

async def fill_embeddings():
    chunks = get_disabled_job_offers_without_embedding()
    for chunk in chunks:
        print("🔍 처리 중:", chunk.get("busplaName", "제목없음"))
        text = f"{chunk.get('busplaName', '')} {chunk.get('compAddr', '')} {chunk.get('jobNm', '')}"
        if not text.strip():
            continue
        try:
            embedding = await get_embedding(openai_client, text)
            update_disabled_job_offer_embedding(chunk["_id"], embedding)
            print(f"✅ 임베딩 완료: {chunk.get('busplaName', '')[:30]}...")
        except Exception as e:
            import traceback
            print(f"❌ 에러: {e}")

if __name__ == "__main__":
    asyncio.run(fill_embeddings())