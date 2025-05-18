from pymongo import MongoClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os, uuid, json
from dotenv import load_dotenv

# .env에서 MONGO_URI 불러오기
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["kead_db"]
policy_collection = db["policy"]
chunk_collection = db["policy_chunks"]

# 텍스트 쪼개기 설정
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
)

def make_chunks_and_save():
    docs = list(policy_collection.find())
    chunk_docs = []

    for doc in docs:
        # ✅ summary와 details를 합쳐서 하나의 텍스트로 구성
        summary = doc.get("summary", "")
        details = json.dumps(doc.get("details", {}), ensure_ascii=False, indent=2)
        full_text = summary + "\n" + details

        chunks = splitter.split_text(full_text)

        for i, chunk in enumerate(chunks):
            chunk_docs.append({
                "_id": str(uuid.uuid4()),
                "doc_id": str(doc.get("_id")),
                "chunk_index": i,
                "page_content": chunk,
                "metadata": {
                    "policy_name": doc.get("policy_name", ""),
                    "beneficiary_type": doc.get("beneficiary_type", "")
                },
                "embedding": None,
                "gpt_analysis": None
            })

    if chunk_docs:
        chunk_collection.insert_many(chunk_docs)
        print(f"✅ {len(chunk_docs)}개의 chunk가 저장되었습니다.")
    else:
        print("❗ chunk가 없습니다.")

if __name__ == "__main__":
    make_chunks_and_save()
