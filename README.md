# Research Paper Intelligence Hub 📚

An intelligent platform for searching, summarizing, and analyzing academic papers from multiple global databases. Perfect for researchers writing papers for publication and PhD applications.

## Features

✨ **Multi-Source Search**
- ArXiv, CrossRef, CORE, OpenAlex, PubMed, Europe PMC
- Real-time aggregation from 6+ academic databases

🤖 **AI-Powered Summarization**
- Automatic paper summarization using Hugging Face transformers
- Extract key findings and methodology

📊 **Smart Relevance Scoring**
- Semantic similarity matching with your research topic
- Sort by relevance, date, or citation count

🔗 **Citation Network**
- Visualize paper relationships
- Track influential works in your field

📋 **Export & Organization**
- BibTeX, APA, MLA citation formats
- Save searches and create paper collections

## Tech Stack

**Frontend:**
- React 18.2.0
- TypeScript
- Vite
- Axios

**Backend:**
- FastAPI
- Python 3.10+
- Hugging Face Transformers
- SQLAlchemy (database)
- arXiv, CrossRef APIs

**Deployment:**
- Frontend: Vercel
- Backend: Railway
- Database: PostgreSQL

## Quick Start

### Prerequisites
- Node.js 16+
- Python 3.10+
- Git

### Installation

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

#### Frontend Setup
```bash
cd frontend
npm install
```

### Running Locally

**Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` in your browser.

## API Endpoints

### Search Papers
```
POST /api/v1/search
{
  "query": "machine learning",
  "sources": ["arxiv", "crossref"],
  "limit": 100,
  "sort_by": "relevance"
}
```

### Get Paper Details
```
GET /api/v1/paper/{paper_id}
```

### Summarize Paper
```
POST /api/v1/summarize
{
  "url": "https://arxiv.org/abs/..."
}
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```
ARXIV_API_KEY=your_key
CROSSREF_API_KEY=your_key
CORE_API_KEY=your_key
OPENALEX_API_KEY=your_key
```

## Project Structure

```
Research-Paper-Intelligence-Hub/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration
│   ├── requirements.txt
│   └── services/         # API clients & processing
├── frontend/
│   ├── src/
│   │   ├── App.tsx       # Main component
│   │   ├── App.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
└── README.md
```

## Usage

1. **Search**: Enter research keywords and select sources
2. **Filter**: Choose specific databases and sort preferences
3. **Review**: Read summaries and relevance scores
4. **Export**: Download citations in your preferred format
5. **Track**: Save important papers for your research

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Contact

For questions or suggestions, please open an issue on GitHub.

---

**Built for researchers publishing papers and applying to PhD programs** 🎓
