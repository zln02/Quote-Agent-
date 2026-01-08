"""
API 라우트 정의
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.api.models import QuoteRequest, QuoteResponse
from src.core.quote_generator import generate_quote_json
from src.services.pdf_service import generate_pdf
from src.services.email_service import send_email
from src.services.sheets_service import log_to_sheets
from src.config import settings
from src.utils.logger import logger

router = APIRouter()


@router.get("/")
async def root() -> dict:
    """루트 엔드포인트"""
    return {
        "message": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running"
    }


@router.post("/quote", response_model=QuoteResponse)
async def create_quote(request: QuoteRequest) -> QuoteResponse:
    """
    견적서 생성 및 발송 API
    
    처리 흐름:
    1) CrewAI로 견적서 JSON 생성
    2) PDF 생성
    3) 이메일 발송
    4) 구글 시트 로그
    """
    # 요청값 출력
    print("REQ:", request.model_dump())
    
    # 고객명 처리 (무조건 req.client_name만 사용)
    name = request.client_name.strip()
    
    pdf_filename = None
    pdf_path = None
    
    try:
        
        # 1. CrewAI로 견적서 JSON 생성
        try:
            logger.info(f"견적서 생성 요청: {name}")
            quote_json = generate_quote_json(
                client_name="",  # crew에서는 고객명 사용하지 않음
                customer_request=request.customer_request
            )
        except Exception as e:
            logger.error(f"견적서 생성 실패: {e}", exc_info=True)
            return QuoteResponse(
                status="error",
                message="견적서 생성 실패",
                error=f"crew_pipeline 오류: {str(e)}"
            )
        
        # 2. PDF 생성
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"quote_{timestamp}.pdf"
            pdf_path = os.path.join(settings.PROPOSALS_DIR, pdf_filename)
            
            generate_pdf(quote_json, pdf_path, name)
        except Exception as e:
            logger.error(f"PDF 생성 실패: {e}", exc_info=True)
            return QuoteResponse(
                status="error",
                message="PDF 생성 실패",
                error=f"pdf_gen 오류: {str(e)}"
            )
        
        # 3. 이메일 발송
        email_success = False
        try:
            # 이메일 제목/본문 생성
            subject = f"[견적서] {name}님 요청 건"
            body = f"""안녕하세요, {name}님.

요청하신 프로젝트에 대한 참고용 견적서를 작성하여 첨부파일로 보내드립니다.
본 견적은 참고용이며, 범위 확정 시 금액과 일정은 조정될 수 있습니다.

감사합니다.
Quote Agent
"""
            send_email(
                to_email=request.client_email,
                client_name=name,
                pdf_path=pdf_path,
                subject=subject,
                body=body
            )
            email_success = True
        except Exception as e:
            logger.warning(f"이메일 발송 실패: {e}")
        
        # 4. Google Sheets에 로그 기록 (실패해도 서비스는 계속)
        service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
        if not os.path.exists(service_account_path):
            print(f"service_account.json not found: {service_account_path}")
            logger.warning(f"서비스 계정 파일이 없어 Google Sheets 로깅을 건너뜁니다: {service_account_path}")
        else:
            try:
                log_to_sheets(
                    client_name=name,
                    client_email=request.client_email,
                    quote_json=quote_json
                )
            except Exception as e:
                print(f"SHEETS_LOG_ERROR: {repr(e)}")
                logger.warning(f"Google Sheets 로깅 실패: {str(e)}")
        
        # 성공 응답
        message = (
            "견적서가 생성되고 발송되었습니다."
            if email_success
            else "견적서가 생성되었습니다. (이메일 발송 실패)"
        )
        
        logger.info(f"견적서 처리 완료: {name}")
        return QuoteResponse(
            status="success",
            message=message,
            pdf_filename=pdf_filename,
            pdf_path=pdf_path
        )
        
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}", exc_info=True)
        return QuoteResponse(
            status="error",
            message="처리 중 오류 발생",
            error=str(e),
            pdf_filename=pdf_filename,
            pdf_path=pdf_path
        )
