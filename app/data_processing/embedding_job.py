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
collection = db["disabled_job_offers"]

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str):
    response = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

print("💡 아직 임베딩되지 않은 문서 수:", collection.count_documents({"embedding": None}))

async def fill_embeddings():
    chunks = collection.find({"embedding": None})
    for chunk in chunks:
        print("🔍 처리 중:", chunk.get("busplaName", "제목없음"))
        text = f"{chunk.get('busplaName', '')} {chunk.get('compAddr', '')} {chunk.get('jobNm', '')}"
        if not text.strip():
            continue
        try:
            response = await openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            collection.update_one({"_id": chunk["_id"]}, {"$set": {"embedding": embedding}})
            print(f"✅ 임베딩 완료: {chunk.get('busplaName', '')[:30]}...")
        except Exception as e:
            import traceback
            print(f"❌ 에러: {e}")

if __name__ == "__main__":
    asyncio.run(fill_embeddings())