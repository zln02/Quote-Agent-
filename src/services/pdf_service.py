"""
PDF 생성 서비스
"""
import os
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

from src.config import settings
from src.utils.logger import logger

# 한글 폰트 등록
FONT_NAME = "NotoSansKR"
FONT_BOLD_NAME = "NotoSansKR-Bold"
FONT_REGISTERED = False
FONT_BOLD_REGISTERED = False

# 프로젝트 루트 기준으로 폰트 경로 설정
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_current_dir))
FONT_PATH = os.path.join(_project_root, "fonts", "NotoSansKR-Regular.ttf")
FONT_BOLD_PATH = os.path.join(_project_root, "fonts", "NotoSansKR-Bold.ttf")

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        FONT_REGISTERED = True
        logger.info(f"한글 폰트 등록 완료: {FONT_PATH}")
    else:
        logger.warning(f"한글 폰트 파일이 없습니다: {FONT_PATH}")
        logger.warning("한글 폰트 파일이 없어 한글이 깨질 수 있습니다.")
    
    if os.path.exists(FONT_BOLD_PATH):
        pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, FONT_BOLD_PATH))
        FONT_BOLD_REGISTERED = True
        logger.info(f"한글 Bold 폰트 등록 완료: {FONT_BOLD_PATH}")
except Exception as e:
    logger.warning(f"한글 폰트 등록 실패: {e}")
    logger.warning("한글 폰트 파일이 없어 한글이 깨질 수 있습니다.")


