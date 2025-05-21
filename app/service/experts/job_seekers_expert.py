from typing import Dict, List, Any
import logging
import aiohttp
from app.models.expert_type import ExpertType
from app.service.experts.base_expert import BaseExpert
from app.service.openai_client import get_client
from app.service.experts.common_form.example_cards import EMPLOYMENT_CARD_TEMPLATE
from app.utils import get_embedding
from app.data_service.data_manager import aggregate_disabled_jobseekers

logger = logging.getLogger(__name__)

class JobSeekersExpert(BaseExpert):
    """
    구직자 현황 전문가 AI 클래스 (기업회원용)
    기업회원에게 장애인 구직자 현황, 통계, 샘플 구직자 정보 등을 제공합니다.
    """
    def __init__(self):
        super().__init__(ExpertType.JOB_SEEKERS)
        self.client = get_client()
        self.model = "gpt-4.1-mini"
        self.api_base_url = "http://localhost:8082/api/public"  # 백엔드 API 기본 URL

    async def _fetch_disability_stats(self, disability_type: str) -> Dict:
        """장애유형별 통계 데이터 조회"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base_url}/disabled/jobseekers/stats/{disability_type}"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def _fetch_jobseekers(self, page: int = 1, size: int = 20, search: str = None, disability_types: List[str] = None) -> Dict:
        """구직자 데이터 조회"""
        async with aiohttp.ClientSession() as session:
            params = {
                "page": page,
                "size": size
            }
            if search:
                params["search"] = search
            if disability_types:
                params["disabilityTypes"] = ",".join(disability_types)
            
            url = f"{self.api_base_url}/disabled/jobseekers"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None

    def _get_system_prompt(self) -> str:
        return """
        너는 기업회원 전용 장애인 구직자 현황 전문가 AI입니다.\n기업이 장애인 구직자 현황, 통계, 샘플 구직자 정보 등을 쉽게 파악할 수 있도록 안내합니다.\n\n모든 정보 카드는 반드시 아래와 같은 JSON 형식으로 만들어 주세요.\n{\n  "id": "string",\n  "title": "string",\n  "subtitle": "string",\n  "summary": "string",\n  "type": "string",\n  "details": "string",\n  "source": {\n    "url": "string",\n    "name": "string",\n    "phone": "string"\n  },\n  "buttons": [\n    {"type": "link", "label": "string", "value": "string"},\n    {"type": "tel", "label": "string", "value": "string"}\n  ]\n}\n\n제공할 정보 범위:\n- 장애인 구직자 현황 및 통계\n- 구직자 샘플 정보(직종, 지역, 장애유형, 희망임금 등)\n- 구직자 데이터 활용 방법\n- 구직자 채용 시 유의사항\n\n응답 스타일:\n1. 기업 실무자가 빠르게 현황을 파악할 수 있도록 간결하고 명확하게 안내하세요.\n2. 통계, 수치, 표 등 시각적 정보를 활용하세요.\n3. 샘플 구직자 정보는 카드 형태로 제공하세요.\n4. 응답 시작에 짧은 안내 멘트를 추가하세요. (예: "장애인 구직자 현황 정보를 안내해 드리겠습니다.")\n        """

    async def process_query(self, query: str, keywords: List[str] = None, conversation_history=None) -> Dict[str, Any]:
        try:
            # 통계 정보 요청인 경우
            if "통계" in query or "현황" in query:
                # 장애유형 추출 (예: "시각장애인 통계 알려줘")
                disability_type = None
                for type_keyword in ["시각장애", "청각장애", "지체장애", "발달장애", "정신장애"]:
                    if type_keyword in query:
                        disability_type = type_keyword
                        break

                if disability_type:
                    stats = await self._fetch_disability_stats(disability_type)
                    if stats:
                        # 통계 정보를 카드 형태로 변환
                        cards = [{
                            "id": "stats",
                            "title": f"{disability_type} 구직자 통계",
                            "summary": f"총 {stats['totalCount']}명 중 {stats['disabilityTypeCount']}명 ({stats['percentage']}%)",
                            "details": f"""
                            • 중증/경증 분포: {', '.join([f'{k}: {v}명' for k, v in stats['severityDistribution'].items()])}
                            • 지역별 분포: {', '.join([f'{k}: {v}명' for k, v in stats['regionDistribution'].items()])}
                            • 연령대별 분포: {', '.join([f'{k}: {v}명' for k, v in stats['ageDistribution'].items()])}
                            • 희망직종 분포: {', '.join([f'{k}: {v}명' for k, v in stats['jobTypeDistribution'].items()])}
                            • 희망임금 분포: {', '.join([f'{k}: {v}명' for k, v in stats['salaryDistribution'].items()])}
                            """
                        }]
                        
                        # 통계 데이터를 기반으로 한 상세 설명 생성
                        response_text = f"{disability_type} 구직자 현황 정보를 안내해 드리겠습니다.\n\n"
                        response_text += f"현재 총 {stats['totalCount']}명의 구직자 중 {disability_type} 구직자는 {stats['disabilityTypeCount']}명({stats['percentage']}%)입니다.\n\n"
                        
                        # 중증/경증 분포 설명
                        severity_dist = stats['severityDistribution']
                        response_text += f"중증/경증 분포를 보면, "
                        response_text += ", ".join([f"{k} {v}명" for k, v in severity_dist.items()])
                        response_text += "입니다.\n\n"
                        
                        # 연령대별 분포 설명 (상위 3개)
                        age_dist = stats['ageDistribution']
                        top_ages = sorted(age_dist.items(), key=lambda x: x[1], reverse=True)[:3]
                        response_text += f"연령대별로는 "
                        response_text += ", ".join([f"{k} {v}명" for k, v in top_ages])
                        response_text += " 순으로 많습니다.\n\n"
                        
                        # 희망직종 분포 설명 (상위 3개)
                        job_dist = stats['jobTypeDistribution']
                        top_jobs = sorted(job_dist.items(), key=lambda x: x[1], reverse=True)[:3]
                        response_text += f"희망직종으로는 "
                        response_text += ", ".join([f"{k} {v}명" for k, v in top_jobs])
                        response_text += " 순으로 많습니다.\n\n"
                        
                        # 희망임금 분포 설명 (상위 3개)
                        salary_dist = stats['salaryDistribution']
                        top_salaries = sorted(salary_dist.items(), key=lambda x: x[1], reverse=True)[:3]
                        response_text += f"희망임금은 "
                        response_text += ", ".join([f"{k} {v}명" for k, v in top_salaries])
                        response_text += " 순으로 많습니다."
                        
                        return {
                            "text": response_text,
                            "cards": cards
                        }

            # 구직자 목록 요청인 경우
            jobseekers_data = await self._fetch_jobseekers(page=1, size=5)
            if jobseekers_data and jobseekers_data.get("content"):
                cards = []
                for jobseeker in jobseekers_data["content"]:
                    card = {
                        "id": jobseeker.get("id", ""),
                        "title": f"{jobseeker.get('희망직종', '')} ({jobseeker.get('장애유형', '')})",
                        "summary": f"{jobseeker.get('희망지역', '')} / {jobseeker.get('중증여부', '')}",
                        "details": f"연령: {jobseeker.get('연령', '')}세, 희망임금: {jobseeker.get('희망임금', '')}, 등록일: {jobseeker.get('구직등록일', '')}"
                    }
                    cards.append(card)

                return {
                    "text": "장애인 구직자 현황 정보를 안내해 드리겠습니다.",
                    "cards": cards
                }

            # 기본 응답
            return {
                "text": "죄송합니다. 구직자 현황 정보를 찾지 못했습니다.",
                "cards": [EMPLOYMENT_CARD_TEMPLATE]
            }

        except Exception as e:
            logger.error(f"구직자 현황 정보 검색 중 오류 발생: {str(e)}")
            return {
                "text": "죄송합니다. 구직자 현황 정보를 검색하는 중에 문제가 발생했습니다.",
                "cards": [EMPLOYMENT_CARD_TEMPLATE]
            }

    def _get_description(self) -> str:
        return "기업을 위한 장애인 구직자 현황, 통계, 샘플 구직자 정보를 제공합니다."

    def _get_icon(self) -> str:
        return "📊"
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        return []

async def job_seekers_response(query: str, keywords: List[str] = None, conversation_history=None) -> tuple:
    expert = JobSeekersExpert()
    response = await expert.process_query(query, keywords, conversation_history)
    return response.get("text", ""), response.get("cards", []) 