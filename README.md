# Quote Agent

견적서 자동 생성 및 발송 시스템

## 개요

CrewAI를 활용하여 고객 요청사항을 분석하고 전문적인 견적서를 자동으로 생성하여 PDF로 변환하고 이메일로 발송하는 FastAPI 기반 시스템입니다.

## 주요 기능

- 🤖 **AI 기반 견적서 생성**: CrewAI 3명의 Agent 협업으로 견적서 JSON 생성
- 📄 **PDF 변환**: reportlab을 사용하여 A4 견적서 PDF 생성
- 📧 **이메일 발송**: Gmail SMTP를 통한 자동 이메일 발송
- 📊 **로그 기록**: Google Sheets에 견적서 생성 내역 자동 기록
- 📝 **로깅 시스템**: 구조화된 로깅 시스템
- ⚙️ **설정 관리**: 환경변수 기반 설정 관리

## 프로젝트 구조

```
quote-agent/
├── app.py                    # FastAPI 엔트리 포인트
├── src/
│   ├── __init__.py
│   ├── config.py             # 설정 관리
│   ├── api/                  # API 모듈
│   │   ├── __init__.py
│   │   ├── models.py         # Pydantic 모델
│   │   └── routes.py         # API 라우트
│   ├── core/                 # 핵심 로직
│   │   ├── __init__.py
│   │   └── quote_generator.py # CrewAI 견적 생성
│   ├── services/             # 서비스 레이어
│   │   ├── __init__.py
│   │   ├── pdf_service.py     # PDF 생성 서비스
│   │   ├── email_service.py   # 이메일 발송 서비스
│   │   └── sheets_service.py  # Google Sheets 서비스
│   └── utils/                # 유틸리티
│       ├── __init__.py
│       └── logger.py          # 로깅 유틸리티
├── requirements.txt          # 파이썬 패키지 목록
├── .env                      # 환경변수 설정 (생성 필요)
├── service_account.json      # Google Sheets 서비스 계정 키 (선택)
├── fonts/                    # 한글 폰트 폴더
│   └── NotoSansKR-Regular.ttf # Noto Sans KR 폰트 파일 (필수)
├── output/
│   └── proposals/            # 생성된 PDF 저장 폴더
└── README.md
```

## 설치 방법

### 1. 가상환경 생성 및 활성화

```powershell
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1
```

### 2. 패키지 설치

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 한글 폰트 설치 (필수)

PDF에서 한글이 정상적으로 표시되도록 한글 폰트를 설치해야 합니다.

**Noto Sans KR 폰트 다운로드:**

1. [Google Fonts - Noto Sans KR](https://fonts.google.com/noto/specimen/Noto+Sans+KR) 페이지 접속
2. "Download family" 버튼 클릭하여 ZIP 파일 다운로드
3. 압축 해제 후 `NotoSansKR-Regular.ttf` 파일을 찾습니다
4. 프로젝트 루트에 `fonts/` 폴더가 없으면 생성합니다
5. `fonts/NotoSansKR-Regular.ttf` 경로에 파일을 복사합니다

**또는 직접 다운로드:**
```powershell
# fonts 폴더 생성
New-Item -ItemType Directory -Force -Path fonts

# PowerShell에서 직접 다운로드 (선택사항)
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Regular.ttf" -OutFile "fonts\NotoSansKR-Regular.ttf"
```

**⚠️ 중요:** 폰트 파일이 없으면 PDF에서 한글이 네모(□□□)로 깨져서 표시됩니다.

### 4. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# OpenAI API 키 (CrewAI 사용)
OPENAI_API_KEY=your_openai_api_key_here

# API 설정
API_HOST=0.0.0.0
API_PORT=8000

# VAT 및 최소 공급가 설정
VAT_RATE=0.1
MIN_SUBTOTAL_KRW=500000

# 이메일 발송 설정 (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password_here
SENDER_NAME=Quote Agent

# Google Sheets 설정 (선택)
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# 출력 디렉토리 설정 (선택)
OUTPUT_DIR=output
```

**참고:**
- Gmail 사용 시 앱 비밀번호를 사용해야 합니다. ([설정 방법](https://support.google.com/accounts/answer/185833))
- Google Sheets 사용 시 서비스 계정 키 파일(`service_account.json`)이 필요합니다.

## 실행 방법

### API 서버 시작

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 서버 실행
python -m uvicorn app:app --reload
```

또는

```powershell
python app.py
```

서버가 시작되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

### API 문서

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API 사용 예시

### 견적서 생성 및 발송

**PowerShell에서 Invoke-RestMethod 사용:**

```powershell
$body = @{
    client_name = "테스트 회사"
    client_email = "test@example.com"
    customer_request = "웹사이트 개발 프로젝트"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/quote" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

**curl 사용:**

```bash
curl -X POST "http://localhost:8000/quote" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "테스트 회사",
    "client_email": "test@example.com",
    "customer_request": "웹사이트 개발 프로젝트"
  }'
```

### 응답 예시

```json
{
  "status": "success",
  "message": "견적서가 생성되고 발송되었습니다.",
  "pdf_filename": "quote_20260108_143000.pdf",
  "pdf_path": "output/proposals/quote_20260108_143000.pdf"
}
```

## API 엔드포인트

### `GET /`

서버 상태 확인

**응답:**
```json
{
  "message": "Quote Agent API",
  "version": "1.0.0",
  "status": "running"
}
```

### `POST /quote`

견적서 생성 및 발송

**요청 본문:**
```json
{
  "client_name": "고객명",
  "client_email": "이메일주소",
  "customer_request": "고객 요청사항"
}
```

**응답:**
```json
{
  "status": "success" | "error",
  "message": "메시지",
  "pdf_filename": "파일명",
  "pdf_path": "파일경로",
  "error": "오류 메시지 (오류 시)"
}
```

## 개발 가이드

### 코드 구조

- **API 레이어** (`src/api/`): FastAPI 라우트 및 모델 정의
- **코어 레이어** (`src/core/`): 비즈니스 로직 (CrewAI 견적 생성)
- **서비스 레이어** (`src/services/`): 외부 서비스 연동 (PDF, 이메일, Sheets)
- **유틸리티** (`src/utils/`): 공통 유틸리티 (로깅 등)

### 로깅

로깅은 `src/utils/logger.py`에서 관리됩니다. 기본적으로 콘솔에 출력되며, 필요시 파일 로깅도 가능합니다.

### 설정 관리

모든 설정은 `src/config.py`의 `Settings` 클래스에서 관리됩니다. 환경변수를 통해 설정할 수 있습니다.

## 주의사항

- OpenAI API 키가 필요합니다.
- 이메일 발송을 위해서는 Gmail SMTP 설정이 필요합니다.
- Google Sheets 로깅은 선택 사항이며, 실패해도 서비스는 계속됩니다.
- 생성된 PDF는 `output/proposals/` 폴더에 저장됩니다.
- 최소 공급가는 500,000원이며, VAT는 10%입니다.
- **한글 폰트 파일(`fonts/NotoSansKR-Regular.ttf`)이 없으면 PDF에서 한글이 깨질 수 있습니다.**

## 라이선스

MIT License
