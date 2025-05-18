from openai import AsyncOpenAI
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
# db = client["kead_db"]
db = client["public_data_db"]
# collection = db["policy_chunks"]
collection = db["disabled_jobseekers"]

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str):
    response = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

print("💡 아직 임베딩되지 않은 문서 수:", collection.count_documents({"embedding": None}))

async def fill_embeddings_batch():
    batch_size = 10  # 한 번에 처리할 문서 수
    total_processed = 0
    
    while True:
        # 아직 임베딩되지 않은 문서를 batch_size만큼 가져옴
        chunks = list(collection.find({"embedding": {"$exists": False}}).limit(batch_size))
        if not chunks:
            break  # 더 이상 처리할 문서가 없으면 종료
            
        tasks = []
        for chunk in chunks:
            text = f"{chunk.get('연번', '')} {chunk.get('연령', '')} {chunk.get('장애유형', '')} {chunk.get('중증여부', '')} {chunk.get('희망임금', '')} {chunk.get('희망지역', '')} {chunk.get('희망직종', '')}"
            if text.strip():
                tasks.append(process_document(chunk, text))
        
        if tasks:
            await asyncio.gather(*tasks)
            total_processed += len(tasks)
            print(f"✅ 총 {total_processed}개 문서 처리 완료")
            await asyncio.sleep(1)  # 배치 사이에 지연 추가
            
async def process_document(chunk, text):
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        doc_id = chunk["_id"]
        collection.update_one({"_id": doc_id}, {"$set": {"embedding": embedding}})
        print(f"✅ 임베딩 완료: {chunk.get('연번', '')}")
    except Exception as e:
        print(f"❌ 에러: {type(e).__name__} - {e}")


if __name__ == "__main__":
    asyncio.run(fill_embeddings_batch())