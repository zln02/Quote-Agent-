"""
API 모델 정의
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class QuoteRequest(BaseModel):
    """견적 요청 모델"""
    client_name: str = Field(..., description="고객명", min_length=1)
    client_email: EmailStr = Field(..., description="고객 이메일")
    customer_request: str = Field(..., description="고객 요청사항", min_length=1)


class QuoteResponse(BaseModel):
    """견적 응답 모델"""
    status: str = Field(..., description="상태 (success/error)")
    message: str = Field(..., description="메시지")
    pdf_filename: Optional[str] = Field(None, description="PDF 파일명")
    pdf_path: Optional[str] = Field(None, description="PDF 파일 경로")
    error: Optional[str] = Field(None, description="오류 메시지")
