from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from config import FRONTEND_URL, CORE_API_KEY, CROSSREF_API_KEY, OPENALEX_API_KEY
from services.orchestrator import SearchOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research Paper Intelligence Hub",
    description="Search, summarize, and analyze academic papers from multiple databases",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search orchestrator
orchestrator = SearchOrchestrator(
    core_api_key=CORE_API_KEY,
    crossref_api_key=CROSSREF_API_KEY,
    openalex_email=OPENALEX_API_KEY,
)

# Pydantic models
class PaperSummary(BaseModel):
    id: str
    title: str
    authors: List[str]
    published_date: Optional[str] = None
    summary: str
    relevance_score: float
    source: str
    url: str
    citations_count: Optional[int] = 0
    abstract: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    sources: List[str] = ["arxiv", "crossref", "openalex"]
    limit: int = 100
    sort_by: str = "relevance"  # relevance, date, citations

class SearchResponse(BaseModel):
    query: str
    total_papers: int
    papers: List[PaperSummary]
    search_time: float
    timestamp: datetime

# Routes
@app.get("/")
async def root():
    return {
        "message": "Research Paper Intelligence Hub API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/v1/search",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow()}

@app.post("/api/v1/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """
    Search for papers across multiple academic databases.
    
    - **query**: Search keywords
    - **sources**: List of sources to search (arxiv, crossref, openalex, core, pubmed)
    - **limit**: Maximum papers to return (max 500)
    - **sort_by**: Sort results by relevance, date, or citations
    """
    try:
        if not request.query or len(request.query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        if request.limit > 500:
            request.limit = 500

        valid_sources = {"arxiv", "crossref", "core", "openalex", "pubmed"}
        request.sources = [s for s in request.sources if s in valid_sources]
        if not request.sources:
            request.sources = ["arxiv", "crossref", "openalex"]
        
        logger.info(f"Search query: {request.query}, sources: {request.sources}")
        
        result = await orchestrator.search(
            query=request.query,
            sources=request.sources,
            limit=request.limit,
            sort_by=request.sort_by,
        )

        papers = []
        for p in result["papers"]:
            papers.append(PaperSummary(
                id=p.get("id", ""),
                title=p.get("title", "Untitled"),
                authors=p.get("authors", []),
                published_date=p.get("published_date"),
                summary=p.get("summary", ""),
                relevance_score=p.get("relevance_score", 0.0),
                source=p.get("source", "unknown"),
                url=p.get("url", ""),
                citations_count=p.get("citations_count", 0),
                abstract=p.get("abstract"),
            ))

        return SearchResponse(
            query=request.query,
            total_papers=result["total_papers"],
            papers=papers,
            search_time=result["search_time"],
            timestamp=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/v1/paper/{paper_id}")
async def get_paper_details(paper_id: str):
    """Get detailed information about a specific paper"""
    try:
        # TODO: Implement paper details retrieval
        return {"paper_id": paper_id, "status": "details endpoint"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/summarize")
async def summarize_paper(url: str):
    """Summarize a paper from a given URL"""
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # TODO: Implement paper summarization
        return {"url": url, "summary": "Your summary will appear here"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
