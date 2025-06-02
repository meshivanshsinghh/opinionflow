# OpinionFlow 🗣️

**Real‑time, cross‑store product‑review intelligence**  
_Bright Data Real‑Time AI Agents Challenge (May 2025)_

Shoppers drown in thousands of fragmented reviews. OpinionFlow turns that chaos into clarity: it scrapes fresh reviews from **Amazon and Walmart** in real‑time, distills crowd sentiment with AI, and surfaces instant, source‑cited insights—so anyone can decide with confidence.

Powered by **Bright Data MCP**, FastAPI, PGVector, and Retrieval‑Augmented Generation (RAG).

## Features

🔍 **Smart Product Discovery** - Search across Amazon & Walmart simultaneously  
📊 **AI-Powered Analysis** - Extract and analyze thousands of reviews with sentiment intelligence  
💬 **Interactive Chat** - Ask questions about products and get source-cited answers  
⚡ **Real-time Processing** - Fresh review data with instant insights  
🔗 **Cross-Store Comparison** - Compare products from different retailers side-by-side

## Tech Stack

**Backend:**

- FastAPI (Python)
- PGVector for vector storage
- Transformers & Sentence Transformers for AI
- Bright Data MCP for web scraping
- Google Generative AI

**Frontend:**

- React (Next.js)
- Tailwind CSS
- Lucide Icons

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL with PGVector extension

### Backend Setup

1. **Clone and setup Python environment:**

```bash
git clone <repository-url>
cd opinionflow
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration:**
   Create `.env` file in backend directory:

```env
BRIGHT_DATA_API_KEY=
BRIGHT_DATA_SERP_ZONE=
BRIGHT_DATA_WEBUNLOCKER_ZONE=
GEMINI_API_KEY=
HUGGINGFACE_API_KEY=
PINECONE_API_KEY=
PINECONE_DISCOVERY_INDEX=
PINECONE_ENVIRONMENT=
PINECONE_REVIEWS_INDEX=
```

3. **Start Backend:**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. **Install dependencies:**

```bash
cd react-frontend
npm install
```

2. **Start development server:**

```bash
npm run dev
```

3. **Open browser:**
   Navigate to `http://localhost:3000`

## Usage

1. **Search Products** - Enter a product name to discover items across stores
2. **Select & Compare** - Choose products from different retailers to compare
3. **Analyze Reviews** - Let AI extract and analyze thousands of reviews
4. **Ask Questions** - Chat with the AI about product insights, comparisons, and reviews

## Contributing

This project is part of the Bright Data Real-Time AI Agents Challenge. Contributions welcome!

## License

MIT License
