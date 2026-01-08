"""
Google Sheets 로그 서비스
"""
import os
from typing import Optional
from datetime import datetime

from src.config import settings
from src.utils.logger import logger

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    logger.warning("gspread가 설치되지 않았습니다. Google Sheets 로깅이 비활성화됩니다.")


class SheetsService:
    """Google Sheets 로그 서비스"""
    
    def __init__(self):
        """초기화"""
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self.service_account_file = settings.GOOGLE_SERVICE_ACCOUNT_FILE
        self.available = GSPREAD_AVAILABLE
    
    def log(
        self,
        client_name: str,
        client_email: str,
        quote_json: dict,
        sheet_id: Optional[str] = None
    ) -> bool:
        """
        견적서 생성 내역을 Google Sheets에 기록
        
        Args:
            client_name: 고객명
            client_email: 고객 이메일
            quote_json: 견적서 JSON 데이터
            sheet_id: Google Sheets ID (선택)
        
        Returns:
            기록 성공 여부
        """
        if not self.available:
            logger.debug("Google Sheets 로깅이 비활성화되어 있습니다.")
            return False
        
        sheet_id = sheet_id or self.sheet_id
        
        if not sheet_id:
            error_msg = "GOOGLE_SHEET_ID 환경변수가 설정되지 않았습니다."
            print(error_msg)
            logger.debug(error_msg)
            return False
        
        if not os.path.exists(self.service_account_file):
            error_msg = f"{self.service_account_file} 파일이 없습니다."
            print(error_msg)
            logger.warning(error_msg)
            return False
        
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=scope
            )
            client = gspread.authorize(creds)
            
            sheet = client.open_by_key(sheet_id).sheet1
            
            headers = sheet.row_values(1)
            if not headers:
                error_msg = "Google Sheets 에러: 시트의 1행 헤더를 읽을 수 없습니다."
                print(error_msg)
                logger.error(error_msg)
                return False
            
            print(f"Google Sheets 헤더 확인: {headers}")
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            project_summary = quote_json.get("project_summary", "")
            scope_list = quote_json.get("scope", [])
            scope_str = "\n".join(scope_list) if isinstance(scope_list, list) else str(scope_list)
            pricing = quote_json.get("pricing", {})
            subtotal = pricing.get("subtotal", "")
            vat = pricing.get("vat", "")
            total = pricing.get("total", "")
            currency = pricing.get("currency", "KRW")
            delivery_days = quote_json.get("delivery_days", "")
            
            row = {
                "시간": now,
                "고객명": client_name,
                "이메일": client_email,
                "요청요약": project_summary,
                "작업범위": scope_str,
                "공급가": subtotal,
                "부가세": vat,
                "합계": total,
                "통화": currency,
                "소요일수": delivery_days
            }
            
            values = [row.get(h, "") for h in headers]
            sheet.append_row(values)
            
            logger.info(f"Google Sheets에 로그 기록 완료: {client_name}")
            return True
            
        except Exception as e:
            print(f"SHEETS_LOG_ERROR: {repr(e)}")
            logger.error(f"Google Sheets 로깅 중 오류 발생: {str(e)}", exc_info=True)
            return False


def log_to_sheets(
    client_name: str,
    client_email: str,
    quote_json: dict,
    sheet_id: Optional[str] = None
) -> bool:
    """
    Google Sheets 로그 기록 (호환성 함수)
    
    Args:
        client_name: 고객명
        client_email: 고객 이메일
        quote_json: 견적서 JSON 데이터
        sheet_id: Google Sheets ID (선택)
    
    Returns:
        기록 성공 여부
    """
    service = SheetsService()
    return service.log(client_name, client_email, quote_json, sheet_id)
