from typing import Dict, List, Any
import logging
from app.models.expert_type import ExpertType
from app.service.experts.base_expert import BaseExpert
from app.service.openai_client import get_client
from app.service.experts.common_form.example_cards import EMPLOYMENT_CARD_TEMPLATE
from app.utils import get_embedding
from app.service.utils.data_processor import DataProcessor
from app.data_service.data_manager import (
    aggregate_disabled_job_offers,
    aggregate_welfare_service_list
)

logger = logging.getLogger(__name__)

class EmploymentExpert(BaseExpert):
    """
    취업 전문가 AI 클래스
    장애인 취업, 고용 지원, 직업 교육 등에 대한 정보를 제공합니다.
    """
    
    def __init__(self):
        super().__init__(ExpertType.EMPLOYMENT)
        self.client = get_client()
        self.model = "gpt-4.1-mini"
    
    def _get_system_prompt(self) -> str:
        return """
        너는 장애인 취업 전문가 AI입니다. 
        장애인 취업, 고용 지원, 직업 교육 등에 대한 정확하고 유용한 정보를 제공해야 합니다.
        
        모든 정보 카드는 반드시 아래와 같은 JSON 형식으로 만들어 주세요.
        {
          "id": "string",
          "title": "string",
          "subtitle": "string",
          "summary": "string",
          "type": "string",
          "details": "string",
          "source": {
            "url": "string",
            "name": "string",
            "phone": "string"
          },
          "buttons": [
            {"type": "link", "label": "string", "value": "string"},
            {"type": "tel", "label": "string", "value": "string"}
          ]
        }
        
        제공할 정보 범위:
        - 장애인 의무고용제도
        - 장애인 구인구직 정보
        - 장애인 표준사업장 정보
        - 장애인 직업훈련 프로그램
        - 취업 후 근로지원 서비스
        - 장애인 취업 관련 보조금 및 지원금
        - 장애인 창업 지원 정보
        
        응답 스타일:
        1. 항상 따뜻하고 격려하는 톤으로 응답하세요. 구직자의 어려움에 공감하고 희망을 주는 표현을 포함하세요.
        2. 응답 시작 부분에 짧은 공감/격려 멘트를 추가하세요. (예: "취업 준비가 쉽지 않으시죠. 함께 좋은 정보를 찾아보겠습니다.")
        3. 최신 고용 동향과 정보를 기반으로 실용적인 조언을 제공하세요.
        4. 취업 지원 제도와 프로그램에 대해 구체적으로 설명하되, 지원 자격, 신청 방법, 혜택 등을 명확히 안내하세요.
        5. 가능한 많은 취업 기회를 제공하고, 다양한 직업 영역을 탐색하도록 격려하세요.
        6. 취업 후 적응과 지속적인 근무를 위한 정보도 함께 제공하세요.
        
        정보 카드:
        1. 모든 응답에는 반드시 관련 취업 정보 카드를 포함하세요.
        2. 카드에는 구인 정보, 직업훈련 프로그램, 취업지원 서비스 등 핵심 정보를 담으세요.
        
        사용자에게 실질적인 취업 기회와 정보를 제공하면서도, 심리적 지지와 자신감을 키워주는 응답을 제공하세요.
        """
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_employment_database",
                    "description": "장애인 취업 데이터베이스에서 관련 정보를 검색합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "검색 키워드 목록"
                            },
                            "job_type": {
                                "type": "string",
                                "description": "직업 유형 또는 산업 분야"
                            },
                            "region": {
                                "type": "string",
                                "description": "지역 정보"
                            }
                        },
                        "required": ["keywords"]
                    }
                }
            }
        ]
    
    async def search_job_offers_by_semantic(self, user_query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        disabled_job_offers에서 구인 정보를 임베딩 기반으로 검색
        """
        try:
            keywords = DataProcessor.extract_keywords(user_query, max_keywords=5)
            keyword_query = " ".join(keywords)
            user_embedding = await get_embedding(keyword_query)
            logger.info(f"job_offers 벡터 검색 임베딩: {user_embedding[:5]}...")
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index_disabled_offers",
                        "path": "embedding",
                        "queryVector": user_embedding,
                        "numCandidates": 500,
                        "limit": limit
                    }
                }
            ]
            docs = await aggregate_disabled_job_offers(pipeline, limit=limit)
            results = []
            for doc in docs:
                logger.info(f"job_offers 검색 결과: {doc}")
                card = {
                    "id": doc.get("id", ""),
                    "type": "job_offer",
                    "title": doc.get("jobNm", ""),
                    "summary": f"{doc.get('busplaName', '')} | {doc.get('compAddr', '')}",
                    "empType": doc.get("empType", ""),
                    "compAddr": doc.get("compAddr", ""),
                    "termDate": doc.get("termDate", ""),
                    "cntctNo": doc.get("cntctNo", ""),
                    "enterType": doc.get("enterType", ""),
                    "offerregDt": doc.get("offerregDt", ""),
                    "regDt": doc.get("regDt", ""),
                    "regagnName": doc.get("regagnName", ""),
                    "reqCareer": doc.get("reqCareer", ""),
                    "reqEduc": doc.get("reqEduc", ""),
                    "salary": doc.get("salary", ""),
                    "salaryType": doc.get("salaryType", ""),
                    "envBothHands": doc.get("envBothHands", ""),
                    "envEyesight": doc.get("envEyesight", ""),
                    "envHandwork": doc.get("envHandwork", ""),
                    "envLiftPower": doc.get("envLiftPower", ""),
                    "envLstnTalk": doc.get("envLstnTalk", ""),
                    "envStndWalk": doc.get("envStndWalk", ""),
                    "source": {
                        "url": doc.get("url", ""),
                        "name": doc.get("company", ""),
                        "phone": doc.get("contact", "")
                    },
                    "buttons": [
                        {
                            "type": "link",
                            "label": "공고 보기",
                            "value": doc.get("url", "")
                        }
                    ]
                }
                if doc.get("contact"):
                    card["buttons"].append({
                        "type": "tel",
                        "label": "문의하기",
                        "value": doc.get("contact")
                    })
                results.append(card)
            logger.info(f"job_offers 검색 결과 개수: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"임베딩 기반 구인 정보 검색 중 오류 발생: {str(e)}")
            return []

    async def search_employment_by_semantic(self, user_query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        welfare_service_list에서 취업 관련 정책/지원 정보를 임베딩 기반으로 검색
        """
        try:
            user_embedding = await get_embedding(self.client,user_query)
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index_welfare_list",
                        "path": "embedding",
                        "queryVector": user_embedding,
                        "numCandidates": 100,
                        "limit": limit
                    }
                }
            ]
            docs = await aggregate_welfare_service_list(pipeline, limit=limit)
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
            return results
        except Exception as e:
            logger.error(f"임베딩 기반 취업 정보 검색 중 오류 발생: {str(e)}")
            return []

    async def process_query(
        self, query: str, keywords: List[str] = None, conversation_history=None,
        user_role: str = "user", job_offer_priority: bool = False
    ) -> Dict[str, Any]:
        logger.info(f"[취업전문가] 쿼리: {query} | user_role: {user_role} | job_offer_priority: {job_offer_priority}")
        job_cards, policy_cards = [], []
        if job_offer_priority and user_role == "user":
            job_cards = await self.search_job_offers_by_semantic(query, limit=3)
            policy_cards = await self.search_employment_by_semantic(query, limit=3)
            all_cards = job_cards + policy_cards
        else:
            policy_cards = await self.search_employment_by_semantic(query, limit=3)
            if user_role == "user":
                job_cards = await self.search_job_offers_by_semantic(query, limit=3)
            all_cards = policy_cards + job_cards
        logger.info(f"[취업전문가] 정책카드 {len(policy_cards)}개, 구인카드 {len(job_cards)}개 반환")
        if not all_cards:
            return {
                "text": "죄송합니다. 관련 취업 정책이나 구인 정보를 찾지 못했습니다.",
                "cards": [EMPLOYMENT_CARD_TEMPLATE]
            }
        response_text = "안녕하세요! 문의하신 취업 정책 및 구인 정보를 알려드리겠습니다.\n\n"
        for card in all_cards:
            response_text += f"• {card['title']}\n{card['summary']}\n"
            if "source" in card and "phone" in card["source"]:
                response_text += f"문의: {card['source']['name']} ({card['source']['phone']})\n"
            response_text += "\n"
        return {
            "text": response_text.strip(),
            "cards": all_cards
        }

    def _prepare_messages(self, query: str, conversation_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        if conversation_history:
            recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            for msg in recent_history:
                if msg.get("role") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})
        return messages
    
    def _format_card(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": data.get("id", EMPLOYMENT_CARD_TEMPLATE["id"]),
            "title": data.get("title", EMPLOYMENT_CARD_TEMPLATE["title"]),
            "subtitle": data.get("subtitle", EMPLOYMENT_CARD_TEMPLATE["subtitle"]),
            "summary": data.get("summary", EMPLOYMENT_CARD_TEMPLATE["summary"]),
            "type": data.get("type", EMPLOYMENT_CARD_TEMPLATE["type"]),
            "details": data.get("details", EMPLOYMENT_CARD_TEMPLATE["details"]),
            "source": data.get("source", EMPLOYMENT_CARD_TEMPLATE["source"]),
            "buttons": data.get("buttons", EMPLOYMENT_CARD_TEMPLATE["buttons"])
        }
    
    def _get_description(self) -> str:
        return "장애인 취업, 고용 지원, 직업 교육 등에 대한 정보를 제공합니다."
    
    def _get_icon(self) -> str:
        return "💼"

async def employment_response(
    query: str, keywords: List[str] = None, conversation_history=None,
    user_role: str = "user", job_offer_priority: bool = False
) -> tuple:
    expert = EmploymentExpert()
    response = await expert.process_query(
        query, keywords, conversation_history,
        user_role=user_role, job_offer_priority=job_offer_priority
    )
    return response.get("text", ""), response.get("cards", []) 