"""
이메일 발송 서비스
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header

from src.config import settings
from src.utils.logger import logger


class EmailService:
    """이메일 발송 서비스"""
    
    def __init__(self):
        """초기화"""
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.sender_email = settings.SENDER_EMAIL
        self.sender_password = settings.SENDER_PASSWORD
        self.sender_name = settings.SENDER_NAME
        
        if not self.sender_email or not self.sender_password:
            logger.warning("이메일 설정이 완료되지 않았습니다.")
    
    def send(
        self,
        to_email: str,
        client_name: str,
        pdf_path: str,
        subject: str,
        body: str
    ) -> bool:
        """
        견적서 PDF를 이메일로 발송
        
        Args:
            to_email: 수신자 이메일 주소
            client_name: 고객명
            pdf_path: 첨부할 PDF 파일 경로
            subject: 이메일 제목
            body: 이메일 본문
        
        Returns:
            발송 성공 여부
        """
        if not self.sender_email or not self.sender_password:
            raise ValueError("SENDER_EMAIL과 SENDER_PASSWORD 환경변수가 설정되어야 합니다.")
        
        logger.info(f"이메일 발송 시작: {to_email} (고객명: {client_name})")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8').encode()
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # PDF 파일 첨부
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_path)}'
            )
            msg.attach(part)
            
            # 이메일 발송
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            
            logger.info(f"이메일 발송 완료: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 중 오류 발생: {e}", exc_info=True)
            raise


def send_email(to_email: str, client_name: str, pdf_path: str, subject: str, body: str) -> bool:
    """
    이메일 발송 (호환성 함수)
    
    Args:
        to_email: 수신자 이메일 주소
        client_name: 고객명
        pdf_path: 첨부할 PDF 파일 경로
        subject: 이메일 제목
        body: 이메일 본문
    
    Returns:
        발송 성공 여부
    """
    service = EmailService()
    return service.send(to_email, client_name, pdf_path, subject, body)
