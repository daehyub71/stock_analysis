# Stock Analysis Dashboard

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🇰🇷 [한국어 문서](README_KO.md)

A comprehensive Korean stock analysis system that combines **technical analysis**, **fundamental analysis**, and **sentiment analysis** to provide investment scoring for KOSPI/KOSDAQ stocks.

## Features

### 📊 Multi-Dimensional Analysis
- **Technical Analysis (30 points)**
  - Moving Average arrangement (MA5/20/60/120)
  - MA divergence analysis
  - RSI (14-day)
  - MACD (12, 26, 9)
  - Volume analysis

- **Fundamental Analysis (50 points)**
  - Valuation metrics: PER, PBR, PSR
  - Growth metrics: Revenue growth, Operating profit growth
  - Profitability: ROE, Operating margin
  - Financial stability: Debt ratio, Current ratio

- **Sentiment Analysis (20 points)**
  - News sentiment analysis (OpenAI GPT-4o-mini)
  - Google Trends integration
  - **Manual news rating system** (-10 to +10)

### 🤖 AI-Powered Features
- **LLM Commentary**: Automated Korean investment commentary using GPT-4o-mini
- **News Sentiment Analysis**: Automatic sentiment classification of financial news
- **Manual Override**: User can rate news manually to replace automatic analysis

### 📈 Dashboard Features
- Real-time stock price display
- Interactive price charts with MA overlays
- Stock comparison (up to 4 stocks)
- Historical analysis tracking
- Score-based stock ranking
- Advanced filtering by sector, score, market

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API framework |
| SQLAlchemy | ORM for SQLite (price data) |
| Supabase | Cloud database (analysis data) |
| pykrx | Korean stock data collector |
| OpenAI API | Sentiment analysis & commentary |
| pandas/numpy | Data processing |
| ta (Technical Analysis) | Technical indicators |

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool |
| TanStack Query | Server state management |
| Zustand | Client state management |
| Tailwind CSS | Styling |
| Recharts | Data visualization |
| Lightweight Charts | Price charts |

### Data Sources
- **KIS API** (Korea Investment & Securities): Real-time prices
- **pykrx**: Historical price data (backup)
- **Naver Finance**: Financial statements, valuation metrics
- **Google Trends**: Search trend data
- **Naver News**: Financial news crawling

## Project Structure

```
stock_analysis/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── analysis.py   # Analysis endpoints
│   │   │   ├── stocks.py     # Stock endpoints
│   │   │   └── portfolios.py # Portfolio endpoints
│   │   ├── collectors/       # Data collectors
│   │   │   ├── kis_api.py    # KIS API client
│   │   │   ├── pykrx_collector.py
│   │   │   ├── naver_finance.py
│   │   │   ├── news_collector.py
│   │   │   └── google_trends.py
│   │   ├── services/         # Business logic
│   │   │   ├── technical.py  # Technical analysis
│   │   │   ├── fundamental.py # Fundamental analysis
│   │   │   ├── sentiment.py  # Sentiment analysis
│   │   │   ├── scoring.py    # Score calculation
│   │   │   └── commentary.py # LLM commentary
│   │   ├── analyzers/        # Analysis modules
│   │   │   ├── indicators.py # Technical indicators
│   │   │   └── openai_sentiment.py
│   │   ├── db/               # Database
│   │   │   ├── sqlite_db.py  # Price data (local)
│   │   │   └── supabase_db.py # Analysis data (cloud)
│   │   ├── models/           # Pydantic models
│   │   └── main.py           # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── StockDetailPage.tsx
│   │   │   ├── ComparePage.tsx
│   │   │   └── HistoryPage.tsx
│   │   ├── components/       # UI components
│   │   │   ├── dashboard/
│   │   │   ├── charts/
│   │   │   ├── analysis/
│   │   │   └── common/
│   │   ├── services/         # API client
│   │   ├── stores/           # Zustand stores
│   │   └── types/            # TypeScript types
│   └── package.json
├── scripts/                  # Automation scripts
│   ├── collect_daily_prices.py
│   ├── run_daily_analysis.py
│   └── collect_news.py
├── docs/                     # Documentation
└── .github/workflows/        # GitHub Actions
```

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account
- OpenAI API key
- KIS API credentials (optional)

### Backend Setup

```bash
# Clone repository
git clone https://github.com/yourusername/stock_analysis.git
cd stock_analysis

# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Variables

Create `backend/.env`:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key

# KIS API (optional)
KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret
KIS_ACCOUNT_TYPE=VIRTUAL  # or REAL

# Database
SQLITE_DB_PATH=./data/stock_prices.db
```

## Usage

