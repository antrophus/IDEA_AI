# mongodb.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import numpy as np

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))

def get_db(db_name: str):
    return client[db_name]

def get_collection(db_name: str, col_name: str):
    return client[db_name][col_name]

# ✅ 1. Atlas Search 기반 키워드 검색
def search_chunks_by_keyword(keyword: str, limit: int = 5):
    collection = get_collection("kead_db", "policy_chunks")
    pipeline = [
        {
            "$search": {
                "index": "default",
                "text": {
                    "query": keyword,
                    "path": ["page_content", "metadata.title"]
                }
            }
        },
        { "$limit": limit }
    ]
    return list(collection.aggregate(pipeline))


# ✅ 2. 벡터 임베딩 기반 유사도 검색 (GPT 응답용)
def search_similar_policies(query_vector, limit=3):
    collection = get_collection("kead_db", "policy_chunks")
    documents = list(collection.find({"embedding": {"$ne": None}}))
    scores = []

    for doc in documents:
        doc_vector = doc["embedding"]
        score = cosine_similarity(query_vector, doc_vector)
        scores.append((doc, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scores[:limit]]



# ✅ 3. 코사인 유사도 계산 함수
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

# ✅ 4. public_data_db 복지 서비스 목록 검색

def search_welfare_services(keyword: str = "", limit: int = 5):
    col = get_collection("public_data_db", "welfare_service_list")
    if keyword:
        query = {
            "$or": [
                {"servNm": {"$regex": keyword, "$options": "i"}},
                {"jurMnofNm": {"$regex": keyword, "$options": "i"}},
                {"servDgst": {"$regex": keyword, "$options": "i"}}
            ]
        }
    else:
        query = {}
    return list(col.find(query).limit(limit))

# ✅ 5. public_data_db 복지 서비스 상세 조회

def get_welfare_service_detail(servId: str):
    col = get_collection("public_data_db", "welfare_service_detail")
    return col.find_one({"servId": servId})

# ✅ 6. public_data_db 장애인 구직 현황 검색

def search_disabled_job_offers(keyword: str = "", limit: int = 5):
    col = get_collection("public_data_db", "disabled_job_offers")
    if keyword:
        query = {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"company": {"$regex": keyword, "$options": "i"}},
                {"location": {"$regex": keyword, "$options": "i"}}
            ]
        }
    else:
        query = {}
    return list(col.find(query).limit(limit))
