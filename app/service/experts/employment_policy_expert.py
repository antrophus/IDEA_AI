from typing import Dict, List, Any
import logging
from app.models.expert_type import ExpertType
from app.service.experts.base_expert import BaseExpert
from app.service.openai_client import get_client
from app.service.experts.common_form.example_cards import POLICY_CARD_TEMPLATE
from app.utils import get_embedding
from app.data_service.data_manager import aggregate_welfare_service_list

logger = logging.getLogger(__name__)

class EmploymentPolicyExpert(BaseExpert):
    """
    고용 정책 전문가 AI 클래스 (기업회원용)
    장애인 고용 정책, 제도, 지원금 등 기업 대상 정보를 제공합니다.
    """
    def __init__(self):
        super().__init__(ExpertType.EMPLOYMENT_POLICY)
        self.client = get_client()
        self.model = "gpt-4.1-mini"

    def _get_system_prompt(self) -> str:
        return """
        너는 기업회원 전용 장애인 고용 정책 전문가 AI입니다.\n기업이 장애인 고용 시 받을 수 있는 지원 정책, 제도, 보조금, 컨설팅 등에 대해 정확하고 실용적인 정보를 제공합니다.\n\n모든 정보 카드는 반드시 아래와 같은 JSON 형식으로 만들어 주세요.\n{\n  "id": "string",\n  "title": "string",\n  "subtitle": "string",\n  "summary": "string",\n  "type": "string",\n  "details": "string",\n  "source": {\n    "url": "string",\n    "name": "string",\n    "phone": "string"\n  },\n  "buttons": [\n    {"type": "link", "label": "string", "value": "string"},\n    {"type": "tel", "label": "string", "value": "string"}\n  ]\n}\n\n제공할 정보 범위:\n- 장애인 고용 의무제도\n- 기업 대상 장애인 고용장려금, 지원금\n- 장애인 고용 컨설팅, 채용 절차\n- 장애인 표준사업장 설립 지원\n- 장애인 고용 관련 법률 및 제도\n- 장애인 고용관리 우수기업 사례\n\n응답 스타일:\n1. 기업 실무자가 이해하기 쉽도록 실용적이고 명확하게 안내하세요.\n2. 지원금, 신청 방법, 자격 요건 등 실질적 정보를 구체적으로 안내하세요.\n3. 관련 기관, 문의처, 참고 링크를 반드시 포함하세요.\n4. 응답 시작에 짧은 안내 멘트를 추가하세요. (예: "기업의 장애인 고용을 위한 정책 정보를 안내해 드리겠습니다.")\n\n정보 카드:\n1. 모든 응답에는 반드시 관련 고용 정책 정보 카드를 포함하세요.\n2. 카드에는 정책명, 요약, 신청 방법, 문의처 등 핵심 정보를 담으세요.\n        """

    async def process_query(self, query: str, keywords: List[str] = None, conversation_history=None) -> Dict[str, Any]:
        # 실제 구현에서는 정책 DB/외부 API 연동 또는 OpenAI 활용
        # 여기서는 예시로 임베딩 기반 검색 구조만 스케치
        try:
            user_embedding = await get_embedding(self.client,query)
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index_welfare_list",
                        "path": "embedding",
                        "queryVector": user_embedding,
                        "numCandidates": 100,
                        "limit": 3
                    }
                },
                {
                    "$match": {
                        "$or": [
                            {"servNm": {"$regex": "고용|장려금|지원금|기업|장애인 고용", "$options": "i"}},
                            {"intrsThemaArray": {"$regex": "고용|장려금|지원금|기업|장애인 고용", "$options": "i"}}
                        ]
                    }
                }
            ]
            docs = await aggregate_welfare_service_list(pipeline, limit=3)
            results = []
            for doc in docs:
                card = {
                    "id": doc.get("servId", ""),
                    "title": doc.get("servNm", ""),
                    "subtitle": doc.get("jurMnofNm", ""),
                    "summary": doc.get("servDgst", ""),
                    "type": "policy",
                    "details": doc.get("servDgst", ""),
                    "source": {
                        "url": doc.get("servDtlLink", ""),
                        "name": doc.get("jurOrgNm", ""),
                        "phone": doc.get("rprsCtadr", "")
                    },
                    "buttons": [
                        {
                            "type": "link",
                            "label": "자세히 보기",
                            "value": doc.get("servDtlLink", "")
                        }
                    ]
                }
                if doc.get("rprsCtadr"):
                    card["buttons"].append({
                        "type": "tel",
                        "label": "문의하기",
                        "value": doc.get("rprsCtadr")
                    })
                results.append(card)
            if not results:
                return {
                    "text": "죄송합니다. 관련 고용 정책 정보를 찾지 못했습니다.",
                    "cards": [POLICY_CARD_TEMPLATE]
                }
            response_text = "기업의 장애인 고용을 위한 정책 정보를 안내해 드리겠습니다.\n\n"
            for card in results:
                response_text += f"• {card['title']}\n{card['summary']}\n"
                if "source" in card and "phone" in card["source"]:
                    response_text += f"문의: {card['source']['name']} ({card['source']['phone']})\n"
                response_text += "\n"
            return {
                "text": response_text.strip(),
                "cards": results
            }
        except Exception as e:
            logger.error(f"고용 정책 정보 검색 중 오류 발생: {str(e)}")
            return {
                "text": "죄송합니다. 고용 정책 정보를 검색하는 중에 문제가 발생했습니다.",
                "cards": [POLICY_CARD_TEMPLATE]
            }

    def _get_description(self) -> str:
        return "기업을 위한 장애인 고용 정책, 지원금, 제도 정보를 제공합니다."

    def _get_icon(self) -> str:
        return "🏢"

    def _get_tools(self) -> List[Dict[str, Any]]:
        return []

async def employment_policy_response(query: str, keywords: List[str] = None, conversation_history=None) -> tuple:
    expert = EmploymentPolicyExpert()
    response = await expert.process_query(query, keywords, conversation_history)
    return response.get("text", ""), response.get("cards", []) 