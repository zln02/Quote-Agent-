"""
설정 관리 모듈
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """애플리케이션 설정"""
    
    # API 설정
    API_TITLE: str = "Quote Agent API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # CrewAI 설정
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    VAT_RATE: float = float(os.getenv("VAT_RATE", "0.1"))
    MIN_SUBTOTAL_KRW: int = int(os.getenv("MIN_SUBTOTAL_KRW", "500000"))
    
    # 이메일 설정
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD: Optional[str] = os.getenv("SENDER_PASSWORD")
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Quote Agent")
    
    # Google Sheets 설정
    GOOGLE_SHEET_ID: Optional[str] = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE", 
        "service_account.json"
    )
    
    # 출력 디렉토리
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    PROPOSALS_DIR: str = os.path.join(OUTPUT_DIR, "proposals")
    
    @classmethod
    def validate(cls) -> None:
        """필수 설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되어야 합니다.")
    
    @classmethod
    def ensure_directories(cls) -> None:
        """필요한 디렉토리 생성"""
        os.makedirs(cls.PROPOSALS_DIR, exist_ok=True)


settings = Settings()
