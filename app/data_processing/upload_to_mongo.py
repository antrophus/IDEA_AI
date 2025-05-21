from app.data_service.data_manager import insert_policies
from dotenv import load_dotenv
import os, uuid, datetime
import json
from app.utils import load_json

# ✅ .env에서 Mongo URI 불러오기
load_dotenv()

# ✅ JSON 파일에서 데이터 불러오기
def load_policy_file(file_path="policies.json"):
    return load_json(file_path)

def save_to_mongo():
    data = load_policy_file()
    docs = []
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
        docs.append(doc)
    insert_policies(docs)
    print(f"✅ {len(data)}개 문서가 MongoDB에 저장되었습니다.")

if __name__ == "__main__":
    save_to_mongo()
