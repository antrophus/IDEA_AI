from pymongo import MongoClient
from dotenv import load_dotenv
import os, uuid, datetime
import json

# ✅ .env에서 Mongo URI 불러오기
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["kead_db"]
collection = db["policy"]  # 문서 단위로 저장할 컬렉션

# ✅ JSON 파일에서 데이터 불러오기
def load_policy_file(file_path="policies.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_to_mongo():
    data = load_policy_file()
    for item in data:
        doc = {
            "_id": str(uuid.uuid4()),
            "beneficiary_type": item.get("beneficiary_type", ""),
            "policy_name": item.get("policy_name", ""),
            "summary": item.get("summary", ""),
            "details": item.get("details", {}),
            "source_url": item.get("source_url", []),
            "last_updated": item.get("last_updated", ""),
            "created_at": datetime.datetime.utcnow()
        }
        collection.insert_one(doc)
    print(f"✅ {len(data)}개 문서가 MongoDB에 저장되었습니다.")

if __name__ == "__main__":
    save_to_mongo()
