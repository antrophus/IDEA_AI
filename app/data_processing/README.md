# data_processing

이 디렉토리는 임베딩, 크롤링, 데이터 적재 등 챗봇 API 서버의 실시간 응답과 직접 관련 없는 배치/데이터 처리 코드를 분리하여 관리합니다.

## 주요 목적
- 임베딩 생성 및 저장
- 크롤링 및 데이터 수집
- 대량 데이터 적재 및 전처리
- 기타 배치성 데이터 처리

## 하위 구조 예시
- embedding/
- crawling/
- utils/

각 기능별로 하위 디렉토리 및 파일을 추가해 관리하세요.

## 현재 포함된 파일
- embedding.py
- embedding_job.py
- embedding_jobseekers.py
- embedding_welfare.py
- crawl_kead.py
- upload_to_mongo.py
- chunk_policy.py
- policies.json 