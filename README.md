# 📰 Crypto News ETL + RAG Insight Service

A data engineering pipeline that ingests cryptocurrency news into PostgreSQL and provides intelligent question-answering through Retrieval-Augmented Generation (RAG) powered by DeepSeek AI.

## ✨ Features

- **Automated ETL Pipeline**: Fetches crypto news from multiple categories without requiring API keys
- **PostgreSQL Storage**: Optimized schema with deduplication and indexing
- **Vector Search**: FAISS-powered semantic search using SentenceTransformer embeddings
- **RAG Q&A**: Natural language question-answering using DeepSeek AI
- **Live Market Data**: Real-time crypto prices from CoinGecko for ranking queries
- **Analytics Dashboard**: Insights on trending tickers, top sources, and article distribution
- **Interactive UI**: Streamlit interface with ETL controls, analytics visualizations, and Q&A chat

## 🏗️ Architecture

```
cryptocurrency.cv API                    CoinGecko API
        ↓                                       ↓
ETL Pipeline (Fetch → Clean → Load)     Market Data
        ↓                                       ↓
PostgreSQL Database ←────────────────────────────┘
        ↓
FAISS Vector Store (SentenceTransformer embeddings)
        ↓
RAG Q&A Engine (Retrieval + DeepSeek Generation)
        ↓
Streamlit UI (Ask Questions / Analytics / ETL Controls)
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.9+ |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy |
| **Vector Store** | FAISS |
| **Embeddings** | SentenceTransformers (all-MiniLM-L6-v2) |
| **LLM** | DeepSeek API (with retrieval-only fallback) |
| **Market Data** | CoinGecko API |
| **UI** | Streamlit |
| **Data Processing** | Pandas, NumPy |

## 📊 Database Schema

```sql
news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source VARCHAR(255),
    url VARCHAR(500) UNIQUE,
    published_at TIMESTAMP,
    ticker VARCHAR(20),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
)
```

**Indexes**: `published_at`, `ticker` for optimized queries

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- DeepSeek API key (optional, for AI-generated answers)

### Installation

```bash
# Clone the repository
git clone https://github.com/SaahilAlam1/crypto_rag.git
cd crypto_rag

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```env
DATABASE_URL=postgresql://crypto_user:crypto_password123@localhost:5432/crypto_news_rag
DEEPSEEK_API_KEY=your_deepseek_api_key_here  # Get at https://platform.deepseek.com
```

### Database Setup

```bash
# Create PostgreSQL database
createdb crypto_news_rag

# Initialize tables
python -c "from etl.database import init_db; init_db()"
```

### Run the Application

```bash
# 1. Run ETL pipeline (fetch and load news)
python -m etl.pipeline

# 2. Launch Streamlit UI
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## 📱 Application Tabs

### 1. Ask Questions
- Natural language queries about crypto news
- Example: "What are the latest Bitcoin developments?"
- Example: "What are the top 3 cryptos right now?" (uses live CoinGecko data)
- Returns answer with source URLs for verification

### 2. Analytics
- Articles per ticker visualization
- Top news sources ranking
- Recent headlines filtered by cryptocurrency

### 3. ETL Pipeline
- Manual trigger for news fetching
- Adjustable pagination (fetch 1-20 pages)
- Rebuild FAISS index after new data

## 📈 Sample Analytics

- **Trending Tickers**: BTC, ETH, SOL based on article frequency
- **Top Sources**: CoinDesk, CoinTelegraph, Decrypt
- **Time Analysis**: Daily article distribution across 10+ categories

## 🤖 RAG Implementation Details

1. **Embedding**: Articles encoded using SentenceTransformer (384-dimensional vectors)
2. **Indexing**: FAISS IndexFlatIP for efficient similarity search
3. **Retrieval**: Top-k nearest neighbors based on query embedding
4. **Generation**: Retrieved contexts + user query → DeepSeek AI → grounded answer
5. **Market Data**: Live prices from CoinGecko for ranking/price questions
6. **Fallback**: If no DeepSeek key, returns retrieved article snippets

## 📁 Project Structure

```
crypto_rag/
├── app.py                 # Streamlit UI (3 tabs)
├── etl/
│   ├── __init__.py
│   ├── database.py       # SQLAlchemy models & PostgreSQL setup
│   ├── fetch_news.py     # API integration (cryptocurrency.cv)
│   └── pipeline.py       # Full ETL orchestration
├── rag/
│   ├── __init__.py
│   ├── index.py          # FAISS vector store builder
│   ├── qa.py             # RAG question-answering (DeepSeek)
│   └── market_data.py    # CoinGecko live prices
├── analytics/
│   ├── __init__.py
│   └── queries.py        # Analytics functions
├── requirements.txt
├── .env.example
└── README.md
```

## 🔄 Scheduled Updates (Optional)

Run ETL automatically with cron:

```bash
# Run every 6 hours
0 */6 * * * cd /path/to/project && .venv/bin/python -m etl.pipeline
```

## 🎯 Use Cases

- **Market Intelligence**: Track trending cryptocurrencies in real-time
- **News Aggregation**: Centralize crypto news from multiple categories
- **Research Assistant**: Ask questions about recent developments
- **Price Queries**: Get live rankings with CoinGecko integration
- **Sentiment Tracking**: Monitor news volume for specific tokens


## ⚡ Performance

- **Ingestion**: ~54 articles in under 30 seconds (5 pages)
- **Vector Search**: Sub-second retrieval with FAISS
- **Database**: Indexed queries for fast analytics
- **UI**: Cached FAISS index for instant startup
