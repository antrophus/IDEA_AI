# mongodb.py
from app.data_service.data_manager import (
    search_welfare_services,
    get_welfare_service_detail,
    search_disabled_job_offers,
    search_chunks_by_keyword,
    search_similar_policies
)

# ✅ 1. Atlas Search 기반 키워드 검색
def search_chunks_by_keyword_proxy(keyword: str, limit: int = 5):
    return search_chunks_by_keyword(keyword, limit)

# ✅ 2. 벡터 임베딩 기반 유사도 검색 (GPT 응답용)
def search_similar_policies_proxy(query_vector, limit=3):
    return search_similar_policies(query_vector, limit)

# ✅ 4. public_data_db 복지 서비스 목록 검색
def search_welfare_services_proxy(keyword: str = "", limit: int = 5):
    return search_welfare_services(keyword, limit)

# ✅ 5. public_data_db 복지 서비스 상세 조회
def get_welfare_service_detail_proxy(servId: str):
    return get_welfare_service_detail(servId)

# ✅ 6. public_data_db 장애인 구직 현황 검색
def search_disabled_job_offers_proxy(keyword: str = "", limit: int = 5):
    return search_disabled_job_offers(keyword, limit)
