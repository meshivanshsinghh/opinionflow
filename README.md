# OpinionFlow 🗣️

**Real‑time, cross‑store product‑review intelligence**
Bright Data Real‑Time AI Agents Challenge (May 2025)

---

## 1 · Why OpinionFlow?

Shoppers drown in thousands of fragmented reviews. OpinionFlow turns that chaos into clarity: it scrapes fresh reviews from **Amazon and Walmart** in real‑time, distills crowd sentiment with AI, and surfaces instant, source‑cited insights—so anyone can decide with confidence.

Powered by **Bright Data MCP**, FastAPI, PGVector, and Retrieval‑Augmented Generation (RAG), OpinionFlow shows judges how reliable web data super‑charges large‑language‑model reasoning.

---

## 2 · Features (MVP)

| 💎 Feature                 | What you see                                                             | Tech behind it                                           |
| -------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------- |
| **Instant Answer Box**     | One‑paragraph, LLM‑grounded summary answering your free‑form question.   | LangChain RAG + Llama‑3, citations linked to review IDs. |
| **Overall Sentiment Card** | "⭐ 4.3 (82 % positive)" metric with color cue.                          | Aggregated star ratings / Text sentiment.                |
| **Top Pros / Cons**        | Three key positives & negatives.                                         | Gemini JSON formatting + frequency analysis.             |
| **Store Tabs**             | Per‑store breakdown for Amazon / Walmart plus "All Sources" tab.         | Separate scrape & analysis pipelines.                    |
| **Aspect Mini‑Charts**     | Dynamic bar charts (battery, comfort, longevity …) per product category. | YAML aspect map + AI scoring.                            |
| **Source Explorer**        | Expandable snippets with outbound review links.                          | PGVector similarity search.                              |

---

## 3 · Quick Start (local)

```bash
# clone & configure
git clone https://github.com/<your‑handle>/opinionflow.git
cd opinionflow
cp .env.example .env          # add Bright Data token, DB creds, LLM keys

# launch everything
docker compose up --build     # FastAPI + Streamlit → http://localhost:8501
```

Enter a product (e.g. **“Dior Sauvage EDT”**) and watch insights populate in \~30 s.

---

## 4 · Tech Stack

| Layer                  | Choice                                        | Hackathon category satisfied        |
| ---------------------- | --------------------------------------------- | ----------------------------------- |
| Front‑end              | **Streamlit**                                 | Frontend                            |
| Backend / Model Access | **FastAPI + LangChain**                       | Backend                             |
| Embeddings & RAG       | **SentenceTransformers (MiniLM) + LangChain** | Embeddings & RAG                    |
| Data & Retrieval       | **Postgres + PGVector**                       | PGVector                            |
| LLM                    | **Llama‑3‑Instruct** (Ollama / Together AI)   | Large Language Models               |
| Scraping / Interaction | **Bright Data Web Unlocker + MCP Browser**    | Discover, Access, Extract, Interact |

---

## 5 · Architecture at a Glance

```
┌────────────── Cloud Run container ───────────────┐
│ Streamlit 8501     FastAPI /analyze 8080         │
│   ├─ discover_urls() – Bright Data SERP          │
│   ├─ scrape_reviews() – Web Unlocker + click     │
│   ├─ extract → JSON                              │
│   ├─ embed → PGVector                            │
│   └─ RAG QA → LLM                                │
│                                                  │
│ Cloud SQL socket  →  Postgres (+PGVector)        │
└───────────────────────────────────────────────────┘
```

Directory map

```
.cursor/rules/      development guard‑rails
backend/            FastAPI + Bright Data client + analysis
frontend/           Streamlit UI
data/               aspects.yaml, prompt templates
Dockerfile          single image build
```

---

## 6 · Environment Variables (`.env.example`)

```dotenv
# Bright Data
BRIGHT_DATA_TOKEN=
BRIGHT_DATA_SERP_ZONE=
BRIGHT_DATA_BROWSER_ZONE=

# Database
DATABASE_URL=postgresql+asyncpg://pguser:pgpass@db:5432/opinionflow

# LLM / Embedding
OPENAI_API_KEY=
OLLAMA_BASE_URL=
```

---

## 7 · Development Road‑map

1. **Scaffold** repo – follow `.cursor/rules/opinionflow.mdc`.
2. **Implement** discover → scrape → extract for Amazon.
3. **Store** reviews & embeddings; test PGVector search.
4. **Build** analysis chain (pros/cons, sentiment, RAG answer).
5. **Add** Walmart & Amazon extractors.
6. **Wire** Streamlit UI panels.
7. **Deploy** to Cloud Run; attach Secret Manager creds.
8. **Polish** docs, add screenshots, record demo.

---

## 8 · Scripts & Commands

| Purpose                  | Command                                                   |
| ------------------------ | --------------------------------------------------------- |
| Lint & format            | `ruff check . && ruff format .`                           |
| Run tests                | `pytest -q`                                               |
| DB migration             | `alembic revision --autogenerate && alembic upgrade head` |
| Start local dev API only | `uvicorn backend.main:app --reload`                       |

---

## 9 · Bright Data Compliance

OpinionFlow exercises all four MCP actions:

1. **Discover** – SERP API fetches review URLs.
2. **Access** – Web Unlocker fetches product/review pages.
3. **Extract** – site‑specific parsers convert HTML → JSON.
4. **Interact** – Playwright scrolls and clicks “Next page”.

We scrape only public data, respect rate limits, and store credentials solely in secret vars.

---

## 10 · Contributing

Follow _Conventional Commits_, run tests before PR, and adhere to `.cursor/rules/opinionflow.mdc` (async‑only, no hard‑coded secrets). CI pipeline blocks merges that fail lint or tests.

---

## License

[MIT](LICENSE)
