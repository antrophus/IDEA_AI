from fastapi import FastAPI
from app.router import chatbot
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import logging
from pymongo import MongoClient
from fastapi.responses import JSONResponse
import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 환경 변수 로드
load_dotenv()

app = FastAPI(
    title="장애인 복지 AI 챗봇 API",
    description="장애인 복지 정보 및 상담을 제공하는 AI 챗봇 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한해야 함
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chatbot.router, prefix="", tags=["chatbot"])

@app.get("/")
def root():
    return {"message": "장애인 복지 AI 챗봇 API가 정상적으로 동작 중입니다."}
