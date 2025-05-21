from openai import AsyncOpenAI
from app.data_service.data_manager import (
    get_disabled_jobseekers_without_embedding,
    update_disabled_jobseeker_embedding,
    count_disabled_jobseekers_without_embedding
)
import os
from dotenv import load_dotenv
import asyncio
from app.utils import get_embedding

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("💡 아직 임베딩되지 않은 장애인 취업 준비생 문서 수:", count_disabled_jobseekers_without_embedding())

async def fill_embeddings_batch():
    batch_size = 10  # 한 번에 처리할 문서 수
    total_processed = 0
    while True:
        chunks = list(get_disabled_jobseekers_without_embedding(batch_size))
        if not chunks:
            break
        tasks = []
        for chunk in chunks:
            text = f"{chunk.get('연번', '')} {chunk.get('연령', '')} {chunk.get('장애유형', '')} {chunk.get('중증여부', '')} {chunk.get('희망임금', '')} {chunk.get('희망지역', '')} {chunk.get('희망직종', '')}"
            if text.strip():
                tasks.append(process_document(chunk, text))
        if tasks:
            await asyncio.gather(*tasks)
            total_processed += len(tasks)
            print(f"✅ 총 {total_processed}개 문서 처리 완료")
            await asyncio.sleep(1)

async def process_document(chunk, text):
    try:
        embedding = await get_embedding(openai_client, text)
        doc_id = chunk["_id"]
        update_disabled_jobseeker_embedding(doc_id, embedding)
        print(f"✅ 임베딩 완료: {chunk.get('연번', '')}")
    except Exception as e:
        print(f"❌ 에러: {type(e).__name__} - {e}")

if __name__ == "__main__":
    asyncio.run(fill_embeddings_batch())