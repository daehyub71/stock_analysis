# 배포 가이드: Frontend → Vercel / Backend → Google Cloud Run

## 아키텍처

```
[사용자] → [Vercel (React SPA)] → [Google Cloud Run (FastAPI)] → [Supabase (DB)]
                                                                 → [SQLite (가격 로컬)]
```

| 구성 요소 | 플랫폼 | 역할 |
|-----------|--------|------|
| Frontend | Vercel | React SPA 호스팅, CDN |
| Backend | Google Cloud Run | FastAPI API 서버 |
| Database | Supabase (클라우드) | 분석/종목/포트폴리오 데이터 |
| Price DB | SQLite (로컬) | 가격 히스토리 (Cloud Run에서는 비어있음) |
| Data Pipeline | GitHub Actions | 자동 데이터 수집 (독립 실행) |

---

## 사전 준비

### 필요한 도구
- [Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Vercel CLI](https://vercel.com/docs/cli) (`npm i -g vercel`)
- [Node.js](https://nodejs.org/) v18+

### 필요한 계정
- Google Cloud Platform 계정 + 프로젝트
- Vercel 계정 (GitHub 연동 권장)
- Supabase 프로젝트 (이미 사용 중)

---

## Step 1: Google Cloud 초기 설정

```bash
# 1. gcloud CLI 로그인
gcloud auth login

# 2. 프로젝트 설정 (기존 프로젝트 또는 새로 생성)
gcloud config set project YOUR_PROJECT_ID

# 3. 필요한 API 활성화
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# 4. Artifact Registry 저장소 생성 (서울 리전)
gcloud artifacts repositories create stock-analysis \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="Stock Analysis Dashboard"
```

---

## Step 2: Backend → Google Cloud Run 배포

### 2-1. Docker 이미지 빌드 & 푸시

```bash
cd c:\data_analysis\stock_analysis\stock_analysis

# Docker 인증 설정
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 이미지 빌드
docker build -t asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/stock-analysis/backend:latest ./backend

# 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/stock-analysis/backend:latest
```

### 2-2. Cloud Run 배포

```bash
gcloud run deploy stock-analysis-backend \
    --image=asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/stock-analysis/backend:latest \
    --platform=managed \
    --region=asia-northeast3 \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --timeout=60 \
    --set-env-vars="APP_ENV=production,DEBUG=False,LOG_LEVEL=WARNING" \
    --set-env-vars="SUPABASE_URL=실제_SUPABASE_URL" \
    --set-env-vars="SUPABASE_KEY=실제_SUPABASE_KEY" \
    --set-env-vars="OPENAI_API_KEY=실제_OPENAI_KEY" \
    --set-env-vars="CORS_ORIGINS=https://your-app.vercel.app"
```

### 2-3. 배포 확인

```bash
# 서비스 URL 확인
BACKEND_URL=$(gcloud run services describe stock-analysis-backend \
    --region=asia-northeast3 --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"

# 헬스체크
curl $BACKEND_URL/health

# API 테스트
curl "$BACKEND_URL/api/stocks?page=1&page_size=1"
```

---

## Step 3: Frontend → Vercel 배포

### 3-1. Vercel CLI 설치

```bash
npm install -g vercel
```

### 3-2. 프로젝트 배포

```bash
cd c:\data_analysis\stock_analysis\stock_analysis\frontend

# 초기 배포 (대화형)
vercel

# 프롬프트 응답:
# - Set up and deploy? → Y
# - Link to existing project? → N
# - Project name → stock-analysis-dashboard
# - In which directory is your code? → ./
# - Want to modify settings? → Y
#   - Build Command → npm run build
#   - Output Directory → dist
```

### 3-3. 환경변수 설정

```bash
# Cloud Run 백엔드 URL 설정 (반드시 /api 포함)
vercel env add VITE_API_URL
# 값: https://stock-analysis-backend-xxxxx.a.run.app/api
# 환경: Production, Preview 선택
```

### 3-4. 프로덕션 배포

```bash
vercel --prod
```

---

## Step 4: CORS 업데이트

Vercel 배포 후 확정된 도메인으로 Cloud Run CORS 설정 업데이트:

```bash
gcloud run services update stock-analysis-backend \
    --region=asia-northeast3 \
    --update-env-vars="CORS_ORIGINS=https://stock-analysis-dashboard.vercel.app,http://localhost:3000,http://localhost:5173"
```

---

## Step 5: 검증 체크리스트

| 항목 | 확인 방법 | 기대 결과 |
|------|-----------|-----------|
| Backend 헬스체크 | `curl BACKEND_URL/health` | `{"status":"healthy"}` |
| Backend DB 연결 | `curl BACKEND_URL/health/db` | Supabase connected |
| Backend API | `curl BACKEND_URL/api/stocks?page=1&page_size=1` | 종목 데이터 반환 |
| Frontend 로딩 | Vercel URL 접속 | 대시보드 렌더링 |
| SPA 라우팅 | `/stocks/005930` 직접 접속 | 페이지 정상 로딩 (404 아님) |
| CORS | 브라우저 콘솔 확인 | CORS 에러 없음 |
| 종목 목록 | 메인 페이지 | 종목 + 점수 표시 |
| 분석 상세 | 종목 클릭 | 분석 결과 표시 |
| 포트폴리오 | 포트폴리오 생성/조회 | 정상 동작 |

---

## GitHub Actions (변경 불필요)

기존 3개 워크플로우는 GitHub Runner에서 독립 실행되므로 Cloud Run/Vercel과 무관합니다.

| Workflow | 주기 | 대상 |
|----------|------|------|
| collect-prices | 평일 20:30 KST | 시세 데이터 → Supabase |
| collect-quarterly | 분기별 | 재무 데이터 → Supabase |
| collect-sentiment | 월/목 21:00 KST | 감성 분석 → Supabase |

---

## 알려진 제한사항

### SQLite (가격 데이터)
- Cloud Run은 stateless → 컨테이너 재시작 시 SQLite 초기화
- **영향**: 가격 차트, 백테스트 기능 (빈 데이터 반환)
- **영향 없음**: 종목 목록, 분석 점수, 랭킹, 포트폴리오 (Supabase 사용)
- **향후 해결**: 가격 데이터도 Supabase로 마이그레이션 가능

---

## 업데이트 & 재배포

### Backend 재배포
```bash
# 이미지 재빌드 & 푸시
docker build -t asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/stock-analysis/backend:latest ./backend
docker push asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/stock-analysis/backend:latest

# Cloud Run 업데이트
gcloud run deploy stock-analysis-backend \
    --image=asia-northeast3-docker.pkg.dev/YOUR_PROJECT_ID/stock-analysis/backend:latest \
    --region=asia-northeast3
```

### Frontend 재배포
```bash
cd frontend
vercel --prod
```

### GitHub 연동 시 자동 배포
- Vercel: GitHub repo 연결하면 push 시 자동 빌드/배포
- Cloud Run: Cloud Build 트리거 설정으로 자동화 가능

---

## 비용 참고

| 서비스 | 무료 티어 | 초과 시 |
|--------|-----------|---------|
| Vercel (Frontend) | 월 100GB 대역폭, 무제한 배포 | $20/월~ |
| Cloud Run (Backend) | 월 200만 요청, 360,000 vCPU초 | 종량제 |
| Supabase (DB) | 이미 사용 중 | 기존 플랜 |
| Artifact Registry | 월 0.5GB 무료 | $0.10/GB |