class PDFService:
    """PDF 생성 서비스"""
    
    def __init__(self):
        """초기화"""
        self.output_dir = settings.PROPOSALS_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """스타일 생성"""
        styles = getSampleStyleSheet()
        font_name = FONT_NAME if FONT_REGISTERED else "Helvetica"
        
        return {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                alignment=TA_CENTER
            ),
            'heading': ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=8,
                spaceBefore=12
            ),
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                leading=14,
                alignment=TA_LEFT
            )
        }
    
    def _build_content(self, quote_json: Dict[str, Any], client_name: str) -> list:
        """PDF 내용 구성"""
        styles = self._create_styles()
        story = []
        
        # 제목
        story.append(Paragraph("견적서", styles['title']))
        story.append(Spacer(1, 10*mm))
        
        # 고객 정보
        if not client_name:
            client_name = ""
        client_name_escaped = str(client_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        client_name_bold_style = ParagraphStyle(
            'ClientNameBoldStyle',
            parent=styles['normal'],
            fontName=FONT_BOLD_NAME if FONT_BOLD_REGISTERED else (FONT_NAME if FONT_REGISTERED else "Helvetica-Bold"),
            fontSize=10,
            leading=14
        )
        client_name_normal_style = ParagraphStyle(
            'ClientNameNormalStyle',
            parent=styles['normal'],
            fontName=FONT_NAME if FONT_REGISTERED else "Helvetica",
            fontSize=10,
            leading=14
        )
        
        story.append(Paragraph(f"<font name=\"{FONT_BOLD_NAME if FONT_BOLD_REGISTERED else (FONT_NAME if FONT_REGISTERED else 'Helvetica-Bold')}\"><b>고객명:</b></font> <font name=\"{FONT_NAME if FONT_REGISTERED else 'Helvetica'}\">{client_name_escaped}</font>", styles['normal']))
        story.append(Paragraph(
            f"<b>발행일:</b> {datetime.now().strftime('%Y년 %m월 %d일')}",
            styles['normal']
        ))
        story.append(Spacer(1, 5*mm))
        
        # 프로젝트 개요
        story.append(Paragraph("1. 프로젝트 개요", styles['heading']))
        story.append(Paragraph(quote_json.get("project_summary", ""), styles['normal']))
        story.append(Spacer(1, 5*mm))
        
        # 작업 범위
        story.append(Paragraph("2. 작업 범위", styles['heading']))
        for item in quote_json.get("scope", []):
            story.append(Paragraph(f"• {item}", styles['normal']))
        story.append(Spacer(1, 5*mm))
        
        # 산출물
        if quote_json.get("deliverables"):
            story.append(Paragraph("3. 산출물", styles['heading']))
            for item in quote_json.get("deliverables", []):
                story.append(Paragraph(f"• {item}", styles['normal']))
            story.append(Spacer(1, 5*mm))
        
        # 일정
        story.append(Paragraph("4. 일정", styles['heading']))
        delivery_days = quote_json.get("delivery_days", 0)
        story.append(Paragraph(
            f"예상 소요 기간: <b>{delivery_days}일</b>",
            styles['normal']
        ))
        
        milestones = quote_json.get("milestones", [])
        if milestones:
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph("<b>주요 마일스톤:</b>", styles['normal']))
            for milestone in milestones:
                story.append(Paragraph(f"• {milestone}", styles['normal']))
        story.append(Spacer(1, 5*mm))
        
        # 견적
        story.append(Paragraph("5. 견적", styles['heading']))
        pricing = quote_json.get("pricing", {})
        
        pricing_data = [
            ['항목', '금액'],
            ['공급가액', f"{pricing.get('subtotal', 0):,}원"],
            ['부가세 (10%)', f"{pricing.get('vat', 0):,}원"],
            ['합계', f"<b>{pricing.get('total', 0):,}원</b>"]
        ]
        
        table_header_font = FONT_BOLD_NAME if FONT_BOLD_REGISTERED else (FONT_NAME if FONT_REGISTERED else "Helvetica-Bold")
        table_normal_font = FONT_NAME if FONT_REGISTERED else "Helvetica"
        pricing_table = Table(pricing_data, colWidths=[100*mm, 70*mm])
        pricing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), table_header_font),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('FONTNAME', (0, 1), (-1, -1), table_normal_font),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        story.append(pricing_table)
        story.append(Spacer(1, 5*mm))
        
        # 가정사항 및 제외사항
        assumptions = quote_json.get("assumptions", [])
        exclusions = quote_json.get("exclusions", [])
        
        if assumptions or exclusions:
            story.append(Paragraph("6. 기타 사항", styles['heading']))
            
            if assumptions:
                story.append(Paragraph("<b>가정사항:</b>", styles['normal']))
                for item in assumptions:
                    story.append(Paragraph(f"• {item}", styles['normal']))
                story.append(Spacer(1, 3*mm))
            
            if exclusions:
                story.append(Paragraph("<b>제외사항:</b>", styles['normal']))
                for item in exclusions:
                    story.append(Paragraph(f"• {item}", styles['normal']))
                story.append(Spacer(1, 5*mm))
        
        # 면책 문구
        story.append(Paragraph("7. 면책 사항", styles['heading']))
        disclaimer = quote_json.get("disclaimer", "")
        story.append(Paragraph(disclaimer, styles['normal']))
        story.append(Spacer(1, 5*mm))
        
        # 리스크
        risks = quote_json.get("risks", [])
        if risks:
            story.append(Paragraph("8. 주요 리스크", styles['heading']))
            for risk in risks:
                story.append(Paragraph(f"• {risk}", styles['normal']))
            story.append(Spacer(1, 5*mm))
        
        return story
    
    def generate(
        self,
        quote_json: Dict[str, Any],
        client_name: str,
        filename: str
    ) -> str:
        """
        PDF 생성
        
        Args:
            quote_json: 견적서 JSON 딕셔너리
            client_name: 고객명
            filename: 파일명
        
        Returns:
            생성된 PDF 파일 경로
        """
        output_path = os.path.join(self.output_dir, filename)
        
        logger.info(f"PDF 생성 시작: {output_path}")
        
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            story = self._build_content(quote_json, client_name)
            doc.build(story)
            
            logger.info(f"PDF 생성 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF 생성 중 오류 발생: {e}", exc_info=True)
            raise


def generate_pdf(quote_json: Dict[str, Any], output_path: str, client_name: str) -> str:
    """
    PDF 생성 (호환성 함수)
    
    Args:
        quote_json: 견적서 JSON 딕셔너리
        output_path: PDF 저장 경로
        client_name: 고객명
    
    Returns:
        생성된 PDF 파일 경로
    """
    service = PDFService()
    filename = os.path.basename(output_path)
    return service.generate(quote_json, client_name, filename)
