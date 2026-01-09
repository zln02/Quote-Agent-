"""
CrewAI 기반 견적서 생성 로직
"""
import json
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew

from src.config import settings
from src.utils.logger import logger


class QuoteGenerator:
    """견적서 생성기"""
    
    def __init__(self):
        """초기화"""
        self.vat_rate = settings.VAT_RATE
        self.min_subtotal = settings.MIN_SUBTOTAL_KRW
    
    def _create_scope_analyst(self) -> Agent:
        """범위 분석 Agent 생성"""
        return Agent(
            role="프로젝트 범위 분석가",
            goal="고객 요청사항을 구체적인 작업 범위, 산출물, 마일스톤으로 분해합니다.",
            backstory="""당신은 10년 이상의 경험을 가진 프로젝트 매니저입니다.
            고객의 요구사항을 정확히 이해하고, 구체적이고 측정 가능한 작업 항목으로 분해하는 것이 전문 분야입니다.
            항상 명확하고 실무적인 범위 정의를 제공합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _create_estimator(self) -> Agent:
        """견적 산출 Agent 생성"""
        return Agent(
            role="견적 산출 전문가",
            goal="작업 범위를 기반으로 현실적인 일정과 금액을 산출합니다.",
            backstory="""당신은 IT 프로젝트 견적 전문가입니다.
            작업 범위를 분석하여 적정한 일정과 공정한 가격을 제시합니다.
            최소 공급가와 VAT를 고려하여 정확한 견적을 산출합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _create_proposal_writer(self) -> Agent:
        """견적서 작성 Agent 생성"""
        return Agent(
            role="견적서 작성 전문가",
            goal="바로 고객에게 보내도 되는 전문적인 견적서를 작성합니다.",
            backstory="""당신은 비즈니스 문서 작성 전문가입니다.
            명확하고 전문적인 문구로 견적서를 작성하며, 면책 문구를 적절히 포함합니다.
            마케팅 문구보다는 실무 문서 톤을 유지합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _extract_json_from_result(self, result_str: str) -> Optional[Dict[str, Any]]:
        """결과 문자열에서 JSON 추출"""
        try:
            # JSON 코드 블록에서 추출 시도
            if "```json" in result_str:
                json_start = result_str.find("```json") + 7
                json_end = result_str.find("```", json_start)
                json_str = result_str[json_start:json_end].strip()
            elif "```" in result_str:
                json_start = result_str.find("```") + 3
                json_end = result_str.find("```", json_start)
                json_str = result_str[json_start:json_end].strip()
            else:
                # JSON 객체 찾기
                json_start = result_str.find("{")
                json_end = result_str.rfind("}") + 1
                json_str = result_str[json_start:json_end]
            
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON 추출 실패: {e}")
            return None
    
    def _validate_and_adjust_pricing(self, quote_json: Dict[str, Any]) -> Dict[str, Any]:
        """견적 가격 검증 및 조정"""
        if "pricing" not in quote_json:
            quote_json["pricing"] = {}
        
        pricing = quote_json["pricing"]
        subtotal = pricing.get("subtotal", 0)
        
        # 최소 공급가 검증
        if subtotal < self.min_subtotal:
            subtotal = self.min_subtotal
        
        # VAT 재계산
        vat = int(subtotal * self.vat_rate)
        total = subtotal + vat
        
        quote_json["pricing"] = {
            "subtotal": subtotal,
            "vat": vat,
            "total": total,
            "currency": "KRW"
        }
        
        return quote_json
    
    def _get_default_quote(self, client_name: str) -> Dict[str, Any]:
        """기본 견적서 반환"""
        return {
            "project_summary": "요청사항을 바탕으로 한 프로젝트 견적입니다.",
            "scope": ["요청사항 분석", "기술 검토", "구현 작업"],
            "deliverables": ["최종 산출물"],
            "milestones": ["요구사항 확정", "개발 완료", "납품"],
            "assumptions": ["기존 인프라 활용 가능", "고객 협조 가능"],
            "exclusions": ["추가 요구사항", "유지보수"],
            "risks": ["범위 변경 가능성", "일정 지연 가능성"],
            "disclaimer": "본 견적은 참고용이며 범위 확정 시 조정될 수 있습니다. 최종 계약 시 상세 범위를 재확인하여 견적이 변경될 수 있습니다.",
            "delivery_days": 30,
            "pricing": {
                "subtotal": self.min_subtotal,
                "vat": int(self.min_subtotal * self.vat_rate),
                "total": int(self.min_subtotal * (1 + self.vat_rate)),
                "currency": "KRW"
            }
        }
    
    def generate(
        self,
        client_name: str,
        customer_request: str
    ) -> Dict[str, Any]:
        """
        견적서 JSON 생성
        
        Args:
            client_name: 고객명
            customer_request: 고객 요청사항
        
        Returns:
            견적서 JSON 딕셔너리
        """
        logger.info("견적서 생성 시작")
        
        try:
            # Agent 생성
            scope_analyst = self._create_scope_analyst()
            estimator = self._create_estimator()
            proposal_writer = self._create_proposal_writer()
            
            # Task 생성
            scope_task = Task(
                description=f"""
                다음 고객 요청사항을 분석하여 작업 범위를 정의하세요:
                
                요청사항: {customer_request}
                
                다음 항목들을 JSON 형식으로 정리하세요:
                - scope: 작업 범위 배열 (구체적인 작업 항목들)
                - deliverables: 산출물 배열 (최종 결과물들)
                - milestones: 마일스톤 배열 (주요 단계별 완료 시점)
                - assumptions: 가정사항 배열 (전제 조건들)
                - exclusions: 제외 사항 배열 (포함되지 않는 작업들)
                - risks: 리스크 배열 (잠재적 위험 요소들)
                
                각 항목은 구체적이고 실무적으로 작성하세요.
                project_summary에는 고객명을 포함하지 말고 요청 내용 요약만 작성하세요.
                """,
                agent=scope_analyst,
                expected_output="작업 범위, 산출물, 마일스톤, 가정사항, 제외사항, 리스크가 포함된 JSON 형식의 분석 결과"
            )
            
            estimate_task = Task(
                description=f"""
                작업 범위 분석 결과를 바탕으로 견적을 산출하세요.
                
                다음 사항을 반드시 준수하세요:
                - 최소 공급가: {self.min_subtotal:,}원 이상
                - VAT: {self.vat_rate*100}% (부가세)
                - 일정: delivery_days (일 단위, 현실적인 기간)
                - 통화: KRW
                
                견적 금액은 작업 범위의 복잡도와 일정을 고려하여 산출하세요.
                """,
                agent=estimator,
                expected_output="delivery_days와 pricing (subtotal, vat, total, currency)가 포함된 JSON 형식의 견적 산출 결과"
            )
            
            proposal_task = Task(
                description=f"""
                분석 결과와 견적 산출 결과를 종합하여 최종 견적서를 작성하세요.
                
                다음 JSON 스키마를 정확히 준수하여 작성하세요:
                {{
                    "project_summary": "프로젝트 개요 (2-3문장, 고객명 없이 요청 내용 요약만 작성)",
                    "scope": ["작업 범위 1", "작업 범위 2", ...],
                    "deliverables": ["산출물 1", "산출물 2", ...],
                    "milestones": ["마일스톤 1", "마일스톤 2", ...],
                    "assumptions": ["가정사항 1", "가정사항 2", ...],
                    "exclusions": ["제외사항 1", "제외사항 2", ...],
                    "risks": ["리스크 1", "리스크 2", ...],
                    "disclaimer": "면책 문구 (반드시 '본 견적은 참고용이며 범위 확정 시 조정될 수 있습니다'라는 의미 포함)",
                    "delivery_days": 숫자,
                    "pricing": {{
                        "subtotal": 숫자,
                        "vat": 숫자,
                        "total": 숫자,
                        "currency": "KRW"
                    }}
                }}
                
                면책 문구에는 반드시 "본 견적은 참고용이며 범위 확정 시 조정될 수 있습니다"라는 의미가 포함되어야 합니다.
                견적서는 바로 고객에게 보내도 되는 수준의 전문적인 문서로 작성하세요.
                project_summary에는 고객명을 절대 포함하지 말고 요청 내용 요약만 작성하세요.
                """,
                agent=proposal_writer,
                expected_output="완전한 JSON 형식의 견적서 (위 스키마 정확히 준수)"
            )
            
            # Crew 구성 및 실행
            crew = Crew(
                agents=[scope_analyst, estimator, proposal_writer],
                tasks=[scope_task, estimate_task, proposal_task],
                verbose=True
            )
            
            logger.info("CrewAI 실행 중...")
            result = crew.kickoff()
            
            # 결과에서 JSON 추출
            result_str = str(result)
            quote_json = self._extract_json_from_result(result_str)
            
            if quote_json is None:
                logger.warning("JSON 추출 실패, 기본 견적서 사용")
                quote_json = self._get_default_quote(client_name)
            else:
                # 가격 검증 및 조정
                quote_json = self._validate_and_adjust_pricing(quote_json)
            
            logger.info("견적서 생성 완료")
            return quote_json
            
        except Exception as e:
            logger.error(f"견적서 생성 중 오류 발생: {e}", exc_info=True)
            return self._get_default_quote(client_name)


def generate_quote_json(client_name: str, customer_request: str) -> Dict[str, Any]:
    """
    견적서 JSON 생성 (호환성 함수)
    
    Args:
        client_name: 고객명
        customer_request: 고객 요청사항
    
    Returns:
        견적서 JSON 딕셔너리
    """
    generator = QuoteGenerator()
    return generator.generate(client_name, customer_request)