### Start the Application

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Access the dashboard at `http://localhost:3000`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks` | List stocks with filters |
| GET | `/api/stocks/{code}` | Get stock details |
| GET | `/api/stocks/{code}/history` | Get price history |
| GET | `/api/stocks/compare` | Compare multiple stocks |
| GET | `/api/analysis/{code}` | Get analysis results |
| POST | `/api/analysis/{code}/run` | Run new analysis |
| GET | `/api/analysis/{code}/commentary` | Get AI commentary |
| GET | `/api/analysis/{code}/news` | Get news list |
| PUT | `/api/analysis/{code}/news/{id}/rate` | Rate news item |

### Automated Data Collection

```bash
# Daily price collection (GitHub Actions or cron)
python scripts/collect_daily_prices.py

# Run analysis for all stocks
python scripts/run_daily_analysis.py

# Collect news
python scripts/collect_news.py
```

## Scoring System

### Grade Calculation

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A+ | 90-100 | Excellent |
| A | 80-89 | Very Good |
| B+ | 70-79 | Good |
| B | 60-69 | Above Average |
| C+ | 50-59 | Average |
| C | 40-49 | Below Average |
| D | 30-39 | Poor |
| F | 0-29 | Very Poor |

### Score Components

```
Total Score (100) = Technical (30) + Fundamental (50) + Sentiment (20)

Technical (30):
├── MA Arrangement: 6
├── MA Divergence: 6
├── RSI: 5
├── MACD: 5
└── Volume: 8

Fundamental (50):
├── PER: 8
├── PBR: 7
├── PSR: 5
├── Revenue Growth: 6
├── OP Growth: 6
├── ROE: 5
├── OP Margin: 5
├── Debt Ratio: 4
└── Current Ratio: 4

Sentiment (20):
├── News Sentiment: 10
├── News Impact: 6
└── News Volume/Interest: 4
```

## Screenshots

### 1. Main Dashboard
The main dashboard displays all stocks with their scores, grades, and score distribution bars. Users can filter by sector, market (KOSPI/KOSDAQ), and sort by various criteria.

![Main Dashboard](docs/screenshots/dash_00.png)

**Features shown:**
- Portfolio summary (total stocks, average score, gainers/losers)
- Stock table with real-time prices and change rates
- Visual score breakdown bars (Technical/Fundamental/Sentiment)
- Quick grade indicators (A+, A, B+, B, C+, C, D, F)

---

### 2. Stock Detail - Overview & AI Commentary
The stock detail page shows comprehensive analysis with AI-generated investment commentary.

![Stock Overview](docs/screenshots/stock_news_04.png)

**Features shown:**
- Stock header with current price and change rate
- Total score with grade badge
- Score breakdown cards (Technical 23.0/30, Fundamental 27.0/50, Sentiment 15.0/20)
- AI-generated Korean investment commentary with key insights and risk factors

---

### 3. Technical Analysis Tab
Interactive price chart with moving average overlays and detailed technical indicators.

![Technical Analysis](docs/screenshots/stock_tech_02.png)

**Features shown:**
- Price chart with MA5, MA20, MA60, MA120 lines
- Technical score cards (MA Arrangement, MA Divergence, RSI, MACD, Volume)
- Detailed indicator values and interpretation
- RSI gauge visualization (oversold/neutral/overbought zones)

---

### 4. Fundamental Analysis Tab
Comprehensive financial metrics organized by category with visual scoring.

![Fundamental Analysis](docs/screenshots/stock_basic_03.png)

**Features shown:**
- Valuation metrics: PER (9.7), PBR (1.60), PSR (4.44)
- Profitability indicators: ROE (21.1%), Operating Margin (43.6%)
- Growth metrics: Revenue Growth (+41.8%), OP Growth (+54.0%)
- Financial stability: Debt Ratio (16.0%), Current Ratio (231.2%)

---

### 5. Sentiment Analysis & News Rating
Manual news rating system that allows users to override automatic sentiment analysis.

![Sentiment Analysis](docs/screenshots/stock_total_01.png)

**Features shown:**
- Current sentiment status with manual/auto indicator
- Manual rating notification when user ratings are applied
- News rating interface with -10 to +10 scale
- Individual news items with rating buttons
- Real-time score recalculation based on user ratings

## Roadmap

- [x] Phase 1: MVP (Week 1-4)
  - [x] Data collection infrastructure
  - [x] Analysis engine
  - [x] React dashboard
  - [x] LLM commentary
  - [x] Manual news rating

- [x] Phase 2: Week 5
  - [x] Stock comparison
  - [x] Analysis history

- [ ] Phase 2: Week 6-8
  - [ ] Backtesting module
  - [ ] Alert system
  - [ ] Dark mode
  - [ ] Portfolio simulation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and informational purposes only. It is not intended to provide investment advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.

## Acknowledgments

- [pykrx](https://github.com/sharebook-kr/pykrx) - Korean stock data library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Supabase](https://supabase.com/) - Open source Firebase alternative
- [OpenAI](https://openai.com/) - GPT-4o-mini for sentiment analysis
