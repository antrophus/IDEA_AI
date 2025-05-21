from .db_connection import MongoDBConnection
import os
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
from app.utils import cosine_similarity

mongo = MongoDBConnection()

def search_welfare_services(keyword: str = "", limit: int = 5):
    col = mongo.get_collection("public_data_db", "welfare_service_list")
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

def get_welfare_service_detail(servId: str):
    col = mongo.get_collection("public_data_db", "welfare_service_detail")
    return col.find_one({"servId": servId})

def search_disabled_job_offers(keyword: str = "", limit: int = 5):
    col = mongo.get_collection("public_data_db", "disabled_job_offers")
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

def get_policy_chunks_without_embedding():
    col = mongo.get_collection("kead_db", "policy_chunks")
    return col.find({"embedding": None})

def update_policy_chunk_embedding(chunk_id, embedding):
    col = mongo.get_collection("kead_db", "policy_chunks")
    return col.update_one({"_id": chunk_id}, {"$set": {"embedding": embedding}})

def count_policy_chunks_without_embedding():
    col = mongo.get_collection("kead_db", "policy_chunks")
    return col.count_documents({"embedding": None})

def get_disabled_job_offers_without_embedding():
    col = mongo.get_collection("public_data_db", "disabled_job_offers")
    return col.find({"embedding": None})

def update_disabled_job_offer_embedding(chunk_id, embedding):
    col = mongo.get_collection("public_data_db", "disabled_job_offers")
    return col.update_one({"_id": chunk_id}, {"$set": {"embedding": embedding}})

def count_disabled_job_offers_without_embedding():
    col = mongo.get_collection("public_data_db", "disabled_job_offers")
    return col.count_documents({"embedding": None})

def get_disabled_jobseekers_without_embedding(batch_size=0):
    col = mongo.get_collection("public_data_db", "disabled_jobseekers")
    cursor = col.find({"embedding": {"$exists": False}})
    if batch_size > 0:
        return cursor.limit(batch_size)
    return cursor

def update_disabled_jobseeker_embedding(doc_id, embedding):
    col = mongo.get_collection("public_data_db", "disabled_jobseekers")
    return col.update_one({"_id": doc_id}, {"$set": {"embedding": embedding}})

def count_disabled_jobseekers_without_embedding():
    col = mongo.get_collection("public_data_db", "disabled_jobseekers")
    return col.count_documents({"embedding": {"$exists": False}})

def get_welfare_services_without_embedding():
    col = mongo.get_collection("public_data_db", "welfare_service_list")
    return col.find({"embedding": None})

def update_welfare_service_embedding(doc_id, embedding):
    col = mongo.get_collection("public_data_db", "welfare_service_list")
    return col.update_one({"_id": doc_id}, {"$set": {"embedding": embedding}})

def count_welfare_services_without_embedding():
    col = mongo.get_collection("public_data_db", "welfare_service_list")
    return col.count_documents({"embedding": None})

def insert_policies(docs):
    col = mongo.get_collection("kead_db", "policy")
    if isinstance(docs, list):
        return col.insert_many(docs)
    else:
        return col.insert_one(docs)

def get_all_policies():
    col = mongo.get_collection("kead_db", "policy")
    return col.find()

def insert_policy_chunks(chunk_docs):
    col = mongo.get_collection("kead_db", "policy_chunks")
    return col.insert_many(chunk_docs)

async def aggregate_welfare_service_list(pipeline, limit=5):
    mongo_uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["public_data_db"]
    collection = db["welfare_service_list"]
    cursor = collection.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(doc)
        if len(results) >= limit:
            break
    return results

async def aggregate_disabled_job_offers(pipeline, limit=5):
    mongo_uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["public_data_db"]
    collection = db["disabled_job_offers"]
    cursor = collection.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(doc)
        if len(results) >= limit:
            break
    return results

async def aggregate_disabled_jobseekers(pipeline, limit=5):
    mongo_uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["public_data_db"]
    collection = db["disabled_jobseekers"]
    cursor = collection.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(doc)
        if len(results) >= limit:
            break
    return results

def search_chunks_by_keyword(keyword: str, limit: int = 5):
    col = mongo.get_collection("kead_db", "policy_chunks")
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
    return list(col.aggregate(pipeline))

def search_similar_policies(query_vector, limit=3):
    col = mongo.get_collection("kead_db", "policy_chunks")
    documents = list(col.find({"embedding": {"$ne": None}}))
    scores = []
    for doc in documents:
        doc_vector = doc["embedding"]
        score = cosine_similarity(query_vector, doc_vector)
        scores.append((doc, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scores[:limit]] 